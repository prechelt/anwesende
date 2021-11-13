import datetime as dt
import logging
import os
import re
import tempfile
import time
import typing as tg

import crispy_forms.helper as cfh
import crispy_forms.layout as cfl
from django.conf import settings
import django.core.exceptions as djce
import django.forms as djf
import django.forms.widgets as djfw
import django.utils.timezone as djut

import anwesende.room.excel as are
import anwesende.room.models as arm
import anwesende.utils.date as aud


def mytxt(width: int) -> djfw.TextInput:
    return djfw.TextInput(attrs={'size': str(width)})


class TimeOnlyDateTimeField(djf.CharField):
    def to_python(self, value: str) -> dt.datetime:
        time_regex = r"^([01][0-9]|2[0-3]):?[0-5][0-9]$"  # with or without colon
        error_msg = "Falsches Uhrzeitformat / Wrong time-of-day format"
        if not re.match(time_regex, value or ""):
            raise djce.ValidationError(error_msg)
        if ':' not in value:
            value = value[:-2] + ':' + value[-2:]  # insert colon
        dt_string = djut.localtime().strftime(f"%Y-%m-%d {value}")
        dt_tuple = time.strptime(dt_string, "%Y-%m-%d %H:%M")[0:5]
        dt_obj = djut.make_aware(dt.datetime(*dt_tuple))
        return dt_obj


class TimeRangeField(djf.CharField):
    @staticmethod
    def _make_dt(datestr, timestr) -> dt.datetime:
        mydt = dt.datetime.strptime(f"{datestr} {timestr}", "%Y-%m-%d %H:%M")
        return djut.make_aware(mydt)

    def to_python(self, value: str) -> tg.Tuple[dt.datetime, dt.datetime]:
        date_regex = r"(\d\d\d\d-\d\d-\d\d)"
        time_regex = r"(\d\d:\d\d)"
        error_msg = "Falsches Zeitraumformat"
        try:
            regex = f"{date_regex} {time_regex}-{time_regex}"
            mm = re.match(regex, value)
            assert mm  # catch many wrong inputs early, others fail strptime
            from_dt = self._make_dt(mm.group(1), mm.group(2))
            to_dt = self._make_dt(mm.group(1), mm.group(3))
            assert from_dt < to_dt, "Anfang muss vor Ende liegen"
            return (from_dt, to_dt)
        except Exception as exc:  # whatever goes wrong: it will be due to the input string
            raise djce.ValidationError(f"{error_msg} ({str(exc)})")



class UploadFileForm(djf.Form):
    """
    This form will also read the uploaded Excel file, validate it, and 
    create the Rooms and Seats,
    because validation is not considered complete until that is successful.
    (This is a departure from normal Django application architecture.)
    """
    file = djf.FileField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = cfh.FormHelper()
        self.helper.form_id = 'UploadForm'
        self.helper.form_method = 'post'
        self.helper.add_input(cfl.Submit('submit', 'Hochladen'))
        
    def clean(self):
        logger = logging.getLogger('error')
        self.cleaned_data = super().clean()
        try:
            uploadedfile = self.cleaned_data['file']
        except KeyError:
            raise djce.ValidationError("Dateiname fehlt")
        try:
            excelfile = self._store_excelfile(uploadedfile)
        except Exception:
            msg = f"Kann die Datei {{uploadedfile}} nicht öffnen"
            logger.warning(msg)
            raise djce.ValidationError(msg)
        try:
            are.validate_excel_importfile(excelfile)  # stores models iff valid
        except are.InvalidExcelError as err:
            logger.error("InvalidExcelError({uploadedfile})", exc_info=err)
            raise djce.ValidationError(err)
        except Exception as err:
            msg = f"{uploadedfile} ist keine gültige XLSX-Datei, oder?"
            logger.error(f"UploadFileForm({uploadedfile})", exc_info=err)
            raise djce.ValidationError(msg)
        self.cleaned_data['excelfile'] = excelfile
        
    def _store_excelfile(self, uploadedfile):
        fh, filename = tempfile.mkstemp(prefix="rooms", suffix=".xlsx")
        fd = os.fdopen(fh, mode='wb')
        for chunk in uploadedfile.chunks():
            fd.write(chunk)
        fd.close()
        return filename


