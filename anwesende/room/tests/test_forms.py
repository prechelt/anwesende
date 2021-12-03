import datetime as dt
import typing as tg

import django.core.exceptions as djce
import django.utils.timezone as djut
import pytest

import anwesende.room.forms as arf
import anwesende.room.models as arm
import anwesende.room.tests.makedata as artmd
import anwesende.utils.date as aud


def test_TimeOnlyDateTimeField_to_python_OK():
    fmt = "%Y-%m-%d %H:%M"
    now = djut.localtime().strftime(fmt)
    for input in ("17:27", "1727"):
        dt_val = arf.TimeOnlyDateTimeField().to_python(input)
        dt_str = dt_val.strftime(fmt)
        print(f"{input} --> {dt_str}")
        assert dt_str[-5:] == "17:27"   # correct time
        assert dt_str[:10] == now[:10]  # today's date


def test_TimeOnlyDateTimeField_to_python_wrong():
    with pytest.raises(djce.ValidationError) as ex:
        dt_val = arf.TimeOnlyDateTimeField().to_python("37:27")  # noqa
    assert "Falsches Uhrzeitformat" in str(ex.value)


def test_TimeRangeField_to_python_OK():
    now = djut.localtime()
    recently = now - dt.timedelta(hours=2)  # range is 2hrs ago until now
    minute = dt.timedelta(minutes=1)
    timerange_str = "%s %s-%s" % (
        now.strftime('%Y-%m-%d'), 
        recently.strftime('%H:%M'), now.strftime('%H:%M'))
    dt_from, dt_to = arf.TimeRangeField().to_python(timerange_str)
    assert recently-minute < dt_from < recently+minute
    assert now-minute < dt_to < now+minute


def test_TimeRangeField_to_python_wrong():
    range = lambda rangestr: arf.TimeRangeField().to_python(rangestr)
    with pytest.raises(djce.ValidationError) as ex:
        range("some stuff")
    assert "Falsches Zeitraumformat" in str(ex.value)
    with pytest.raises(djce.ValidationError) as ex:
        range("2021-11-31 01:00-02:00")  # 31st does not exist
    assert "day is out of range" in str(ex.value)
    with pytest.raises(djce.ValidationError) as ex:
        range("2021-11-13 02:00-03:60")  # minute 60 does not exist
    assert "Falsches Zeitraumformat" in str(ex.value)
    with pytest.raises(djce.ValidationError) as ex:
        range("2021-11-13 03:00-03:00")  # empty range
    assert "Anfang muss vor Ende liegen" in str(ex.value)
    with pytest.raises(djce.ValidationError) as ex:
        range("2021-11-13 04:00-03:00")  # inverted range
    assert "Anfang muss vor Ende liegen" in str(ex.value)


@pytest.mark.django_db
def test_SearchByRoomForm():
    def tr(times: str) -> str:
        return f"{aud.nowstring()} {times}"
    def get_rooms(descr, times) -> tg.Set[arm.Room]:
        f = arf.SearchByRoomForm(dict(roomdescriptor=descr, timerange=tr(times)))
        f.full_clean()
        return set(f.cleaned_data['rooms_qs'])
    def get_visits(descr, times) -> tg.Set[arm.Visit]:
        f = arf.SearchByRoomForm(dict(roomdescriptor=descr, timerange=tr(times)))
        f.full_clean()
        return set(f.cleaned_data['visits_qs'])
    #----- create data:
    rm1s1, = artmd.make_seats("myroom", 1)
    rm2s1, = artmd.make_seats("otherroom", 1)
    rm1, rm2 = (rm1s1.room, rm2s1.room)
    v11 = artmd.make_visit(rm1s1, "p11", "02:00", "04:00")  # noqa
    v12 = artmd.make_visit(rm1s1, "p12", "03:00", "05:00")  # noqa
    v21 = artmd.make_visit(rm2s1, "p21", "02:00", "04:00")  # noqa
    #----- check rooms_qs:
    assert get_rooms("%myroom", "02:00-04:00") == set((rm1,))
    assert get_rooms("%org%", "02:00-04:00") == set((rm1, rm2))
    assert get_rooms("---", "02:00-04:00") == set()
    #----- check visits_qs:
    assert get_visits("%myroom", "02:00-04:00") == set((v11, v12))
    assert get_visits("%myroom", "02:00-02:40") == set((v11,))
    assert get_visits("%myroom", "01:00-02:40") == set((v11,))
    assert get_visits("%myroom", "02:20-03:01") == set((v11,))  # too short for v12
    assert get_visits("%org%", "01:00-05:00") == set((v11, v12, v21))
    assert get_visits("---", "01:00-05:00") == set()
