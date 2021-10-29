import os
import re
import tempfile
import typing as tg

import bs4
from django.conf import settings
import django.utils.timezone as djut
import pytest
import webtest as wt
from django.urls import reverse
from freezegun import freeze_time

import anwesende.room.models as arm
import anwesende.room.tests.makedata as artm
import anwesende.utils.date as aud
import anwesende.utils.excel as aue


@pytest.mark.django_db
def test_import_POST_nologin(django_app: wt.TestApp):
    # https://docs.pylonsproject.org/projects/webtest/en/latest/api.html
    excelfile = "anwesende/static/xlsx/roomdata-example.xlsx"
    importpage = django_app.get(reverse('room:import'))  # can GET without login
    form1 = importpage.form
    form1['file'] = wt.Upload(excelfile)
    resp = form1.submit().follow()  # POST requires login: must redirect
    assert resp.request.path == reverse('account_login')
