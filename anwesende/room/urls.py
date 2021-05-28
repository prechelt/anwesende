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
    path("qroverview",
         view=arv.QRoverView.as_view(), name="qroverview"),
    path("qrcodes/<pk>",
         view=arv.QRcodesView.as_view(), name="qrcodes"),
    path("qrcodes-department/<pk>",
         view=arv.QRcodesDepView.as_view(), name="qrcodesdep"),
    path("qrcode/<hash>",
         view=arv.QRcodeView.as_view(), name="qrcode"),
    path("S<hash>",
         view=arv.VisitView.as_view(), name="visit"),
    path("search",
         view=arv.SearchView.as_view(), name="search"),
    path("stats",
         view=arv.UsageStatisticsView.as_view(), name="stats"),
    path("thankyou/visitors_presentN=<visitors_presentN>",
         view=arv.ThankyouView.as_view(), name="thankyou"),
    path("uncookie",
         view=arv.UncookieView.as_view(), name="uncookie"),
    path('favicon.ico', RedirectView.as_view(
        url=staticfiles_storage.url('images/favicon.ico')))
]
