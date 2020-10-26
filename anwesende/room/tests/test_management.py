import django.contrib.auth.models as djcam
import pytest

import anwesende.room.management.commands.make_base_data as make_base_data


@pytest.mark.django_db
def test_make_base_data():
    assert djcam.Group.objects.count() == 0
    make_base_data.Command().handle()
    dvgroup = djcam.Group.objects.get()  # must exist now
    make_base_data.Command().handle()  # must be idempotent
    assert dvgroup == djcam.Group.objects.get()
