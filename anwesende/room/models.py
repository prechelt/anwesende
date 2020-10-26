import datetime as dt
import hashlib

import django.core.validators as djcv
import django.db.models as djdm
import django.db.models.query as djdmq
import strgen
from django.conf import settings
from django.db.models.query import F

import anwesende.users.models as aum
import anwesende.utils.date as aud

FIELDLENGTH = 80
STAFF_GROUP = "datenverwalter"


class Importstep(djdm.Model):
    """Each Importstep corresponds to one set of QR-Codes created."""
    when = djdm.DateTimeField(auto_now_add=True)  # creation timestamp
    user = djdm.ForeignKey(null=False, to=aum.User, on_delete=djdm.PROTECT)
    num_new_rooms = djdm.IntegerField(null=False, default=0)
    num_new_seats = djdm.IntegerField(null=False, default=0)
    num_existing_rooms = djdm.IntegerField(null=False, default=0)
    num_existing_seats = djdm.IntegerField(null=False, default=0)


class Room(djdm.Model):
    """
    One room (that has seats) in one building of one department 
    of one organization.
    """
    # ----- Options:
    class Meta:
        constraints = [djdm.UniqueConstraint(
            name='orgdeptbldgroomunique_room',
            fields=['organization', 'department', 'building', 'room'])]
    # ----- Fields:
    organization = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        db_index=True,
    )
    department = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        db_index=True,
    )
    building = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        db_index=True,
    )
    room = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        db_index=True,
    )
    seat_min = djdm.IntegerField(null=False)
    seat_max = djdm.IntegerField(null=False)
    # ----- References:
    importstep = djdm.ForeignKey(   # set on create or overwrite
        to=Importstep,
        on_delete=djdm.PROTECT)
    
    def __str__(self):
        return f"{self.organization}|{self.department}|{self.building}|{self.room}"

    def __repr__(self):
        return self.__str__()
    

class Seat(djdm.Model):
    """
    One seat in a Room. Each QR code refers to one Seat.
    """
    # ----- Fields:
    number = djdm.IntegerField(null=False)
    hash = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        db_index=True,  # to map a QR code to a Room
        unique=True
    )
    #   ----- References:
    room = djdm.ForeignKey(
        to=Room,
        on_delete=djdm.PROTECT)

    @classmethod
    def by_hash(cls, hash: str):
        return cls.objects.select_related('room').get(hash=hash)
    
    @classmethod
    def get_dummy_seat(cls) -> 'Seat':
        all_dummyseats = cls.objects.filter(room__organization=settings.DUMMY_ORG)
        num_dummyseats = all_dummyseats.count()
        if num_dummyseats == 0:
            return cls._make_dummyseat(settings.DUMMY_ORG)
        return all_dummyseats.select_related('room__importstep').get()

    @classmethod
    def _make_dummyseat(cls, dummyorg: str) -> 'Seat':
        DUMMYSEAT_NUM = 1
        user = aum.User.objects.create(name="dummy", username="dummy", 
                                       first_name="D.", last_name="dummy", email="",
                                       is_active=False)
        step = Importstep.objects.create(num_new_rooms=1, num_new_seats=1,
                                         num_existing_rooms=0, num_existing_seats=0,
                                         user=user)
        room = Room.objects.create(organization=dummyorg, department="dummydept", 
                                   building="dummybldg", 
                                   room="dummyroom", seat_max=1, seat_min=1,
                                   importstep=step)
        dummyseat = cls.objects.create(room=room, number=DUMMYSEAT_NUM,
                                       hash=cls.seathash(room, DUMMYSEAT_NUM))
        return dummyseat
    
    @classmethod
    def seathash(cls, room: Room, seatnumber: int) -> str:
        make_unguessable = settings.SEAT_KEY
        seat_id = (f"{room.organization}|{room.department}|{room.building}|"
                   f"{room.room}|{seatnumber}|{make_unguessable}")
        return hashlib.sha256(seat_id.encode()).hexdigest()[:10]

    def __str__(self):
        return f"{self.room.room}|{self.number}|{self.hash}"

    def __repr__(self):
        return self.__str__()


