import datetime as dt
from pprint import pprint

import pytest

import anwesende.room.models as arm
import anwesende.room.reports as arr
import anwesende.room.tests.makedata as artmd

@pytest.mark.django_db
def test_visits_by_department_report():
   descr = dict(org1=
                dict(dep1=
                     dict(room1=(1,1),
                          room2=(2,2)),
                     dep2=
                     dict(room3=(3,4))),
                org2=
                dict(dep3=
                     dict(room4=(4,9),
                          room5=(5,16))))
   artmd.make_organizations(descr)
   assert arm.Room.objects.count() == 5
   assert arm.Seat.objects.count() == 15
   assert arm.Visit.objects.count() == 32
   result = list(arr.visits_by_department_report())
   pprint(result)
   should = [
       {'organization': 'org1', 'department': 'dep1',
          'rooms': 2,  'seats': 3,  'visits': 3},
       {'organization': 'org1', 'department': 'dep2',
          'rooms': 1,  'seats': 3,  'visits': 4},
       {'organization': 'org2', 'department': 'dep3',
          'rooms': 2,  'seats': 9,  'visits': 25} ]
   assert result == should


@pytest.mark.django_db
def test_visitors_by_week_report(freezer):
    #----- first week: create rooms and some visits:
    freezer.move_to("2021-12-03T02:03")
    seat_r1, = artmd.make_seats("room1", 1, "org1", "dep1")
    seat_r2, = artmd.make_seats("room2", 1, "org1", "dep1")
    seat_r2b, = artmd.make_seats("room2", 1, "org2", "dep2")
    artmd.make_visit(seat_r1, "p1")
    artmd.make_visit(seat_r2, "p1")
    artmd.make_visit(seat_r2, "p2")
    artmd.make_visit(seat_r2b, "p1")
    artmd.make_visit(seat_r2b, "p3")
    artmd.make_visit(seat_r2b, "p4")
    artmd.make_visit(seat_r2b, "p5")

    #----- second week: create more visits:
    freezer.move_to("2021-12-10T02:10")
    artmd.make_visit(seat_r2, "p1")
    artmd.make_visit(seat_r2, "p1")  # double registration
    artmd.make_visit(seat_r2, "p2")

    #----- that evening, look at report:
    freezer.move_to("2021-12-10T18:00")
    #-- first week:
    wr = arr.visitors_by_week_report("%")
    assert wr[0].organizationsN == 2
    assert wr[0].departmentsN == 2
    assert wr[0].buildingsN == 2  # all same name
    assert wr[0].roomsN == 3  # only 2 different names
    assert wr[0].visitorsN == 5
    assert wr[0].visitsN == 7
    assert wr[0].visits_per_visitor == 7/5

    #-- second week:
    assert wr[0].organizationsN == 2
    assert wr[0].departmentsN == 2
    assert wr[0].buildingsN == 2
    assert wr[0].roomsN == 3  # 
    assert wr[0].visitorsN == 5
    assert wr[0].visitsN == 7
    assert wr[0].visits_per_visitor == 7/5

    #-- first week, narrowed search:
    wr = arr.visitors_by_week_report("%dep1%")
    assert wr[0].organizationsN == 1
    assert wr[0].departmentsN == 1
    assert wr[0].buildingsN == 1
    assert wr[0].roomsN == 2
    assert wr[0].visitorsN == 2
    assert wr[0].visitsN == 3
    assert wr[0].visits_per_visitor == 3/2


