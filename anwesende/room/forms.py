import datetime as dt
import os
import re
import tempfile

import crispy_forms.helper as cfh
import crispy_forms.layout as cfl
import django.core.exceptions as djce
import django.forms as djf
import django.utils.timezone as djut

import anwesende.room.logic as arl
import anwesende.room.models as arm

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
        return dt_obj


class VisitForm(djf.ModelForm):
    class Meta:
        model = arm.Visit
        fields = (
            'givenname', 'familyname', 
            'street_and_number', 'zipcode', 'town',
            'phone', 'email',
            'present_from_dt', 'present_to_dt'
        )
    
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