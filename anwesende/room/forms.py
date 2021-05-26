import datetime as dt
import os
import re
import tempfile
import time

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
        self.cleaned_data = super().clean()
        try:
            uploadedfile = self.cleaned_data['file']
        except KeyError:
            raise djce.ValidationError("Dateiname fehlt")
        try:
            excelfile = self._store_excelfile(uploadedfile)
        except Exception:
            raise djce.ValidationError(f"Kann die Datei {{uploadedfile}} nicht öffnen")
        try:
            are.validate_excel_importfile(excelfile)  # stores models iff valid
        except are.InvalidExcelError as err:
            raise djce.ValidationError(err)
        except Exception:
            raise djce.ValidationError("Das ist keine gültige XLSX-Datei, oder?")
        self.cleaned_data['excelfile'] = excelfile

    def _store_excelfile(self, uploadedfile):
        fh, filename = tempfile.mkstemp(prefix="rooms", suffix=".xlsx")
        fd = os.fdopen(fh, mode='wb')
        for chunk in uploadedfile.chunks():
            fd.write(chunk)
        fd.close()
        return filename


class TimeOnlyDateTimeField(djf.CharField):
    def to_python(self, value) -> dt.datetime:
        time_regex = r"^([01][0-9]|2[0-3]):[0-5][0-9]$"
        error_msg = "Falsches Uhrzeitformat / Wrong time-of-day format"
        if not re.match(time_regex, value or ""):
            raise djce.ValidationError(error_msg)
        dt_string = djut.localtime().strftime(f"%Y-%m-%d {value}")
        dt_tuple = time.strptime(dt_string, "%Y-%m-%d %H:%M")[0:5]
        dt_obj = djut.make_aware(dt.datetime(*dt_tuple))
        return dt_obj


class VisitForm(djf.ModelForm):
    class Meta:
        model = arm.Visit
        fields = (
            'givenname', 'familyname',
            'street_and_number', 'zipcode', 'town',
            'phone', 'email',
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
        help_text="Uhrzeit im Format hh:mm, z.B. 16:15 / time of day, e.g. 14:45",
    )
    present_to_dt = TimeOnlyDateTimeField(
        label="Anwesenheit geplant bis / Intend to be present until",
        help_text="Uhrzeit im Format hh:mm, z.B. 17:45 / time of day, e.g. 15:15",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if settings.USE_EMAIL_FIELD:
            self.fields['email'].required = True
        else:
            del self.fields['email']
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
    from_date = djf.SplitDateTimeField(label="von Datum (jjjj-mm-tt) und Uhrzeit (hh:mm)",
                                       widget=djf.SplitDateTimeWidget(
                                           date_attrs={'value': aud.nowstring(time=False),
                                                       'class': 'form-control',
                                                       'placeholder': 'jjjj-mm-tt'},
                                           time_attrs={'value': "08:00",
                                                       'class': 'form-control',
                                                       'placeholder': 'hh:mm'}),
                                       help_text='Bitte das Eingabeformat beachten',
                                       required=True)
    from_date_hidden = djf.CharField(widget=djf.TextInput(attrs={'style': 'display: none'}),
                                     label="",
                                     initial=True,
                                     disabled=True,
                                     required=True)
    to_date = djf.SplitDateTimeField(label="bis Datum (jjjj-mm-tt) und Uhrzeit (hh:mm)",
                                     widget=djf.SplitDateTimeWidget(
                                         date_attrs={'value': aud.nowstring(time=False),
                                                     'class': 'form-control',
                                                     'placeholder': 'jjjj-mm-tt'},
                                         time_attrs={'value': "19:00",
                                                     'class': 'form-control',
                                                     'placeholder': 'hh:mm'}),
                                     help_text='Bitte das Eingabeformat beachten',
                                     required=True)
    to_date_hidden = djf.CharField(widget=djf.TextInput(attrs={'style': 'display: none'}),
                                   label="",
                                   initial=True,
                                   disabled=True,
                                   required=True)

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
            self.add_error('to_date_hidden',
                           "'von Datum und Uhrzeit' muss vor 'bis Datum und Uhrzeit' liegen")
        if not ('from_date' in cd):
            self.add_error('from_date_hidden',
                           "Bitte das richtige Format verwenden")
        if not ('to_date' in cd):
            self.add_error('to_date_hidden',
                           "Bitte das richtige Format verwenden")
        return cd
