import json
import os
import typing as tg

import django.http as djh
import django.urls as dju
import vanilla as vv  # Django vanilla views
from django.conf import settings

import anwesende.room.models as arm
import anwesende.room.forms as arf
import anwesende.room.logic as arl
import anwesende.utils.lookup as aul  # registers lookup
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
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self._no_such_seat(self.kwargs['hash']):
            raise djh.Http404()
        return ctx

    def _no_such_seat(self, hash):
        return arm.Seat.objects.filter(hash=hash).count() == 0
    
    def get_form(self, data=None, files=None, **kwargs):
        if data:
            data = {k:v for k,v, in data.items()}  # extract ordinary dict
        if not data and COOKIENAME in self.request.COOKIES:
            data = json.loads(self.request.COOKIES[COOKIENAME])
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
        self.object = form.save(commit=False)
        self.object.seat = arm.Seat.by_hash(self.kwargs['hash'])
        self.object.save()
        return response


class ThankyouView(vv.TemplateView):
    template_name = "room/thankyou.html"


class UncookieView(vv.GenericView):
    def get(self, request, *args, **kwargs):
        response = djh.HttpResponse("Cookie expired")
        response.set_cookie(COOKIENAME, None, max_age=0)  # expire now
        return response
    

class SearchView(vv.ListView):  # same view for valid and invalid form
    form_class = arf.SearchForm
    template_name="room/search.html"

    def get_context_data(self, **ctx):
        def _key(postdata_key):  # key or None
            return self.form.data.get(postdata_key, None)  
        
        ctx = super().get_context_data(
            environ=os.environ,
            form=self.form,
            **ctx)
        valid = ctx['valid'] = ctx['is_post'] and self.form.is_valid()
        print(self.form.data)
        print(self.form.cleaned_data)
        mode = _key('visit') or _key('visitgroup') or _key('xlsx')
        ctx['display switch'] = mode
        if not valid:
            ctx['display switch'] = 'invalid'
            return ctx
        elif mode == 'visit':
            ctx['queryset'] = self.get_queryset()
            ctx['LIMIT'] = 100
            ctx['NUMRESULTS'] = ctx['queryset'].count()
            if ctx['NUMRESULTS'] > ctx['LIMIT']:
                ctx['display_switch'] = 'too_many_results'
        elif mode == 'visitgroup' or mode == 'xlsx':
            ctx['visits'] = arl.collect_visitgroups(self.get_queryset())
            ctx['LIMIT'] = 1000
            ctx['NUMRESULTS'] = len(ctx['visits'])
            if ctx['NUMRESULTS'] > ctx['LIMIT']:
                ctx['display_switch'] = 'too_many_results'
        else:
            assert False, f"SearchView: unexpected mode '{mode}'"
        return ctx

    def get_queryset(self):
        f = self.form.cleaned_data
        return (arm.Visit.objects
                .filter(seat__room__organization__like=f['organization'])
                .filter(seat__room__department__like=f['department'])
                .filter(seat__room__building__like=f['building'])
                .filter(seat__room__room__like=f['room'])
                .filter(givenname__like=f['givenname'])
                .filter(familyname__like=f['familyname'])
                .filter(phone__like=f['phone'])
                .filter(email__like=f['email'])
                .filter(present_to_dt__gt=f['from_date'])  # left after from
                .filter(present_from_dt__lt=f['to_date'])  # came before to
                )

    def get(self, request, *args, **kwargs):
        self.form = self.get_form()
        context = self.get_context_data(is_post=False)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.form = self.get_form(data=request.POST)
        context = self.get_context_data(is_post=True)
        return self.render_to_response(context)


class DownloadView(vv.ListView):
    pass