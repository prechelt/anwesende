import datetime as dt
import hashlib
import math
import re
import typing as tg

import django.core.validators as djcv
import django.db.models as djdm
import django.db.models.query as djdmq
import django.utils.timezone as djut
import strgen
from django.conf import settings
from django.db.models import Count, Max
from django.db.models.query import F

import anwesende.users.models as aum
import anwesende.utils.date as aud
import anwesende.utils.validators as auv

FIELDLENGTH = 80


class Importstep(djdm.Model):
    """Each Importstep corresponds to one set of QR-Codes created."""
    when = djdm.DateTimeField(auto_now_add=True)  # creation timestamp
    user = djdm.ForeignKey(null=False, to=aum.User, on_delete=djdm.PROTECT)
    num_new_rooms = djdm.IntegerField(null=False, default=0)
    num_new_seats = djdm.IntegerField(null=False, default=0)
    num_existing_rooms = djdm.IntegerField(null=False, default=0)
    num_existing_seats = djdm.IntegerField(null=False, default=0)
    
    def __str__(self):
        return (f"{self.num_new_rooms}+{self.num_new_seats} imported "
                + f"by {self.user.username}, "        
                + f"{self.num_existing_rooms}+{self.num_existing_seats} pre-existing")

    @classmethod
    def displayable_importsteps(cls, interval: dt.timedelta) -> tg.List['Importstep']:
        steps = list(cls.objects.filter(
            when__gt=djut.localtime() - interval) \
            .annotate(organization=Max('room__organization')) \
            .annotate(department=Max('room__department')) \
            .annotate(num_qrcodes=Count('room__seat')) \
            .order_by('when'))
        for step in steps:
            step.num_qrcodes_moved = (step.num_new_seats +   # type: ignore
                                      step.num_existing_seats - 
                                      step.num_qrcodes)
        return steps

class Room(djdm.Model):
    """
    One room (that has seats) in one building of one department 
    of one organization.
    """
    DEFAULT_SEATDISTANCE_in_m = 1.4  # how far seats are assumed to be spaced apart
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
    descriptor = djdm.CharField(null=False, max_length=4*FIELDLENGTH,
        help_text= "a materialization: 'organization;department;building;room' for search",
    )
    seat_last = djdm.CharField(blank=False, null=False, max_length=FIELDLENGTH,
            help_text="e.g. 'r2s7' for row 2, seat 7 (14 seats total in the room)")
    row_dist = djdm.FloatField(blank=False, null=False, 
            help_text="smallest distance between people in two adjacent rows in meters")
    seat_dist = djdm.FloatField(blank=False, null=False, 
            help_text="smallest distance between people in two adjacent seats in meters")

    # ----- References:
    importstep = djdm.ForeignKey(   # set on create or overwrite
        to=Importstep,
        on_delete=djdm.PROTECT)
    
    def __str__(self):
        return f"{self.organization}|{self.department}|{self.building}|{self.room}"

    def __repr__(self):
        return self.__str__()
    
    @classmethod
    def as_float(cls, dist_string: str) -> float:
        return float(dist_string.replace(',', '.'))  # ensure decimal point

    def current_unique_visitors_qs(self) -> djdmq.QuerySet:
        now = djut.localtime()
        allvisits = Visit.objects.filter(seat__room=self,
            present_from_dt__lte=now, present_to_dt__gte=now)
        return allvisits.order_by('phone', '-submission_dt') \
            .distinct('phone')  # beware of not USE_EMAIL_FIELD

    def current_unique_visitorsN(self) -> int:
        return self.current_unique_visitors_qs().count()

    def save(self, *args, **kwargs):
        """Add 'descriptor' materialization behavior."""
        self.descriptor = "%s;%s;%s;%s" % (
            self.organization, self.department, self.building, self.room)
        super().save(*args, **kwargs)


