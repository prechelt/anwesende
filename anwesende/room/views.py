import datetime as dt
import json
import os

import django.contrib.auth.models as djcam
import django.http as djh
import django.urls as dju
import django.utils.timezone as djut
import vanilla as vv  # Django vanilla views
from django.conf import settings
from django.db.models import Max

import anwesende.room.forms as arf
import anwesende.room.excel as are
import anwesende.room.models as arm
import anwesende.utils.date as aud
import anwesende.utils.lookup as aul  # noqa,  registers lookup
import anwesende.utils.qrcode as auq

COOKIENAME = 'anwesende'


class IsDatenverwalterMixin:
    """
    Sets self.is_datenverwalter flag.
    For POST, ensures user is logged in and is member of arm.STAFF_GROUP.
    """
    datenverwalter_group = None  # cache attribute

    def dispatch(self, request: djh.HttpRequest, *args, **kwargs) -> djh.HttpResponse:
        self._init_datenverwalter_group()
        self.is_datenverwalter = request.user.is_authenticated \
            and request.user.groups.filter(pk=self.datenverwalter_group.pk).exists()
        if request.method == 'POST' and not self.is_datenverwalter:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def _init_datenverwalter_group(self):
        if not self.datenverwalter_group:
            self.datenverwalter_group = djcam.Group.objects.get_by_natural_key(
                arm.STAFF_GROUP)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_datenverwalter'] = self.is_datenverwalter
        return context


class HomeView(vv.TemplateView):
    template_name = "room/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dummyseat'] = arm.Seat.get_dummy_seat()
        return context


class ImportView(IsDatenverwalterMixin, vv.FormView):
    form_class = arf.UploadFileForm
    template_name = "room/import.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.is_datenverwalter:
            interval = dt.timedelta(hours=12)
            imports = arm.Importstep.objects.filter(
                when__gt=djut.now() - interval) \
                .annotate(organization=Max('room__organization')) \
                .annotate(department=Max('room__department'))
            show_imports = imports.count() > 0
        else:
            room = arm.Seat.get_dummy_seat().room
            importstep = room.importstep
            importstep.organization = room.organization 
            importstep.department = room.department 
            imports = [importstep]
            show_imports = True
        context['imports'] = imports
        context['show_imports'] = show_imports
        context['settings'] = settings
        return context

    def form_valid(self, form: arf.UploadFileForm):
        filename = form.cleaned_data['excelfile']
        self.result = are.create_seats_from_excel(filename, self.request.user)

    def get_success_url(self):
        pk = self.result['importstep'].pk
        return dju.reverse('room:qrcodes', kwargs=dict(pk=pk))


class QRcodesView(IsDatenverwalterMixin, vv.DetailView):
    model = arm.Importstep
    template_name = "room/qrcodes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        seats = arm.Seat.objects.filter(room__importstep=self.object)
        context['seats'] = seats
        return context

    def get_object(self):
        object = super().get_object()
        if self.is_datenverwalter or object == arm.Seat.get_dummy_seat().room.importstep:
            return object
        else:
            raise djh.Http404


class QRcodeView(IsDatenverwalterMixin, vv.View):
    def get(self, request, *args, **kwargs):
        if not self.is_datenverwalter \
                and kwargs['hash'] != arm.Seat.get_dummy_seat().hash:
            raise djh.Http404
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
        hashvalue = self.kwargs['hash']
        if self._no_such_seat(hashvalue):
            raise djh.Http404()
        seat = arm.Seat.by_hash(hashvalue)
        ctx['seat'] = seat
        ctx['room'] = seat.room
        ctx['settings'] = settings
        return ctx

    def _no_such_seat(self, hashvalue):
        return arm.Seat.objects.filter(hash=hashvalue).count() == 0
    
    def get_form(self, data=None, files=None, **kwargs):
        if data:
            data = {k: v for k, v in data.items()}  # extract ordinary dict
        elif COOKIENAME in self.request.COOKIES:
            data = json.loads(self.request.COOKIES[COOKIENAME])
        else:
            data = dict(cookie=arm.Visit.make_cookie())
        form = arf.VisitForm(data=data, files=files, **kwargs)
        return form
        
    def form_valid(self, form: arf.VisitForm):
        response = djh.HttpResponseRedirect(self.get_success_url())
        response.set_cookie(key=COOKIENAME, value=self.get_cookiejson(form), 
                            max_age=3600 * 24 * 90)
        self.object = form.save(commit=False)
        self.object.seat = arm.Seat.by_hash(self.kwargs['hash'])
        self.object.save()
        return response

    def get_cookiejson(self, form):
        cookiedict = {k: v for k, v, in
                      form.data.items()}  # extract ordinary dict
        del cookiedict['csrfmiddlewaretoken']
        del cookiedict['submit']
        del cookiedict['present_from_dt']
        del cookiedict['present_to_dt']
        cookiejson = json.dumps(cookiedict)
        return cookiejson


class ThankyouView(vv.TemplateView):
    template_name = "room/thankyou.html"


class UncookieView(vv.GenericView):
    def get(self, request, *args, **kwargs):
        response = djh.HttpResponse("Cookie expired")
        response.set_cookie(COOKIENAME, "", max_age=0)  # expire now
        return response


class SearchView(IsDatenverwalterMixin, vv.ListView):  # same view for valid and invalid form
    form_class = arf.SearchForm
    template_name = "room/search.html"

    def get_context_data(self, **ctx):
        def _key(postdata_key):  # key or None
            return postdata_key if postdata_key in self.form.data else None
    
        ctx = super().get_context_data(
            environ=os.environ,
            form=self.form,
            **ctx)
        valid = ctx['valid'] = ctx['is_post'] and self.form.is_valid()
        # print(self.form.data)
        # if valid: 
        #     print(self.form.cleaned_data)
        mode = _key('visit') or _key('visitgroup') or _key('xlsx')
        ctx['display_switch'] = mode
        if not valid:
            ctx['display_switch'] = 'invalid'
            return ctx
        elif mode == 'visit':
            ctx['visits'] = self.get_queryset()
            ctx['LIMIT'] = 100
            ctx['NUMRESULTS'] = ctx['visits'].count()
            if ctx['NUMRESULTS'] > ctx['LIMIT']:
                ctx['display_switch'] = 'too_many_results'
        elif mode == 'visitgroup' or mode == 'xlsx':
            ctx['visits'] = are.collect_visitgroups(self.get_queryset())
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
        if context['display_switch'] == 'xlsx':
            return self.excel_download_response(context['visits'])
        else:
            return self.render_to_response(context)

    def excel_download_response(self, visits):
        # https://stackoverflow.com/questions/4212861
        excel_contenttype_excel = \
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        excelbytes = are.get_excel_download(visits)
        response = djh.HttpResponse(excelbytes,
                                    content_type=excel_contenttype_excel)
        timestamp = aud.nowstring(date=True, time=True)
        # make name nice for Linux (no blanks) and for Windows (no colons):
        timestamp = timestamp.replace(' ', '_').replace(':', ".")
        filename = f"anwesende-{timestamp}.xlsx"
        response['Content-Disposition'] = (
            'attachment; filename="%s"' % (filename,))
        return response
