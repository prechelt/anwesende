from django.apps import AppConfig


class RoomConfig(AppConfig):
    name = "anwesende.room"
    verbose_name = "Room"

    def ready(self):
        _ensure_datenverwalter_group()
        try:
            import anwesende.room.signals  # noqa F401
        except ImportError:
            pass


def _ensure_datenverwalter_group():
    import django.contrib.auth.models as djcam

    import anwesende.room.models as arm
    print("##### _ensure_datenverwalter_group")
    if not djcam.Group.objects.filter(name=arm.STAFF_GROUP).exists():
        djcam.Group.objects.create(name=arm.STAFF_GROUP)
        print("##### STAFF_GROUP created!")
