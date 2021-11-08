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
def test_workflow_happy_path(django_app: wt.TestApp):
    """Use every important page once and check they play together properly."""
    # https://docs.pylonsproject.org/projects/webtest/en/latest/api.html
    xlsx_file = 'anwesende/room/tests/data/rooms1.xlsx'
    beacon_from_xlsx = "MathInf"
    datenverwalter = artm.make_datenverwalter_user("datenverwalter", "1234")  # noqa
    _log_in(django_app, "datenverwalter", "1234")
    seathash, current_html = _test_excel_import(django_app, xlsx_file, beacon_from_xlsx)
    _browse_qrcodes(django_app)
    _log_out(django_app, current_html)
    _make_visits(django_app, seathash)
    resp = _log_in(django_app, "datenverwalter", "1234")
    _browse_usage_statistic(django_app)
    _search_and_download(django_app)

def freeze_at(daytime_string: str):
    return freeze_time(aud.make_dt('now', daytime_string))

def _log_in(django_app: wt.TestApp, username: str, password: str) -> wt.TestResponse:
    # base.html: <a id="log-in-link" class="nav-link" href="{% url 'account_login' %}">Datenverwaltung</a>
    resp = django_app.get("/")
    regexp = r"""<a [^>]*href="([^"]*)"[^>]*>Datenverwaltung</a>"""
    mm = re.search(regexp, resp.text)
    assert mm, f"log-in link '{regexp}' not found in page"
    login_page = django_app.get(mm.group(1))
    login_form = login_page.form
    login_form['login'] = username
    login_form['password'] = password
    return login_form.submit().follow()


def _test_excel_import(django_app, xlsx_file: str, beacon: str) -> tg.Tuple[str, str]:
    # --- get /import:
    import_url = reverse('room:import')
    import_page = django_app.get(import_url)
    assert import_page.status == '200 OK'
    # --- make file upload:
    uploadform = import_page.form
    uploadform['file'] = wt.Upload(xlsx_file)
    resp = uploadform.submit()
    qrcodes_page = resp.follow()
    assert beacon in qrcodes_page.text  # content from xlsx_file 
    # --- get a QR-code image:
    seathash: str = arm.Seat.objects.last().hash  # type: ignore[union-attr,assignment]
    url = reverse('room:qrcode', kwargs=dict(hash=seathash))
    qrcode_response = django_app.get(url)
    assert qrcode_response.headers['Content-Type'] == 'image/svg+xml'
    return (seathash, qrcodes_page.text)


def _browse_qrcodes(django_app):
    # most assertions are implicit: django_app.get could fail
    print("## 1. overview page:")
    resp1 = django_app.get('/').click(href=reverse('room:show-rooms'))
    link1rooms = resp1.html.find(name='a', class_='show-rooms-department')

    print("## 2. department-level page:")
    print("link1rooms:", link1rooms['href'])
    resp2 = django_app.get(link1rooms['href'])
    link2rooms = resp2.html.find(name='a', class_='show-rooms-building')
    link2codes = resp2.html.find(name='a', class_='qrcodes-building')

    print("## 3. building-level browse page:")
    resp3 = django_app.get(link2rooms['href'])
    link3codes = resp3.html.find(name='a', class_='qrcodes-room')

    print("## 4. building-level qrcodes page:")
    resp4 = django_app.get(link2codes['href'])
    assert len(resp4.html.find_all(name='img', class_='qrcode')) == 2*7 + 2*3

    print("## 5. room-level qrcodes page:")
    resp5 = django_app.get(link3codes['href'])
    assert len(resp5.html.find_all(name='img', class_='qrcode')) == 2*7


def _log_out(django_app: wt.TestApp, html: str) -> wt.TestResponse:
    # base.html:  <a class="nav-link" href="{% url 'account_logout' %}">Abmelden</a>
    regexp = r"""<a [^>]*href="([^"]*)"[^>]*>Abmelden</a>"""
    mm = re.search(regexp, html)
    assert mm, f"log-out link '{regexp}' not found in page"
    logout_url = mm.group(1)
    resp = django_app.get(logout_url)
    resp.form.submit()  # Answer "Are you sure you want to log out?" page
    return resp


