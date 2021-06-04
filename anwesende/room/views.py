import datetime as dt
import json
import logging
import os
import typing as tg

import django.http as djh
import django.urls as dju
import django.utils.timezone as djut
import vanilla as vv  # Django vanilla views
from django.conf import settings

import anwesende.room.excel as are
import anwesende.room.forms as arf
import anwesende.room.models as arm
import anwesende.utils.date as aud
import anwesende.utils.lookup as aul  # noqa,  registers lookup
import anwesende.utils.qrcode as auq

COOKIENAME = 'anwesende'


class IsDatenverwalterMixin:
    """
    Sets user and is_datenverwalter flag in self and in context.
    """
    def dispatch(self, request: djh.HttpRequest, *args, **kwargs) -> djh.HttpResponse:
        self.user = self.request.user  # type: ignore
        self.is_datenverwalter = self.user.is_authenticated \
            and self.user.is_datenverwalter()
        return super().dispatch(request, *args, **kwargs)  # type: ignore

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # type: ignore
        context['user'] = self.user
        context['is_datenverwalter'] = self.is_datenverwalter
        return context


class SettingsMixin:
    """base.html requires 'settings' in context"""
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # type: ignore
        context['settings'] = settings
        return context


class FAQView(SettingsMixin, vv.TemplateView):
    template_name = "room/faq.html"


class HomeView(SettingsMixin, vv.TemplateView):
    template_name = "room/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dummyseat'] = arm.Seat.get_dummy_seat()
        return context


class ImportView(IsDatenverwalterMixin, SettingsMixin, vv.FormView):
    form_class = arf.UploadFileForm
    template_name = "room/import.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.is_datenverwalter:
            interval = dt.timedelta(days=8)
            imports = arm.Importstep.displayable_importsteps(interval)
        else:
            room = arm.Seat.get_dummy_seat().room
            importstep = room.importstep
            importstep.organization = room.organization  # type: ignore[attr-defined]
            importstep.department = room.department  # type: ignore[attr-defined]
            imports = [importstep]
        context['imports'] = imports
        context['settings'] = settings
        return context

    def form_invalid(self, form: arf.UploadFileForm):
        logging.warning(f"ImportView invalid: {form.errors}")
        return super().form_invalid(form)

    def form_valid(self, form: arf.UploadFileForm):
        filename = form.cleaned_data['excelfile']  # form has created the file
        self.importstep = are.create_seats_from_excel(filename, self.user)
        os.remove(filename)
        logging.info(f"ImportView({self.importstep})")
        return super().form_valid(form)

    def get_success_url(self):
        return dju.reverse('room:qrcodes', kwargs=dict(pk=self.importstep.pk))


class QRoverView(IsDatenverwalterMixin, SettingsMixin, vv.TemplateView):
    template_name = "room/qroverview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.is_datenverwalter:
            context['rooms'] = arm.Room.get_rooms()
        else:
            context['rooms'] = []
        return context


class QRcodesView(IsDatenverwalterMixin, SettingsMixin, vv.DetailView):
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


class QRcodesDepView(IsDatenverwalterMixin, SettingsMixin, vv.DetailView):
    model = arm.Room
    template_name = "room/qrcodesdep.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        seats = arm.Seat.objects.filter(room__department=self.object.department)
        context['seats'] = seats
        return context

    def get_object(self):
        object = super().get_object()
        if self.is_datenverwalter or object == arm.Seat.get_dummy_seat().room.department:
            return object
        else:
            raise djh.Http404


class QRcodeView(IsDatenverwalterMixin, SettingsMixin, vv.View):
    def get(self, request, *args, **kwargs):
        if not self.is_datenverwalter \
                and kwargs['hash'] != arm.Seat.get_dummy_seat().hash:
            raise djh.Http404
        path = dju.reverse('room:visit', kwargs=dict(hash=kwargs['hash']))
        url = settings.SHORTURL_PREFIX + path
        qrcode_bytes = auq.qrcode_data(url, imgtype='svg')
        return djh.HttpResponse(qrcode_bytes, content_type="image/svg+xml")


