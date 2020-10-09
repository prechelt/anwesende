import datetime as dt
import time
import typing as tg

import django.http as djh
import django.urls as dju
import vanilla as vv  # Django vanilla views
from django.conf import settings

import anwesende.room.models as arm
import anwesende.room.forms as arf
import anwesende.utils.qrcode as auq


class ImportView(vv.FormView):
    form_class = arf.UploadFileForm
    template_name = "room/import.html"

    def get_success_url(self):
        return dju.reverse('room.qrcodes', kwargs=dict(pk=1, randomkey=819737))


class QRcodesView(vv.DetailView):
    model = arm.Importstep
    template_name = "room/qrcodes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        seats = arm.Seat.objects.filter(room__importstep=self.object)
        context['seats'] = seats
        return context

    def get_object(self):
        object = super().get_object()
        # assert self.kwargs['randomkey'] == object.randomkey  # else HTTP 500
        return object
    
    
class QRcodeView(vv.View):
    def get(self, request, *args, **kwargs):
        path = dju.reverse('room:visit', kwargs=dict(hash=kwargs['hash']))
        url = self.request.build_absolute_uri(path)
        qrcode_bytes = auq.qrcode_data(url, imgtype='svg')
        return djh.HttpResponse(qrcode_bytes, content_type="image/svg+xml")


class VisitView(vv.TemplateView):
    #model = arm.Visit
    template_name = "room/visit.html"
    ...
