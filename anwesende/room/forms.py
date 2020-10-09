import os
import tempfile

import crispy_forms.helper as cfh
import crispy_forms.layout as cfl
import django.core.exceptions as djce
import django.forms as djf

import anwesende.room.logic as arl

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
