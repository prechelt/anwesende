import dataclasses
import datetime as dt
import typing as tg

from django.conf import settings
import django.db.models as djdm
from django.db.models import Count
import django.utils.timezone as djut

import anwesende.room.models as arm
import anwesende.utils.lookup  # noqa,  registers lookup


@dataclasses.dataclass
class Weekreport:
    week_from: dt.datetime
    week_to: dt.datetime
    organizationsN: int
    departmentsN: int
    buildingsN: int
    roomsN: int
    visitsN: int
    visitorsN: int
    visits_per_visitor: float


def visits_by_department_report() -> tg.List[tg.Mapping[str, str]]:
    return list(arm.Room.objects.order_by('organization', 'department')
                .values('organization', 'department')
                .annotate(rooms=Count("id", distinct=True))
                .annotate(seats=Count("seat", distinct=True))
                .annotate(visits=Count("seat__visit", distinct=True))
                )


def visitors_by_week_report(roomdescriptor: str) -> tg.List[Weekreport]:
    visit_qs = arm.Visit.objects.filter(seat__room__descriptor__ilike=roomdescriptor)
    weeksN = int(settings.DATA_RETENTION_DAYS / 7)
    oneweek = dt.timedelta(days=7)
    now = djut.localtime()
    result = []
    for weekI in range(weeksN):
        starttime = now - oneweek * (weeksN - weekI)
        endtime = starttime + oneweek
        result.append(weekreport_row(visit_qs, starttime, endtime))
    return result


def weekreport_row(base_qs: djdm.QuerySet, 
                   starttime: dt.datetime, endtime: dt.datetime) -> Weekreport:
    myvisits_qs = base_qs.filter(present_from_dt__gte=starttime,
                                 present_from_dt__lte=endtime)
    def count(attr: str) -> int:
        return _get_count(myvisits_qs, attr)
    wr = Weekreport(
        week_from=starttime, week_to=endtime,
        organizationsN=count('organization'), departmentsN=count('department'),
        buildingsN=count('building'), roomsN=count('room'),
        visitsN=myvisits_qs.count(), visitorsN=_get_peoplecount(myvisits_qs),
        visits_per_visitor=None
    )
    wr.visits_per_visitor = wr.visitsN / wr.visitorsN if wr.visitorsN > 0 else 0.0
    return wr



def _get_count(qs: djdm.QuerySet, attr) -> int:
    attrs = ['organization', 'department', 'building', 'room']
    selectors = ['seat__room__organization', 'seat__room__department', 
                 'seat__room__building', 'seat__room__room']
    pos = attrs.index(attr)
    count = qs.order_by(*selectors[:pos+1]).distinct(*selectors[:pos+1]).count()
    # print("get_count", attr, selectors[:pos+1])
    return count


def _get_peoplecount(qs: djdm.QuerySet) -> int:
    field = 'email' if settings.USE_EMAIL_FIELD else 'phone'
    return qs.order_by(field).distinct(field).count()