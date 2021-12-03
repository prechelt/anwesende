from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import path
from django.views.generic.base import RedirectView

import anwesende.room.views as arv

app_name = "room"
urlpatterns = [
    path("",
         view=arv.HomeView.as_view(), name="home"),
    path("faq",
         view=arv.FAQView.as_view(), name="faq"),
    path("import",
         view=arv.ImportView.as_view(), name="import"),
    path("qrcodes/<pk>",
         view=arv.QRcodesByImportView.as_view(), name="qrcodes-byimport"),
    path("qrcodes/<organization>/<department>/<building>",
         view=arv.QRcodesByRoomsView.as_view(), name="qrcodes-byorgdepbld"),
    path("qrcodes/<organization>/<department>/<building>/<room>",
         view=arv.QRcodesByRoomsView.as_view(), name="qrcodes-byorgdepbldrm"),
    path("qrcode/<hash>",
         view=arv.QRcodeView.as_view(), name="qrcode"),
    path("S<hash>",
         view=arv.VisitView.as_view(), name="visit"),
    path("search",
         view=arv.SearchView.as_view(), name="search"),
    path("search_room",
         view=arv.SearchByRoomView.as_view(), name="searchroom"),
    path("show_rooms",
         view=arv.ShowRoomsView.as_view(), name="show-rooms"),
    path("show_rooms/<organization>/<department>",
         view=arv.ShowRoomsView.as_view(), name="show-rooms-department"),
    path("show_rooms/<organization>/<department>/<building>",
         view=arv.ShowRoomsView.as_view(), name="show-rooms-building"),
    path("report_dept",
         view=arv.VisitsByDepartmentView.as_view(), name="report_dept"),
    path("report_week",
         view=arv.VisitorsByWeekView.as_view(), name="report_week"),
    path("thankyou/S<hash>",
         view=arv.ThankyouView.as_view(), name="thankyou"),
    path("thankyou/S<hash>/seats",
         view=arv.ThankyouView.as_view(with_seats=True), name="thankyouseats"),
    path("thankyou/visitors_presentN=<visitors_presentN>",
         view=arv.LegacyThankyouView.as_view(), name="legacy_thankyou"),
    path("uncookie",
         view=arv.UncookieView.as_view(), name="uncookie"),
    path('favicon.ico', RedirectView.as_view(
        url=staticfiles_storage.url('images/favicon.ico')))
]
