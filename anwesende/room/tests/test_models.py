import typing as tg

import django.utils.timezone as djut
import pytest

import anwesende.room.models as arm
import anwesende.users.models as aum
import anwesende.utils.date as aud


@pytest.mark.django_db
def test_get_overlapping_visits():
    def _make_seats(importstep: arm.Importstep, roomname: str, 
                    numseats: int) -> tg.Tuple[arm.Seat, ...]:
        results = []
        room = arm.Room(organization="org", department="dep", building="bldg",
                        room=roomname, seat_min=1, seat_max=numseats, 
                        importstep=importstep)
        room.save()
        for i in range(numseats):
            seat = arm.Seat(hash=arm.Seat.seathash(room, i), number=i, room=room)
            seat.save()
            results.append(seat)
        return tuple(results)
    
    def _make_visit(seat: arm.Seat, tfrom: str, tto: str) -> arm.Visit:
        now = djut.now()
        present_from = aud.make_dt(now, tfrom)
        present_to = aud.make_dt(now, tto)
        assert present_from < present_to
        v = arm.Visit(givenname="gn", familyname="fn", 
                      street_and_number="sn", zipcode="12345", town="t",
                      phone="p", email="gn@fn.de",
                      submission_dt=now, 
                      present_from_dt=present_from, present_to_dt=present_to,
                      seat=seat)
        v.save()
        return v

    user = aum.User.objects.create(name="x")
    importstep = arm.Importstep(user=user)
    importstep.save()
    r1s1, r1s2 = _make_seats(importstep, "room1", 2)
    r2s1, = _make_seats(importstep, "room2", 1)
    targetvisit = _make_visit(r1s1, "03:00", "04:00")
    shorttargetvisit = _make_visit(r1s1, "03:00", "03:01")
    # --- the following other visits have _y if they are to be found, _n if not:
    otherroom_n = _make_visit(r2s1, "03:00", "04:00")
    before_n = _make_visit(r1s2, "02:00", "03:00")
    within_y = _make_visit(r1s2, "03:15", "03:45")
    across_y = _make_visit(r1s2, "02:00", "05:00")
    after_n = _make_visit(r1s2, "04:00", "05:00")
    halfbefore_y = _make_visit(r1s2, "02:30", "03:30")
    halfafter_y = _make_visit(r1s2, "03:30", "04:30")
    nearlybefore_n = _make_visit(r1s2, "02:00", "03:01")
    nearlyafter_n = _make_visit(r1s2, "03:59", "05:00")
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
