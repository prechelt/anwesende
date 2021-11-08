import datetime as dt
import json
import logging
import os
import traceback
import typing as tg

import django.contrib.auth.mixins as djcam
import django.contrib.auth.views as djcav
import django.contrib.messages as djcm
from django.db.models import Count
import django.http as djh
import django.urls as dju
import django.utils.timezone as djut
import django.views.generic.base as djvgb
import vanilla as vv  # Django vanilla views
from django.conf import settings

import anwesende.room.excel as are
import anwesende.room.forms as arf
import anwesende.room.models as arm
import anwesende.room.utils as aru
import anwesende.utils.date as aud
import anwesende.utils.lookup as aul  # noqa,  registers lookup
import anwesende.utils.qrcode as auq

COOKIENAME = 'anwesende'


class AddIsDatenverwalter:
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


class AddSettings:
    """Put 'settings' in context: base.html requires it."""
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # type: ignore
        context['settings'] = settings
        return context


class FAQView(AddSettings, vv.TemplateView):
    template_name = "room/faq.html"


class HomeView(AddSettings, vv.TemplateView):
    template_name = "room/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dummyseat'] = arm.Seat.get_dummy_seat()
        return context


class ImportView(AddIsDatenverwalter, AddSettings, vv.FormView):
    """Import-Excel-for-QR-code-creation dialog."""
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
        logging.getLogger('error').error(f"ImportView invalid: {form.errors}")
        return super().form_invalid(form)

    def form_valid(self, form: arf.UploadFileForm):
        filename = form.cleaned_data['excelfile']  # form has created the file
        self.importstep = are.create_seats_from_excel(filename, self.user)
        os.remove(filename)
        logging.info(f"ImportView({self.importstep})")
        return super().form_valid(form)

    def get_success_url(self):
        return dju.reverse('room:qrcodes-byimport', kwargs=dict(pk=self.importstep.pk))

    def post(self, request, *args, **kwargs):
        if not self.is_datenverwalter:
            next = self.request.get_full_path()
            login_url = dju.reverse('account_login')
            return djcav.redirect_to_login(next, login_url, 'next')
        return super().post(request, *args, **kwargs)

class QRcodesByImportView(AddIsDatenverwalter, AddSettings, vv.DetailView):
    """Show printable QR codes created in one Importstep."""
    model = arm.Importstep
    template_name = "room/qrcodes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        seats = arm.Seat.objects.filter(room__importstep=self.object)
        context['seats'] = seats
        context['listtype'] = 'importstep'
        return context

    def get_object(self):
        object = super().get_object()
        if self.is_datenverwalter or object == arm.Seat.get_dummy_seat().room.importstep:
            return object
        else:
            raise djh.Http404


class QRcodesByRoomsView(djcam.LoginRequiredMixin, 
                         AddIsDatenverwalter, AddSettings, vv.TemplateView):
    """Show printable QR codes for one room or one building."""
    template_name = "room/qrcodes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['seats'] = self.get_queryset().all()
        context['listtype'] = 'byrooms'
        return context

    def get(self, request, *args, **kwargs):
        pop_org_dept_bldg_room(self)
        return super().get(request, *args, **kwargs)
        
    def get_queryset(self):
        qs = arm.Seat.objects.filter(
                room__organization=self.organization,
                room__department=self.department,
                room__building=self.building)
        if self.room:
            return qs.filter(room__room=self.room)
        else:
            return qs

def pop_org_dept_bldg_room(view):
    """
    Get certain URL params (if present) which come in slash-escaped in original form.
    See aru.escape_slash for rationale.
    """
    for arg in ('organization', 'department', 'building', 'room'):
        val = view.kwargs.pop(arg, "")
        setattr(view, f"{arg}", aru.unescape_slash(val))  # the real value


class QRcodeView(AddIsDatenverwalter, AddSettings, vv.View):
    """Render one QR code as SVG."""
    def get(self, request, *args, **kwargs):
        if not self.is_datenverwalter \
                and kwargs['hash'] != arm.Seat.get_dummy_seat().hash:
            raise djh.Http404
        path = dju.reverse('room:visit', kwargs=dict(hash=kwargs['hash']))
        url = settings.SHORTURL_PREFIX + path
        qrcode_bytes = auq.qrcode_data(url, imgtype='svg')
        return djh.HttpResponse(qrcode_bytes, content_type="image/svg+xml")


class ShowRoomsView(djcam.LoginRequiredMixin,
                    AddIsDatenverwalter, AddSettings, vv.TemplateView):
    """Browse list of departments, buildings, rooms; navigate to QR codes."""
    template_name = "room/show_rooms.html"

    def get(self, request, *args, **kwargs):
        pop_org_dept_bldg_room(self)
        return super().get(request, *args, **kwargs)

    def get_context_data(self):
        context = super().get_context_data()
        if self.building:
            context['type'] = "building"
            context['rooms'] = arm.Room.objects.filter(
                    organization=self.organization,
                    department=self.department,
                    building=self.building)
        elif self.department:
            context['type'] = "department"
            context['buildings'] = (arm.Room.objects
                    .filter(organization=self.organization, 
                            department=self.department)
                    .order_by('building')
                    .values('building')
                    .annotate(rooms=Count("id", distinct=True)))
        else:
            context['type'] = "overview"
            context['departments'] = (arm.Room.objects
                    .order_by('organization', 'department')
                    .values('organization', 'department')
                    .annotate(buildings=Count("building", distinct=True)))
        return context