class VisitView(SettingsMixin, vv.CreateView):
    model = arm.Visit
    form_class = arf.VisitForm
    template_name = "room/visit.html"

    def get_success_url(self):
        room = self.object.seat.room
        visitors_presentN = arm.Visit.current_unique_visitorsN(room)
        return dju.reverse('room:thankyou',
                           kwargs=dict(visitors_presentN=visitors_presentN))

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
        if data:  # POST
            data = {k: v for k, v in data.items()}  # extract ordinary dict
            return arf.VisitForm(data=data, files=files, **kwargs)
        # else GET:
        if COOKIENAME in self.request.COOKIES:
            initial = json.loads(self.request.COOKIES[COOKIENAME])
        else:
            initial = dict(cookie=arm.Visit.make_cookie())
            logging.info(f"VisitView: new {initial}")
        initial['present_from_dt'] = aud.nowstring(date=False, time=True)
        return arf.VisitForm(initial=initial)

    def form_valid(self, form: arf.VisitForm):
        self.object = form.save(commit=False)
        self.object.seat = arm.Seat.by_hash(self.kwargs['hash'])
        self.object.save()
        o = self.object
        logging.info(f"VisitView({o.seat.hash}): {o.givenname}; {o.email}; {o.zipcode}; {o.cookie}")
        response = djh.HttpResponseRedirect(self.get_success_url())
        response.set_cookie(key=COOKIENAME, value=self.get_cookiejson(form),
                            max_age=3600 * 24 * 90)
        return response

    def get_cookiejson(self, form):
        cookiedict = {k: v for k, v, in
                      form.data.items()}  # extract ordinary dict
        del cookiedict['csrfmiddlewaretoken']
        del cookiedict['present_from_dt']
        del cookiedict['present_to_dt']
        if 'submit' in cookiedict:
            del cookiedict['submit']
        cookiejson = json.dumps(cookiedict)
        return cookiejson


class ThankyouView(SettingsMixin, vv.TemplateView):
    template_name = "room/thankyou.html"


class UsageStatisticsView(IsDatenverwalterMixin, SettingsMixin, vv.TemplateView):
    template_name = "room/stats.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.is_datenverwalter:
            context['stats'] = arm.Room.usage_statistics()
        else:
            context['stats'] = []
        return context


class UncookieView(vv.GenericView):
    def get(self, request, *args, **kwargs):
        response = djh.HttpResponse("Cookie expired")
        response.set_cookie(COOKIENAME, "", max_age=0)  # expire now
        return response


class SearchView(IsDatenverwalterMixin, SettingsMixin, vv.ListView):  # same view for valid and invalid form
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
        def fdt(d: dt.datetime):
            return djut.make_aware(dt.datetime(d.year, d.month, d.day, d.hour, d.minute))
        f = self.form.cleaned_data
        secure_organization = f['organization'] if self.is_datenverwalter \
            else settings.DUMMY_ORG
        if not settings.USE_EMAIL_FIELD:
            f['email'] = '%'  # insert dummy so we can use the full search
        return (arm.Visit.objects
                .filter(seat__room__organization__ilike=secure_organization)
                .filter(seat__room__department__like=f['department'])
                .filter(seat__room__building__like=f['building'])
                .filter(seat__room__room__like=f['room'])
                .filter(givenname__ilike=f['givenname'])
                .filter(familyname__ilike=f['familyname'])
                .filter(phone__like=f['phone'])
                .filter(email__like=f['email'])
                .filter(present_to_dt__gt=fdt(f['from_date']))  # left after from
                .filter(present_from_dt__lt=fdt(f['to_date']))  # came before to
                )

    def get(self, request, *args, **kwargs):
        def make_secure():
            if not self.is_datenverwalter:
                self.form.fields['organization'].initial = settings.DUMMY_ORG
                self.form.fields['organization'].widget.attrs['readonly'] = True

        self.form = self.get_form()
        make_secure()
        context = self.get_context_data(is_post=False)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        # will be secure wrt not is_datenverwalter due to safe get_queryset()
        self.form = self.get_form(data=request.POST)
        context = self.get_context_data(is_post=True)
        self._log_post(context)
        self.log_search(context)
        if context['display_switch'] == 'xlsx':
            return self.excel_download_response(context['visits'])
        else:
            return self.render_to_response(context)

    def _log_post(self, context):
        logcontext = context.copy()
        if 'visits' in logcontext:
            del logcontext['visits']
        if 'environ' in logcontext:
            del logcontext['environ']
        if 'form' in logcontext:
            logcontext['form'] = logcontext['form'].data
        logging.info(f"SearchView({logcontext}")

    def log_search(self, context):
        user = context['user']
        search_type = context['display_switch']
        search_protocol = arm.SearchProtocol(
            user=user, search_type=search_type)
        search_protocol.save()

    def excel_download_response(self, visits: tg.List[tg.Optional[arm.Visit]]) -> djh.HttpResponse:
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
