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
        #--- deleted data older than retention time:
        horizon = djut.localtime() - dt.timedelta(days=settings.DATA_RETENTION_DAYS)
        oldvisits = arm.Visit.objects.filter(submission_dt__lt=horizon)
        howmany_deleted = oldvisits.count()
        howmany_exist = arm.Visit.objects.count()
        msg = "delete_outdated_data: deleting %d visit entries before %s (of %d existing)" % \
              (howmany_deleted, aud.dtstring(horizon), howmany_exist)
        logging.info(msg)
        oldvisits.delete()
        #--- deleted status_3g field in data older than status_3g retention time:
        if not settings.USE_STATUS_3G_FIELD or \
           settings.DATA_RETENTION_DAYS_STATUS_3G >= settings.DATA_RETENTION_DAYS:
            return  # nothing else to do 
        horizon_3g = djut.localtime() - dt.timedelta(days=settings.DATA_RETENTION_DAYS_STATUS_3G)
        youngvisits = arm.Visit.objects.filter(submission_dt__lt=horizon_3g)
        howmany_cleaned = youngvisits.count()
        howmany_exist = arm.Visit.objects.count()
        msg = "delete_outdated_data: cleansing %d status_3g values before %s (of %d existing)" % \
              (howmany_cleaned, aud.dtstring(horizon_3g, time=True), howmany_exist)
        logging.info(msg)
        youngvisits.update(status_3g=arm.G_UNKNOWN)
