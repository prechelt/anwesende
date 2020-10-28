import datetime as dt

import django.contrib.auth.models as djcam
import django.utils.timezone as djut
import pytest
from django.conf import settings

import anwesende.room.management.commands.delete_outdated_data as delete_outdated_data
import anwesende.room.management.commands.make_base_data as make_base_data
import anwesende.room.models as arm
import anwesende.room.tests.makedata as artm

@pytest.mark.django_db
def test_make_base_data():
    assert djcam.Group.objects.count() == 0
    make_base_data.Command().handle()
    dvgroup = djcam.Group.objects.get()  # must exist now
    make_base_data.Command().handle()  # must be idempotent
    assert dvgroup == djcam.Group.objects.get()


@pytest.mark.django_db
def test_deleted_outdated_data(freezer, caplog):
    freezer.move_to("2020-10-01")
    batch1 = artm.make_user_rooms_seats_visits(seatsN=5, visitsN=25)
    assert arm.Visit.objects.count() == 2*25
    freezer.move_to("2020-11-01")
    batch2 = artm.make_user_rooms_seats_visits(seatsN=4, visitsN=33)
    assert arm.Room.objects.count() == 2 + 2
    assert arm.Visit.objects.count() == 2 * (25 + 33)
    delete_outdated_data.Command().handle()  # should delete batch 1
    assert arm.Visit.objects.count() == 2 * 33
    msg = caplog.records[0].msg
    assert "deleting 50 (of " in msg
