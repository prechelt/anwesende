import json
import typing as tg

import django.http as djh
import django.urls as dju
import vanilla as vv  # Django vanilla views
from django.conf import settings

import anwesende.room.models as arm
import anwesende.room.forms as arf
import anwesende.utils.qrcode as auq

COOKIENAME = 'anwesende'


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


class VisitView(vv.CreateView):
    model = arm.Visit
    form_class = arf.VisitForm
    template_name = "room/visit.html"
    success_url = dju.reverse_lazy('room:thankyou')
    
    def get_form(self, data=None, files=None, **kwargs):
        #return super().get_form(data, files, **kwargs)
        if data:
            data = {k:v for k,v, in data.items()}  # extract ordinary dict
            print("########data", data)
        if not data and COOKIENAME in self.request.COOKIES:
            data = json.loads(self.request.COOKIES[COOKIENAME])
            print("########cookie", data)
        form = arf.VisitForm(data=data, files=files, **kwargs)
        return form
        
    def form_valid(self, form: arf.VisitForm):
        response = djh.HttpResponseRedirect(self.get_success_url())
        cookiedict = {k:v for k,v, in form.data.items()}  # extract ordinary dict
        del cookiedict['csrfmiddlewaretoken']
        del cookiedict['submit']
        cookiejson = json.dumps(cookiedict)
        print("########", cookiejson)
        response.set_cookie(key=COOKIENAME, value=cookiejson, 
                            max_age=3600*24*90)
        # self.object = form.save()
        return response


class ThankyouView(vv.TemplateView):
    template_name = "room/thankyou.html"


class UncookieView(vv.GenericView):
    def get(self, request, *args, **kwargs):
        response = djh.HttpResponse("Cookie expired")
        response.set_cookie(COOKIENAME, None, max_age=0)  # expire now
        return response