# see https://github.com/wemake-services/django-test-migrations
import typing as tg

import django_test_migrations.migrator as dtmm
import pytest


@pytest.mark.django_db
def test_room_descriptor_DATA_migration(migrator: dtmm.Migrator):
    #--- create migration state before introducing Room.descriptor:
    old_state = migrator.apply_initial_migration(('room', '0010_visit_status_3g'))

    #--- create a Room:
    User = old_state.apps.get_model('users', 'User')
    user = User.objects.create(name="x")  # needed for Importstep
    Importstep = old_state.apps.get_model('room', 'Importstep')
    importstep = Importstep.objects.create(user=user)  # needed for Room
    Room = old_state.apps.get_model('room', 'Room')
    to_be_migrated = Room.objects.create(
            organization="myorg", department="mydep", 
            building="mybldg", room="myroom",
            row_dist=1.3, seat_dist=0.8,
            seat_last="r2s3", importstep=importstep)
    assert getattr(to_be_migrated, 'descriptor', None) is None

    #--- migrate:
    new_state = migrator.apply_tested_migration([
            ('room', '0011_room_descriptor'),
            ('room', '0012_room_descriptor_DATA'), ])

    #--- assert descriptor is filled correctly:
    Room = new_state.apps.get_model('room', 'Room')
    newroom = Room.objects.get()
    assert newroom.descriptor == "myorg;mydep;mybldg;myroom"