class Seat(djdm.Model):
    """
    One seat in a Room. Each QR code refers to one Seat.
    """
    # ----- Fields:
    seatnumber = djdm.IntegerField(null=False)
    rownumber = djdm.IntegerField(null=False)
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
    def exists(cls, hashvalue):
        return cls.objects.filter(hash=hashvalue).exists()

    def distance_in_m(self, otherseat: 'Seat') -> float:
        # Seats are assumed to be on an exact cartesian grid, 
        # which is a slightly optimistic assumption.
        rowdiff = self.rownumber - otherseat.rownumber
        seatdiff = self.seatnumber - otherseat.seatnumber
        rowdist_m = rowdiff * self.room.row_dist
        seatdist_m = seatdiff * self.room.seat_dist
        return math.sqrt(rowdist_m**2 + seatdist_m**2)

    @classmethod
    def get_dummy_seat(cls) -> 'Seat':
        all_dummyseats = cls.objects.filter(room__organization=settings.DUMMY_ORG)
        num_dummyseats = all_dummyseats.count()
        if num_dummyseats == 0:
            return cls._make_dummyseat(settings.DUMMY_ORG)
        return all_dummyseats.select_related('room__importstep').get()

    @classmethod
    def _make_dummyseat(cls, dummyorg: str) -> 'Seat':
        DUMMYSEAT_NAME = cls.form_seatname(1, 1)  # "r1s1"
        DUMMYSEAT_ROW_DIST = 1.1
        DUMMYSEAT_SEAT_DIST = 0.6
        rownumber, seatnumber = cls.split_seatname(DUMMYSEAT_NAME)
        user = aum.User.objects.create(name="dummy", username="dummy", 
                                       first_name="D.", last_name="dummy", email="",
                                       is_active=False)
        step = Importstep.objects.create(num_new_rooms=1, num_new_seats=1,
                                         num_existing_rooms=0, num_existing_seats=0,
                                         user=user)
        room = Room.objects.create(organization=dummyorg, department="dummydept", 
                                   building="dummybldg", 
                                   room="dummyroom",
                                   row_dist=DUMMYSEAT_ROW_DIST, 
                                   seat_dist=DUMMYSEAT_SEAT_DIST,
                                   seat_last=cls.form_seatname(1, 1),
                                   importstep=step)
        dummyseat = cls.objects.create(room=room, 
                rownumber=rownumber, seatnumber=seatnumber,
                hash=cls.seathash(room, DUMMYSEAT_NAME))
        return dummyseat
    
    @classmethod
    def seathash(cls, room: Room, seatname: str) -> str:
        make_unguessable = settings.SEAT_KEY
        seat_id = (f"{room.organization}|{room.department}|{room.building}|"
                   f"{room.room}|{seatname}|{make_unguessable}")
        return hashlib.sha256(seat_id.encode()).hexdigest()[:10]

    @property
    def seatname(self) -> str:
        return f"r{self.rownumber}s{self.seatnumber}"
    
    @classmethod
    def form_seatname(cls, rownum: int, seatnum: int) -> str:
        assert rownum > 0 and seatnum > 0
        return f"r{rownum}s{seatnum}"

    @classmethod
    def split_seatname(cls, seatname: str) -> tg.Tuple[int, int]:
        mm = re.fullmatch(r"r(\d+)s(\d+)", seatname)
        if not mm:
            msg1 = f"Falsche Sitznummber '{seatname}': "
            msg2 = "Richtiges Format ist 'r1s3' für Reihe 1, Sitz 3 etc."
            raise ValueError(msg1 + msg2)
        return (int(mm.group(1)), int(mm.group(2)))

    def __str__(self):
        return f"{self.room.room}|{self.seatname}|{self.hash}"

    def __repr__(self):
        return self.__str__()

