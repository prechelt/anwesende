import django.contrib.auth.models as djcam
import pytest

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
def test_delete_outdated_data(freezer, caplog):
    # --- make batch 1 of visits:
    freezer.move_to("2020-10-01")
    artm.make_user_rooms_seats_visits(seat_last="r1s5", visitsN=25)
    assert arm.Visit.objects.count() == 2 * 25
    # --- make later batch 2:
    freezer.move_to("2020-11-01")
    artm.make_user_rooms_seats_visits(seat_last="r2s2", visitsN=33)
    assert arm.Room.objects.count() == 2 + 2
    assert arm.Visit.objects.count() == 2 * (25 + 33)
    # --- delete batch 1 and check:
    delete_outdated_data.Command().handle()  # should delete batch 1
    assert arm.Visit.objects.count() == 2 * 33
    msg = caplog.records[0].msg
    assert "deleting 50 " in msg
    assert "(of 116 existing)" in msg
