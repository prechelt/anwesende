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
    # --- make batch 1 of visits (to be deleted):
    freezer.move_to("2020-10-01T12:00")
    artm.make_user_rooms_seats_visits(seat_last="r1s5", visitsN=25)
    assert arm.Visit.objects.count() == 2 * 25
    # --- make batch 2 of visits (status_3g just to be deleted):
    freezer.move_to("2020-10-30T11:00")
    artm.make_user_rooms_seats_visits(seat_last="r1s4", visitsN=1)
    assert arm.Visit.objects.count() == 2 * (25 + 1)
    # --- make batch 3 of visits (status_3g just still to be kept):
    freezer.move_to("2020-10-30T13:00")
    artm.make_user_rooms_seats_visits(seat_last="r1s4", visitsN=1)
    assert arm.Visit.objects.count() == 2 * (25 + 1 + 1)
    # --- make later batch 4:
    freezer.move_to("2020-11-01T12:00")
    artm.make_user_rooms_seats_visits(seat_last="r2s2", visitsN=33)
    assert arm.Room.objects.count() == 2 * (1 + 1 + 1 + 1)
    assert arm.Visit.objects.count() == 2 * (25 + 1 + 1 + 33)
    # --- delete batch 1 and check:
    freezer.move_to("2020-11-01T12:01")
    # delete batch 1, delete status_3g from batch 2, keep everything else:
    delete_outdated_data.Command().handle()
    assert arm.Visit.objects.count() == 2 * (1 + 1 + 33)
    assert arm.Visit.objects.filter(status_3g=arm.G_UNKNOWN).count() == 2 * 1
    msg = [rec.msg for rec in caplog.records]
    assert "deleting 50 " in msg[0]
    assert "(of 120 existing)" in msg[0]
    assert "cleansing 2 " in msg[1]
    assert "(of 70 existing)" in msg[1]
