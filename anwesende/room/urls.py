from django.urls import path

import anwesende.room.views as arv

app_name = "users"
urlpatterns = [
    path("import", 
         view=arv.ImportView.as_view(), name="import"),
    path("qrcodes/<pk>/<int:randomkey>",
         view=arv.QRcodesView.as_view(), name="qrcodes"),
]
