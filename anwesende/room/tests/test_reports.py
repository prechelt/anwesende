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

