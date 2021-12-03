import copy
import math
from pprint import pprint
import typing as tg

import django.utils.timezone as djut
from freezegun import freeze_time
import pytest

import anwesende.room.models as arm
import anwesende.room.tests.makedata as artmd
import anwesende.users.models as aum
import anwesende.utils.date as aud


@pytest.mark.django_db
def test_room_descriptor():
    rm1s1, = artmd.make_seats("myroom", 1)
    rm2s1, = artmd.make_seats("otherroom", 1)
    v1 = artmd.make_visit(rm1s1, "p1", "02:00", "04:00")  # noqa
    v2 = artmd.make_visit(rm2s1, "p2", "02:00", "04:00")  # noqa
    myroom = arm.Room.objects.get(room="myroom")
    assert myroom.descriptor == "org;dep;bldg;myroom"


@pytest.mark.django_db
def test_get_overlapping_visits():
    # test can fail if run very shortly before midnight, just run it again
    rm1s1, rm1s2 = artmd.make_seats("room1", 2)
    rm2s1, = artmd.make_seats("room2", 1)
    targetvisit = artmd.make_visit(rm1s1, "p1", "03:00", "04:00")
    shorttargetvisit = artmd.make_visit(rm1s1, "p1", "03:00", "03:01")
    # --- the following other visits have _y if they are to be found, _n if not:
    otherroom_n = artmd.make_visit(rm2s1, "p2", "03:00", "04:00")
    before_n = artmd.make_visit(rm1s2, "p3", "02:00", "03:00")
    within_y = artmd.make_visit(rm1s2, "p4", "03:15", "03:45")
    across_y = artmd.make_visit(rm1s2, "p5", "02:00", "05:00")
    after_n = artmd.make_visit(rm1s2, "p3", "04:00", "05:00")
    halfbefore_y = artmd.make_visit(rm1s2, "p6", "02:30", "03:30")
    halfafter_y = artmd.make_visit(rm1s2, "p7", "03:30", "04:30")
    nearlybefore_n = artmd.make_visit(rm1s2, "p8", "02:00", "03:01")
    nearlyafter_n = artmd.make_visit(rm1s2, "p9", "03:59", "05:00")
    # --- now look which ones appear for targetvisit:
    results = set(targetvisit.get_overlapping_visits())
    result_pks = set(el.pk for el in results)
    expected = set(el.pk for el in (targetvisit, within_y, across_y, halfbefore_y, halfafter_y))
    not_expected = set(el.pk for el in (otherroom_n, before_n, after_n, nearlybefore_n, nearlyafter_n))
    print("result_pks", result_pks)
    print("expected", expected)
    print("not_expected", not_expected)
    assert result_pks.isdisjoint(not_expected)
    assert result_pks == expected
    # --- now look which ones appear for shorttargetvisit:
    assert shorttargetvisit.get_overlapping_visits().count() == 0


@pytest.mark.django_db
def test_current_unique_visitorsN():
    # test can fail if run very shortly before midnight, just run it again
    def show_them(room):
        them = room.current_unique_visitors_qs()
        print ([v.email for v in them])
    rm1s1, rm1s2, rm1s3 = artmd.make_seats("room1", 3)
    rm2s1, = artmd.make_seats("room2", 1)
    room = rm1s1.room
    person1_early = artmd.make_visit(rm1s1, "p1", "02:58", "04:00")  # noqa
    person2_ontime = artmd.make_visit(rm1s2, "p2", "03:00", "04:00")  # noqa
    person3_late = artmd.make_visit(rm1s3, "p3", "03:03", "04:00")  # noqa
    person4_otherroom = artmd.make_visit(rm2s1, "p4", "03:00", "04:00")  # noqa
    person3_changed = artmd.make_visit(rm1s1, "p3", "03:30", "04:00")  # noqa
    # --- now look at different times how many are in rm1:
    def freeze_at(ts: str):
        return freeze_time(aud.make_dt('now', ts))
    with freeze_at("02:50"):
        show_them(room)
        assert room.current_unique_visitorsN() == 0
    with freeze_at("02:59"):
        show_them(room)
        assert room.current_unique_visitorsN() == 1
    with freeze_at("03:01"):
        show_them(room)
        assert room.current_unique_visitorsN() == 2
    with freeze_at("03:06"):
        show_them(room)
        assert room.current_unique_visitorsN() == 3
    with freeze_at("03:33"):
        show_them(room)
        assert room.current_unique_visitorsN() == 3
    with freeze_at("05:00"):
        show_them(room)
        assert room.current_unique_visitorsN() == 0


@pytest.mark.django_db
def test_get_dummy_seat():
    dummy1 = arm.Seat.get_dummy_seat()
    dummy2 = arm.Seat.get_dummy_seat()
    assert dummy1 == dummy2  # from DB query, hence not necessarily also 'is' 
    assert arm.Seat.objects.count() == 1


@pytest.mark.django_db
def test_split_seatname():
    dummy = arm.Seat.get_dummy_seat()
    dummy.seatnumber = 3
    assert dummy.seatname == "r1s3"
    assert dummy.seatname == arm.Seat.form_seatname(1, 3)
    assert (1, 3) == dummy.split_seatname(dummy.seatname)


@pytest.mark.django_db
def test_distance_in_m():
    dummy = arm.Seat.get_dummy_seat()
    other = copy.copy(dummy)
    other.rownumber = 2
    other.seatnumber = 3
    r_dist = ((other.rownumber-1) * dummy.room.row_dist)
    s_dist = ((other.seatnumber-1) * dummy.room.seat_dist)
    dist_is = dummy.distance_in_m(other)
    dist_should = math.sqrt(s_dist**2 + r_dist**2)
    assert abs(dist_is - dist_should) < 0.0001
