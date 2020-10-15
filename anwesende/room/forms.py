import datetime as dt
import os
import re
import tempfile

import crispy_forms.helper as cfh
import crispy_forms.layout as cfl
import django.core.exceptions as djce
import django.forms as djf
import django.forms.widgets as djfw
import django.utils.timezone as djut

import anwesende.room.logic as arl
import anwesende.room.models as arm
import anwesende.utils.date as aud


def mytxt(width: int) -> djfw.TextInput:
    return djfw.TextInput(attrs={'size': str(width)})


class UploadFileForm(djf.Form):
    file = djf.FileField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = cfh.FormHelper()
        self.helper.form_id = 'UploadForm'
        self.helper.form_method = 'post'
        self.helper.add_input(cfl.Submit('submit', 'Submit'))
        
    def clean(self):
        self.cleaned_data = super().clean()
        uploadedfile = self.cleaned_data['file']
        excelfile = self._store_excelfile(uploadedfile)
        try:
            arl.create_seats_from_excel(excelfile)  # stores models iff valid
        except arl.InvalidExcelError as err:
            raise djce.ValidationError(err.value)
        
    def _store_excelfile(self, uploadedfile):
        fh, filename = tempfile.mkstemp(prefix="rooms", suffix=".xlsx")
        fd = os.fdopen(fh, mode='wb')
        for chunk in uploadedfile.chunks():
            fd.write(chunk)
        fd.close()
        return filename


class TimeOnlyDateTimeField(djf.CharField):
    def to_python(self, value: str) -> dt.datetime:
        time_regex = r"^([01][0-9]|2[0-3]):[0-5][0-9]$"
        error_msg = "Falsches Uhrzeitformat / Wrong time-of-day format"
        if not re.match(time_regex, value):
            raise djce.ValidationError(error_msg)
        dt_string = djut.now().strftime(f"%Y-%m-%d {value}")
        dt_obj = dt.datetime.strptime(dt_string, "%Y-%m-%d %H:%M")
        dt_obj.tzinfo = djut.get_current_timezone()
        return dt_obj


class VisitForm(djf.ModelForm):
    class Meta:
        model = arm.Visit
        fields = (
            'givenname', 'familyname', 
            'street_and_number', 'zipcode', 'town',
            'phone', 'email',
            'present_from_dt', 'present_to_dt',
        )
        widgets = {
            'givenname':mytxt(25), 'familyname':mytxt(25),
            'street_and_number':mytxt(25), 
            'zipcode':mytxt(6), 'town':mytxt(20),
            'phone':mytxt(15), 'email':mytxt(25),
            'present_from_dt':mytxt(6), 'present_to_dt':mytxt(6),
        }
    
    present_from_dt = TimeOnlyDateTimeField(
        label = "Anwesenheit von / Present from",
        help_text = "Uhrzeit im Format hh:mm, z.B. 16:15 / time of day, e.g. 14:45",
    )
    present_to_dt = TimeOnlyDateTimeField(
        label = "Anwesenheit geplant bis / Intend to be present until",
        help_text = "Uhrzeit im Format hh:mm, z.B. 17:45 / time of day, e.g. 15:15",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data['present_from_dt'] = aud.nowstring(date=False, time=True)
        self.helper = cfh.FormHelper()
        self.helper.form_id = 'VisitForm'
        self.helper.form_method = 'post'
        self.helper.add_input(cfl.Submit('submit', 'Submit'))

    def clean(self):
        self.cleaned_data = super().clean()
        cd = self.cleaned_data  # short alias
        if ('present_from_dt' in cd and 'present_to_dt' in cd and
                cd['present_from_dt'] > cd['present_to_dt']):
            self.add_error('present_to_dt', 
                           "'von'-Zeit muss vor 'bis'-Zeit liegen / " +
                               "'from' must be before 'until'")


class SearchForm(djf.Form):
    organization = djf.CharField(label="Organization",
            initial="%", required=True, )
    department = djf.CharField(label="Department",
            initial="%", required=True, )
    building = djf.CharField(label="Building",
            initial="%", required=True, )
    room = djf.CharField(label="Room",
            initial="%", required=True, )
    givenname = djf.CharField(label="Given name",
            initial="%", required=True, )
    familyname = djf.CharField(label="Family name (try % for uncertain letters)",
            initial="%", required=True, )
    phone = djf.CharField(label="Phone number (no blank, slash, dash!)",
            initial="+491%", required=True, )
    email = djf.CharField(label="Email address",
            initial="%@%", required=True, )
    from_date = djf.DateField(label="From date (yyyy-mm-dd)",
            initial="", required=True, )
    to_date = djf.DateField(label="To date (yyyy-mm-dd)",
            initial=aud.nowstring(time=False), required=True, )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = cfh.FormHelper()
        self.helper.form_id = 'SearchForm'
        self.helper.form_method = 'post'
        self.helper.add_input(cfl.Submit('visit', 
                                         '1. Find visits'))
        self.helper.add_input(cfl.Submit('visitgroup', 
                                         '2. Find contact groups'))
        self.helper.add_input(cfl.Submit('xlsx', 
                                         '3. Download contact groups Excel'))

    def clean(self):
        self.cleaned_data = super().clean()
        cd = self.cleaned_data  # short alias
        if ('from_date' in cd and 'to_date' in cd and
                cd['from_date'] > cd['to_date']):
            self.add_error('to_date', 
                           "'from' date must not be later than 'to' date")
        cd['to_date'] += dt.timedelta(hours=24)  # is time 0:00, should be 24:00
        return cd
