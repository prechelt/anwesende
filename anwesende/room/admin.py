import django.contrib.admin as djca

import anwesende.room.models as arm


@djca.register(arm.Importstep)
class ImportstepAdmin(djca.ModelAdmin):
    pass

@djca.register(arm.Room)
class RoomAdmin(djca.ModelAdmin):
    pass

@djca.register(arm.Seat)
class SeatAdmin(djca.ModelAdmin):
    pass

@djca.register(arm.Visit)
class VisitAdmin(djca.ModelAdmin):
    pass
