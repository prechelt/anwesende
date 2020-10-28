import datetime as dt
import logging

import django.core.management.base as djcmb
import django.utils.timezone as djut
from django.conf import settings

import anwesende.room.models as arm
import anwesende.utils.date as aud


class Command(djcmb.BaseCommand):
    help = "Deletes all Visits older than settings.DATA_RETENTION_DAYS."

    def handle(self, *args, **options):
        horizon = djut.now() - dt.timedelta(days=settings.DATA_RETENTION_DAYS)
        oldvisits = arm.Visit.objects.filter(submission_dt__lt=horizon)
        howmany_deleted = oldvisits.count()
        howmany_exist = arm.Visit.objects.count()
        msg = "delete_outdated_data: deleting %d (of %d) visit entries before %s" % \
              (howmany_deleted, howmany_exist, aud.dtstring(horizon))
        logging.info(msg)
        oldvisits.delete()
