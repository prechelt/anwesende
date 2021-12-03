import typing as tg

from django.db.models import Count

import anwesende.room.models as arm



def visits_by_department_report() -> tg.List[tg.Mapping[str, str]]:
    return list(arm.Room.objects.order_by('organization', 'department')
                .values('organization', 'department')
                .annotate(rooms=Count("id", distinct=True))
                .annotate(seats=Count("seat", distinct=True))
                .annotate(visits=Count("seat__visit", distinct=True))
                )

