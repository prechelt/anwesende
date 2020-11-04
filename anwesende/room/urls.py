from django.urls import path

import anwesende.room.views as arv

app_name = "room"
urlpatterns = [
    path("",
         view=arv.HomeView.as_view(), name="home"),
    path("import",
         view=arv.ImportView.as_view(), name="import"),
    path("qrcodes/<pk>",
         view=arv.QRcodesView.as_view(), name="qrcodes"),
    path("qrcode/<hash>",
         view=arv.QRcodeView.as_view(), name="qrcode"),
    path("v<hash>",
         view=arv.VisitView.as_view(), name="visit"),
    path("thankyou",
         view=arv.ThankyouView.as_view(), name="thankyou"),
    path("uncookie",
         view=arv.UncookieView.as_view(), name="uncookie"),
    path("search",
         view=arv.SearchView.as_view(), name="search"),
]
