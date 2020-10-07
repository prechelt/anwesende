import django.db.models as djdm

FIELDLENGTH = 80

class Importstep(djdm.Model):
    """Each Importstep corresponds to one set of QR-Codes created."""
    when = djdm.DateTimeField(auto_now_add=True)  # creation timestamp
    

class Room(djdm.Model):
    #----- Options:
    class Meta:
        constraints = [
            djdm.UniqueConstraint(name='orgdeptbldgroomunique_room',
                                  fields=
                ['organization', 'department', 'building', 'room'])]
    #----- Fields:
    organization = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH
    )
    department = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH
    )
    building = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH
    )
    room = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH
    )
    seat_min = djdm.IntegerField(null=False)
    seat_max = djdm.IntegerField(null=False)
    #----- References:
    importstep = djdm.ForeignKey(   # set on create or overwrite
        to=Importstep,
        on_delete=djdm.PROTECT)


class Seat(djdm.Model):
    #----- Fields:
    number = djdm.IntegerField(null=False)
    hash = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        db_index=True,  # to map a QR code to a Room
        unique=True
    )
    #----- References:
    room = djdm.ForeignKey(
        to=Room,
        on_delete=djdm.PROTECT)