class VisitForm(djf.ModelForm):
    class Meta:
        model = arm.Visit
        fields = (
            'givenname', 'familyname', 
            'street_and_number', 'zipcode', 'town',
            'phone', 'email', 'status_3g',
            'present_from_dt', 'present_to_dt', 'cookie',
        )
        widgets = {
            'givenname': mytxt(25), 'familyname': mytxt(25),
            'street_and_number': mytxt(25), 
            'zipcode': mytxt(6), 'town': mytxt(20),
            'phone': mytxt(15), 'email': mytxt(25),
            'present_from_dt': mytxt(6), 'present_to_dt': mytxt(6),
            'cookie': djfw.HiddenInput()
        }

    present_from_dt = TimeOnlyDateTimeField(
        label="Anwesenheit von / Present from",
        help_text="Uhrzeit im Format hh:mm oder hhmm, z.B. 16:15 oder 1615 / time of day, e.g. 09:45 or 0945",
    )
    present_to_dt = TimeOnlyDateTimeField(
        label="Anwesenheit geplant bis / Intend to be present until",
        help_text="Uhrzeit im Format hh:mm oder hhmm, z.B. 17:45 oder 1745 / time of day, e.g. 15:15 or 1515",
    )

    def __init__(self, *args, **kwargs):
        #--- do not reuse a G_TESTET value from the cookie:
        if (settings.USE_STATUS_3G_FIELD and 
                'initial' in kwargs and
                'status_3g' in kwargs['initial'] and
                kwargs['initial']['status_3g'] == str(arm.G_TESTET)):
            kwargs['initial']['status_3g'] = None
        #--- init():
        super().__init__(*args, **kwargs)
        #--- handle conditional fields:
        if settings.USE_EMAIL_FIELD:
            self.fields['email'].required = True
        else:
            del self.fields['email']
        if settings.USE_STATUS_3G_FIELD:
            self.fields['status_3g'].choices = arm.Visit.status_3g_formchoices
        else:
            del self.fields['status_3g']
        #--- set up helper:
        self.helper = cfh.FormHelper()
        self.helper.form_id = 'VisitForm'
        self.helper.form_method = 'post'
        self.helper.add_input(cfl.Submit('submit', 'Submit'))

    def clean(self):
        self.cleaned_data = super().clean()
        cd = self.cleaned_data  # short alias
        if ('present_from_dt' in cd and 'present_to_dt' in cd 
                and cd['present_from_dt'] > cd['present_to_dt']):
            self.add_error('present_to_dt', 
                           "'von'-Zeit muss vor 'bis'-Zeit liegen / "
                           + "'from' must be before 'until'")


class SearchForm(djf.Form):
    emailwarning = ("ABGESCHALTET. Die Daten enthalten keine Emailadressen. "
                    "Sie können also per Emailadresse nichts finden!")
    organization = djf.CharField(label="Organization",
            initial="%", required=True, )
    department = djf.CharField(label="Department",
            initial="%", required=True, )
    building = djf.CharField(label="Building",
            initial="%", required=True, )
    room = djf.CharField(label="Room",
            initial="%", required=True, )
    givenname = djf.CharField(label="Vorname / Given name",
            initial="%", required=True, )
    familyname = djf.CharField(label="Nachname / Family name",
            initial="%", required=True, )
    phone = djf.CharField(label="Telefonnummer",
            initial="+49%1%", required=True, 
            help_text="Mögliche Leerzeichen durch '%' tolerierbar machen!")
    email = djf.CharField(label="Emailadresse",
            initial="%@%" if settings.USE_EMAIL_FIELD else "%", 
            required=True, 
            help_text="" if settings.USE_EMAIL_FIELD else emailwarning)
    from_date = djf.DateField(label="von Datum (jjjj-mm-tt)",
            initial="", required=True, )
    to_date = djf.DateField(label="bis Datum (jjjj-mm-tt)",
            initial=aud.nowstring(time=False), required=True, )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = cfh.FormHelper()
        self.helper.form_id = 'SearchForm'
        self.helper.form_method = 'post'
        self.helper.add_input(cfl.Submit('visit', 
                                         '1. Besuche finden'))
        self.helper.add_input(cfl.Submit('visitgroup', 
                                         '2. Kontaktgruppen finden'))
        self.helper.add_input(cfl.Submit('xlsx', 
                                         '3. Kontaktgruppen-Excel herunterladen'))

    def clean(self):
        self.cleaned_data = super().clean()
        cd = self.cleaned_data  # short alias
        if ('from_date' in cd and 'to_date' in cd 
                and cd['from_date'] > cd['to_date']):
            self.add_error('to_date', 
                           "'von Datum' muss vor oder auf 'bis Datum' liegen")
        if 'to_date' in cd:
            cd['to_date'] += dt.timedelta(hours=24)  # is time 0:00, should be 24:00
        return cd