class VisitView(AddSettings, vv.CreateView):
    """Centerpiece: The registration dialog for room visitors."""
    model = arm.Visit
    form_class = arf.VisitForm
    template_name = "room/visit.html"

    def get_success_url(self):
        return dju.reverse('room:thankyou', 
                           kwargs=dict(hash=self.object.seat.hash))
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        hashvalue = self.kwargs['hash']
        if not arm.Seat.exists(hashvalue):
            raise djh.Http404()
        seat = arm.Seat.by_hash(hashvalue)
        ctx['seat'] = seat
        ctx['room'] = seat.room
        ctx['settings'] = settings
        retention_3g = settings.DATA_RETENTION_DAYS_STATUS_3G
        if settings.USE_STATUS_3G_FIELD and \
           retention_3g <= settings.DATA_RETENTION_DAYS:
            ctx['status_3g_stmt_de'] = ("Der 3G-Status wird bereits nach %d Tagen gelöscht." %
                                       retention_3g)
            ctx['status_3g_stmt_en'] = ("The vaccination status will be deleted after %d days." %
                                       retention_3g)
        else:
            ctx['status_3g_stmt_de'] = ctx['status_3g_stmt_en'] = ""
        return ctx

    
    def get_form(self, data=None, files=None, **kwargs):
        if data:  # POST
            data = {k: v for k, v in data.items()}  # extract ordinary dict
            return arf.VisitForm(data=data, files=files, **kwargs)
        # else GET:
        if COOKIENAME in self.request.COOKIES:
            try:
                thecookie = self.request.COOKIES[COOKIENAME]
                initial = json.loads(thecookie)
            except json.JSONDecodeError as err:
                tb = traceback.format_exc(limit=12, chain=True)
                logging.warning(f"VisitView: broken cookie >>>>{thecookie}<<<<\n{tb}")
                initial = dict(cookie=arm.Visit.make_cookie())
                logging.info(f"VisitView: ersatz {initial}")
        else:
            initial = dict(cookie=arm.Visit.make_cookie())
            logging.info(f"VisitView: new {initial}")
        initial['present_from_dt'] = aud.nowstring(date=False, time=True)
        return arf.VisitForm(initial=initial)
        
    def form_invalid(self, form: arf.VisitForm):
        msg = "Bitte Eingaben überprüfen / Please check your inputs"
        djcm.add_message(self.request, djcm.ERROR, msg)
        return super().form_invalid(form)

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


class ThankyouView(AddSettings, vv.TemplateView):
    template_name = "room/thankyou.html"
    with_seats = False  # initkwarg

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        hashvalue = self.kwargs['hash']
        ctx['hash'] = hashvalue
        if not self.with_seats:
            return ctx
        if not arm.Seat.exists(hashvalue):
            raise djh.Http404()
        seat = ctx['seat'] = arm.Seat.by_hash(hashvalue)
        room = ctx['room'] = seat.room
        ctx['with_seats'] = self.with_seats
        seats = (room.current_unique_visitors_qs()
            .values_list('seat__rownumber', 'seat__seatnumber'))
        seatlist = [f"r{s[0]}s{s[1]}" for s in sorted(seats)]
        ctx['seatlist'] = seatlist
        ctx['visitors_presentN'] = len(seatlist)
        return ctx


class LegacyThankyouView(djvgb.RedirectView):
    def get(self, *args, **kwargs):
        return djh.HttpResponsePermanentRedirect(dju.reverse_lazy('room:home'))


class UsageStatisticsView(djcam.LoginRequiredMixin,
                          AddIsDatenverwalter, AddSettings, vv.TemplateView):
    """Show table of #rooms and #visits per department."""
    template_name = "room/stats.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.is_datenverwalter:
            context['stats'] = arm.Room.usage_statistics()
        else:
            context['stats'] = []
        return context


class UncookieView(vv.GenericView):
    """Get rid of the cookie that stores the person data entered in VisitView."""
    def get(self, request, *args, **kwargs):
        response = djh.HttpResponse("Cookie expired")
        response.set_cookie(COOKIENAME, "", max_age=0)  # expire now
        return response


class SearchView(AddIsDatenverwalter, AddSettings, vv.ListView):
    """
    Dialog by which Datenverwalters retrieve contact group data.
    Kludge: Uses the same view for a valid form (instead of redirecting). 
    """
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
            ctx['LIMIT'] = 10000
            ctx['NUMRESULTS'] = len(ctx['visits'])
            if ctx['NUMRESULTS'] > ctx['LIMIT']:
                ctx['display_switch'] = 'too_many_results'
        else:
            assert False, f"SearchView: unexpected mode '{mode}'"
        return ctx

    def get_queryset(self):
        def fdt(d: dt.date):
            return djut.make_aware(dt.datetime(d.year, d.month, d.day))
        f = self.form.cleaned_data
        secure_organization = f['organization'] if self.is_datenverwalter \
            else settings.DUMMY_ORG
        if not settings.USE_EMAIL_FIELD:
            f['email'] = '%'  # insert dummy so we can use the full search
        return (arm.Visit.objects
                .filter(seat__room__organization__ilike=secure_organization)
                .filter(seat__room__department__ilike=f['department'])
                .filter(seat__room__building__ilike=f['building'])
                .filter(seat__room__room__ilike=f['room'])
                .filter(givenname__ilike=f['givenname'])
                .filter(familyname__ilike=f['familyname'])
                .filter(phone__ilike=f['phone'])
                .filter(email__ilike=f['email'])
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
        logging.getLogger('search').info(f"SearchView({logcontext}")

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
