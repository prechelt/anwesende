from django.urls import path

import anwesende.users.views as auv

app_name = "users"
urlpatterns = [
    path("~redirect/", view=auv.user_redirect_view, name="redirect"),
    path("~update/", view=auv.user_update_view, name="update"),
    path("<str:username>/", view=auv.user_detail_view, name="detail"),
]