def _make_visits(django_app: wt.TestApp, seathash: str):
    # --- get visit form:
    # we take a shortcut here and neither actually read the QR code,
    # nor simulate the redirect from settings.SHORTURL_PREFIX
    visit_url = reverse('room:visit', kwargs=dict(hash=seathash))
    data = dict(givenname="A.", familyname="Fam", 
                street_and_number="Str.1", zipcode="12345", town="Town",
                phone="+49 1234 1", 
                email="a@fam.de",
                status_3g=str(arm.G_IMPFT),
                present_from_dt="11:00", present_to_dt="12:00")
    # --- fill visit form once:
    with freeze_at("11:01"):
        visit_page = django_app.get(visit_url)
        _fill_with(visit_page.form, data)
        resp = visit_page.form.submit()
        # resp.showbrowser()  # activate if follow fails
        # print("container:", _find(resp.text, name="div", class_="container"))
        resp = resp.follow()
        who = arm.Visit.objects.all()
        print([str(v) for v in who])
    assert resp.request.path == reverse('room:thankyou', kwargs=dict(hash=seathash))
    assert "1</b> verschiedene" in resp.text  # visitors_presentN

    # --- check DB contents:
    visit = arm.Visit.objects.last()
    if settings.USE_EMAIL_FIELD:
        assert visit.email == "a@fam.de"  # type: ignore[union-attr]
    mytime = djut.localtime(value=visit.present_from_dt).strftime("%H:%M")  # type: ignore[arg-type,union-attr]
    assert mytime == "11:00"
    # --- fill visit form again (same device, overlapping time):
    visit_page_with_cookie = django_app.get(visit_url)
    del data['present_from_dt']  # not stored in cookie
    del data['present_to_dt']  # not stored in cookie
    _check_against(visit_page_with_cookie.form, data)
    changed_data = dict(givenname="B.",
                        phone="+49 1234 2", 
                        email="b@fam.de",
                        present_from_dt="11:20", present_to_dt="12:00")
    _fill_with(visit_page_with_cookie.form, changed_data)
    with freeze_at("11:21"):
        resp = visit_page_with_cookie.form.submit().follow()
    assert resp.request.path == reverse('room:thankyou', kwargs=dict(hash=seathash))
    assert "2</b> verschiedene" in resp.text  # visitors_presentN

    # --- fill visit form again (same device, later time):
    visit_page3 = django_app.get(visit_url)
    del changed_data['present_from_dt']  # not stored in cookie
    del changed_data['present_to_dt']  # not stored in cookie
    _check_against(visit_page3.form, changed_data)  # partial check suffices
    changed_data3 = dict(givenname="C.",
                         phone="+49 1234 3", 
                         email="c@fam.de",
                         present_from_dt="13:00", present_to_dt="14:00")
    _fill_with(visit_page3.form, changed_data3)
    resp = visit_page3.form.submit().follow()


def _browse_usage_statistic(django_app):
    resp = django_app.get('/').click(href=reverse('room:stats'))
    # the following checks are very minimal only:
    assert "<td>20</td>" in resp.text  # seats
    assert "<td>2</td>" in resp.text  # visits

def _search_and_download(django_app: wt.TestApp):
    # base.html: <a href="/import">QR-Codes erzeugen</a>
    # and        <a href="/search">Nach Personen suchen</a>
    resp = django_app.get("/")
    search_url = _check_menu(resp.text)
    search1 = django_app.get(search_url)
    # the following is hardcoded against data values in _make_visits:
    # --- search:
    data = dict(givenname="A.",
                from_date=aud.nowstring(), to_date=aud.nowstring())
    _fill_with(search1.form, data)
    search2 = search1.form.submit('visit')
    # print("container:", _find(search2.text, name="div", class_="container"))
    if settings.USE_EMAIL_FIELD:
        assert "a@fam.de" in search2.text
        assert "b@fam.de" not in search2.text
        assert "c@fam.de" not in search2.text
    assert "A." in search2.text
    assert "B." not in search2.text
    assert "C." not in search2.text
    # --- find contacts:
    search3 = search2.form.submit('visitgroup')
    # print("searchhits:", _find(search3.text, name="ol", class_="searchhits"))
    if settings.USE_EMAIL_FIELD:
        assert "a@fam.de" in search3.text
        assert "b@fam.de" in search3.text
        assert "c@fam.de" not in search3.text
    assert "A." in search3.text
    assert "B." in search3.text
    assert "C." not in search3.text
    # --- download Excelfile:
    search4 = search3.form.submit('xlsx')
    excelbytes = search4.body
    _validate_excel(excelbytes)


def _check_menu(current_html: str) -> str:
    regexp1 = r"""<a href="/import">[^<]*QR-Codes[^<]*</a>"""
    regexp2 = r"""<a href="(/search)">[^<]*uche[^<]*</a>"""
    mm = re.search(regexp1, current_html)
    assert mm, f"import link '{regexp1}' not found in page"
    mm = re.search(regexp2, current_html)
    assert mm, f"search link '{regexp2}' not found in page"
    return mm.group(1)


def _validate_excel(excelbytes: bytes) -> None:
    with tempfile.NamedTemporaryFile(mode='w+b', suffix='.xlsx', delete=False) as fp:
        fp.write(excelbytes)
        fp.close()
        coldict = aue.read_excel_as_columnsdict(fp.name)
        os.remove(fp.name)
        if settings.USE_EMAIL_FIELD:
            assert coldict['email'] == ["a@fam.de", "b@fam.de"]
        assert coldict['givenname'] == ["A.", "B."]


# ========== helpers:


def _fill_with(form: wt.Form, data: dict):
    for k, v in data.items():
        if k == 'email' and not settings.USE_EMAIL_FIELD:
            continue  # skip field 'email' 
        form[k] = v


def _check_against(form: wt.Form, data: dict):
    for k, v in data.items():
        if k == 'email' and not settings.USE_EMAIL_FIELD:
            continue  # skip field 'email' 
        assert form[k].value == v


def _find(html: str, **kwargs):
    soup = bs4.BeautifulSoup(html, "html.parser")
    return "".join((str(tag) for tag in soup.find(**kwargs).contents))

def _findtag(html: str, **kwargs):
    soup = bs4.BeautifulSoup(html, "html.parser")
    return soup.find(**kwargs)