class Visit(djdm.Model):
    """
    A record of one period of presence of one person in a Room 
    (precisely: at a seat).
    There is no notion of person, only the fields in this record that
    describe a person. 
    """
    # ----- Fields:
    givenname = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        db_index=True,
        verbose_name="Vorname / Given name",
        help_text="Rufname / the firstname by which you are commonly known",
    )
    familyname = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        db_index=True,
        verbose_name="Familienname / Family name",
        help_text="Wie im Ausweis angegeben / as shown in your passport",
    )
    street_and_number = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        db_index=True,
        verbose_name="Straße und Hausnummer / Street and number",
        help_text="Wohnadresse für diese Woche / This week's living address",
    )
    zipcode = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        verbose_name="Postleitzahl / Postal code",
        db_index=True,
        validators=[djcv.RegexValidator(regex=r"^\d{5}$",  # noqa
                message="5 Ziffern bitte / 5 digits, please")]
    )
    town = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        db_index=True,
        verbose_name="Ort / Town",
    )
    phone = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        db_index=True,
        verbose_name="Mobilfunknummer / Mobile phone number",
        help_text="Mit Ländervorwahl, z.B. +49 151... in Deutschland / "
                  "With country code, starting with '+'",
        validators=[djcv.RegexValidator(regex=r"^\+\d\d[\d /-]+$",
                message="Falsches Format für eine Telefonnummer / "
                        "Wrong format as a phone number")],
    )
    email = djdm.EmailField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        db_index=True,
        verbose_name="Emailadresse / Email address",
        help_text="Bitte immer die gleiche benutzen! / Please use the same one each time",
    )
    present_from_dt = djdm.DateTimeField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        db_index=True,
    )
    present_to_dt = djdm.DateTimeField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        db_index=True,
    )
    submission_dt = djdm.DateTimeField(auto_now_add=True)
    cookie = djdm.TextField(blank=False, null=False, max_length=15,  # noqa
        verbose_name="random string, used as pseudo-id",)
    # ----- References:
    seat = djdm.ForeignKey(
        to=Seat,
        on_delete=djdm.PROTECT)

    def __str__(self):
        return (f"{self.familyname}|{self.email}|"
                f"{aud.dtstring(self.submission_dt, time=True)}|"
                f"{aud.dtstring(self.present_from_dt, date=False, time=True)}-"
                f"{aud.dtstring(self.present_to_dt, date=False, time=True)}")

    def __repr__(self):
        return self.__str__()

    def get_overlapping_visits(self) -> djdmq.QuerySet:
        """
        All visits that overlap self by at least MIN_OVERLAP_MINUTES.
        A visit overlaps itself if it is long enough;
        result is empty otherwise.
        """
        delta = dt.timedelta(minutes=settings.MIN_OVERLAP_MINUTES)
        # There are four non-disjoint cases:
        # 1) other visit is long enough and included in self
        # 2) other includes self that is long enough 
        # 3) other extends enough into self from before self
        # 4) other begins early enough within self (and continues after self)
        # We return other visits that belong to either of these cases.
        # The filter param (not arg value!) represents the other visit.
        self_long_enough = (self.present_to_dt - self.present_from_dt) >= delta
        if not self_long_enough:
            return self.__class__.objects.none()  # overlapping-enough visits impossible
        # we now rely on self being long enough:
        base_qs = self.__class__.objects.filter(seat__room=self.seat.room)
        other_included_in_self = (base_qs
                .filter(present_to_dt__gte=F('present_from_dt') + delta)
                .filter(present_from_dt__gte=self.present_from_dt)
                .filter(present_to_dt__lte=self.present_to_dt))
        other_includes_self = (base_qs
                .filter(present_from_dt__lte=self.present_from_dt)
                .filter(present_to_dt__gte=self.present_to_dt))
        other_extends_into_self = (base_qs
                .filter(present_from_dt__lte=self.present_from_dt)
                .filter(present_to_dt__gte=self.present_from_dt + delta))
        other_begins_within_self = (base_qs
                .filter(present_from_dt__gte=self.present_from_dt)
                .filter(present_from_dt__lte=self.present_to_dt - delta)
                .filter(present_to_dt__gte=self.present_to_dt))
        all4cases = (other_included_in_self | other_includes_self
                     | other_extends_into_self | other_begins_within_self)
        return all4cases.distinct().order_by('submission_dt')

    @classmethod
    def make_cookie(cls) -> str:
        return strgen.StringGenerator('[a-z]{10}').render()
