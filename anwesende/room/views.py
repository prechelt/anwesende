import datetime as dt
import time
import typing as tg

import django.db.models as djdm
import django.forms as djf
import django.http
import django.http as djh
import django.utils.text as djutx
import django.utils.timezone as djut
import vanilla as vv  # Django vanilla views
from django.conf import settings

import anwesende.room.models as arm
import anwesende.room.forms as arf

class ImportView(vv.FormView):
    form_class = arf.UploadFileForm
    template_name = "room/import.html"

    def get_success_url(self):
        return "QRcode-page-url"


class QRcodesView(vv.DetailView):
    model = arm.Importstep
    template_name = "room/import.html"

    def get_context_data(self):
        context = super().get_context_data()
        context['must_do'] = 4711
        return context

    def get_object(self):
        self.object = super().get_object()
        assert self.kwargs['randomkey'] == self.object.randomkey  # else HTTP 500