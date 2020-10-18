import datetime as dt
import random
import typing as tg

import django.utils.timezone as djut
import pytest

import anwesende.room.models as arm


@pytest.mark.django_db
def test_get_overlapping_visits():
    def _make_seats(importstep: arm.Importstep, roomname: str, numseats: int
                   ) -> tg.Tuple[arm.Seat]:
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
    
    def _make_visit(seat: arm.Seat, tfrom: tg.Tuple, tto: tg.Tuple) -> arm.Visit:
        def _thetime(hhmm: tg.Tuple[int]):
            timehhmm = dt.time(hhmm[0], hhmm[1], 
                               tzinfo=djut.get_current_timezone())
            result = dt.datetime.combine(date=reftime, time=timehhmm,
                                         tzinfo=djut.get_current_timezone())
            print("timehhmm", timehhmm, " thetime", result)
            return result
        
        present_from = _thetime(tfrom)
        present_to = _thetime(tto)
        v = arm.Visit(givenname="gn", familyname="fn", 
                      street_and_number="sn", zipcode="12345", town="t",
                      phone="p", email="gn@fn.de",
                      submission_dt=djut.now(), 
                      present_from_dt=present_from, present_to_dt=present_to,
                      seat=seat)
        v.save()
        return v

    importstep = arm.Importstep(randomkey=str(random.randrange(100000, 999999)))
    importstep.save()
    reftime = djut.now()
    r1s1, r1s2 = _make_seats(importstep, "room1", 2)
    r2s1, = _make_seats(importstep, "room2", 1)
    targetvisit = _make_visit(r1s1, (3, 00), (4, 00))
    shorttargetvisit = _make_visit(r1s1, (3, 00), (3, 1))
    # the following other visits have _y if they are to be found, _n if not:
    otherroom_n = _make_visit(r2s1, (3, 00), (4, 00))
    before_n = _make_visit(r1s2, (2, 00), (3, 00))
    within_y = _make_visit(r1s2, (3, 15), (3, 45))
    across_y = _make_visit(r1s2, (2, 00), (5, 00))
    after_n = _make_visit(r1s2, (4, 00), (5, 00))
    halfbefore_y = _make_visit(r1s2, (2, 30), (3, 30))
    halfafter_y = _make_visit(r1s2, (3, 30), (4, 30))
    nearlybefore_n = _make_visit(r1s2, (2, 00), (3, 1))
    nearlyafter_n = _make_visit(r1s2, (3, 59), (5, 00))
    #--- now look which ones appear:
    results = set(targetvisit.get_overlapping_visits())
    print("djut.get_current_timezone() =", djut.get_current_timezone().__repr__())
    print("results", results)
    expected = set((within_y, across_y, halfbefore_y, halfafter_y))
    not_expected = set((otherroom_n, before_n, after_n, nearlybefore_n, nearlyafter_n))
    print("expected", expected)
    print("not_expected", not_expected)
    assert False
    assert results.isdisjoint(not_expected)
    assert results == expected
