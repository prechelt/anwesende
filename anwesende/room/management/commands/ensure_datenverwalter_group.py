import django.contrib.auth.models as djcam
import django.core.management.base as djcmb

import anwesende.room.models as arm


class Command(djcmb.BaseCommand):
    help = "Silently creates the mandatory group 'datenverwalter'"

    def handle(self, *args, **options):
        if not djcam.Group.objects.filter(name=arm.STAFF_GROUP).exists():
            djcam.Group.objects.create(name=arm.STAFF_GROUP)
