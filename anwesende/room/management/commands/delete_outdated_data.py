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
        horizon = djut.localtime() - dt.timedelta(days=settings.DATA_RETENTION_DAYS)
        oldvisits = arm.Visit.objects.filter(submission_dt__lt=horizon)
        howmany_deleted = oldvisits.count()
        howmany_exist = arm.Visit.objects.count()
        msg = "delete_outdated_data: deleting %d visit entries before %s (of %d existing)" % \
              (howmany_deleted, aud.dtstring(horizon), howmany_exist)
        logging.info(msg)
        oldvisits.delete()