# Status according to §2 SchAusnahmV
# https://www.gesetze-im-internet.de/schausnahmv/
G_IMPFT = 22
G_NESEN = 24
G_TESTET = 26
G_OTHER = 87
G_UNKNOWN = 88

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
        validators=[auv.validate_isprintable],
        verbose_name="Vorname / Given name",
        help_text="Rufname / the firstname by which you are commonly known",
    )
    familyname = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        db_index=True,
        validators=[auv.validate_isprintable],
        verbose_name="Familienname / Family name",
        help_text="Wie im Ausweis angegeben / as shown in your passport (Latin script)",
    )
    street_and_number = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        db_index=True,
        validators=[auv.validate_isprintable],
        verbose_name="Straße und Hausnummer / Street and number",
        help_text="Wohnadresse für diese Woche / This week's living address",
    )
    zipcode = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        verbose_name="Postleitzahl / Postal code",
        db_index=True,
        validators=[djcv.RegexValidator(regex=r"^\d{5}$",  # noqa
                message="5 Ziffern bitte / 5 digits, please", 
                flags=re.ASCII)]
    )
    town = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        db_index=True,
        validators=[auv.validate_isprintable],
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
                        "Wrong format as a phone number",
                flags=re.ASCII)],
    )
    email = djdm.EmailField(
        blank=True, null=False,
        max_length=FIELDLENGTH,
        db_index=True,
        verbose_name="Emailadresse / Email address",
        help_text="Bitte immer die gleiche benutzen! / Please use the same one each time",
    )
    status_3g_basechoices = [
        (G_IMPFT, "vollständig geimpft / fully vaccinated"),
        (G_NESEN, "genesen / recovered"),
        (G_TESTET, "getestet / tested"),
        (G_OTHER, "weder noch / none of the above"),
    ]
    status_3g_modelchoices = status_3g_basechoices + [(G_UNKNOWN, "unbekannt")]
    status_3g_formchoices = [(None, "---")] + status_3g_basechoices    # type: ignore
    status_3g_gesundheitsamt = [  # for status_3g_txt
        (G_IMPFT, "vollständig geimpft"),
        (G_NESEN, "genesen"),
        (G_TESTET, "getestet"),
        (G_OTHER, "weder noch"),
        (G_UNKNOWN, "unbekannt"),
    ]
    status_3g = djdm.IntegerField(default=G_UNKNOWN,
        blank=False, null=False,
        choices = status_3g_modelchoices,
        verbose_name="3G-Status gemäß §2 SchAusnahmV / vaccination status",
        help_text="Siehe <a href='https://www.gesetze-im-internet.de/schausnahmv/__2.html'>die Verordnung</a> / (see regulation, in german only)",
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

    @property
    def status_3g_txt(self) -> str:
        for key, val in self.status_3g_gesundheitsamt:
            if self.status_3g == key:
                return val
        return "???"

    def get_overlapping_visits(self) -> djdmq.QuerySet:
        """
        All visits that overlap self by at least MIN_OVERLAP_MINUTES.
        A visit overlaps itself if it is long enough;
        result is empty otherwise.
        """
        base_qs = self.__class__.objects.filter(seat__room=self.seat.room)
        from_, to_ = (self.present_from_dt, self.present_to_dt)
        return self._overlapping_visits_qs(base_qs, from_, to_)

    @classmethod
    def visits_in_timerange_qs(cls, from_: dt.datetime, to_: dt.datetime
                              ) -> djdm.QuerySet:
        return cls._overlapping_visits_qs(cls.objects.all(), from_, to_)

    @classmethod
    def _overlapping_visits_qs(cls, base_qs: djdm.QuerySet, 
                               from_: dt.datetime, to_: dt.datetime) -> djdm.QuerySet:
        """
        All visits that overlap the timerange by at least MIN_OVERLAP_MINUTES.
        """
        delta = dt.timedelta(minutes=settings.MIN_OVERLAP_MINUTES)
        # There are four non-disjoint cases:
        # 1) other visit is long enough and included in range
        # 2) other includes range that is long enough 
        # 3) other extends enough into range from before range
        # 4) other begins early enough within range (and continues after range)
        # We return visits that belong to either of these cases.
        # The filter param (not arg value!) represents the other visit.
        range_is_long_enough = (to_ - from_) >= delta
        if not range_is_long_enough:
            return cls.objects.none()  # overlapping-enough visits impossible
        # we now rely on self being long enough:
        other_included_in_self = (base_qs
                .filter(present_to_dt__gte=F('present_from_dt') + delta)
                .filter(present_from_dt__gte=from_)
                .filter(present_to_dt__lte=to_))
        other_includes_self = (base_qs
                .filter(present_from_dt__lte=from_)
                .filter(present_to_dt__gte=to_))
        other_extends_into_self = (base_qs
                .filter(present_from_dt__lte=from_)
                .filter(present_to_dt__gte=from_ + delta))
        other_begins_within_self = (base_qs
                .filter(present_from_dt__gte=from_)
                .filter(present_from_dt__lte=to_ - delta)
                .filter(present_to_dt__gte=to_))
        all4cases = (other_included_in_self | other_includes_self
                     | other_extends_into_self | other_begins_within_self)
        return all4cases.distinct().order_by('submission_dt')

    @classmethod
    def make_cookie(cls) -> str:
        if settings.COOKIE_WITH_RANDOMSTRING:
            return strgen.StringGenerator('[a-z]{10}').render()
        else:
            return "none"
