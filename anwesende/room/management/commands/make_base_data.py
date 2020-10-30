import django.contrib.auth.models as djcam
import django.core.management.base as djcmb

import anwesende.room.models as arm
import anwesende.users.models as aum


class Command(djcmb.BaseCommand):
    help = "Silently creates group 'datenverwalter'"

    def handle(self, *args, **options):
        if not djcam.Group.objects.filter(name=aum.User.STAFF_GROUP).exists():
            djcam.Group.objects.create(name=aum.User.STAFF_GROUP)
        arm.Seat.get_dummy_seat()  # create now to make it nicely the first one
