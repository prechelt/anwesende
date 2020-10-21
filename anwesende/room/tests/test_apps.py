import django.contrib.auth.models as djcam
import pytest

import anwesende.room.apps as ara


@pytest.mark.django_db
def test_STAFF_GROUP_init():
    assert djcam.Group.objects.count() == 0
    ara._ensure_datenverwalter_group()
    dvgroup = djcam.Group.objects.get()  # must exist now
    ara._ensure_datenverwalter_group()  # must be idempotent
    assert dvgroup == djcam.Group.objects.get()
