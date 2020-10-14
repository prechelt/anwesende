import datetime as dt
import re

import django.core.exceptions as djce
import django.core.validators as djcv
import django.db.models as djdm
import django.utils.timezone as djut

import anwesende.utils.date as aud

FIELDLENGTH = 80

class Importstep(djdm.Model):
    """Each Importstep corresponds to one set of QR-Codes created."""
    when = djdm.DateTimeField(auto_now_add=True)  # creation timestamp
    randomkey = djdm.CharField(null=False, max_length=FIELDLENGTH)
    

class Room(djdm.Model):
    """
    One room (that has seats) in one building of one department 
    of one organization.
    """
    #----- Options:
    class Meta:
        constraints = [
            djdm.UniqueConstraint(name='orgdeptbldgroomunique_room',
                                  fields=
                ['organization', 'department', 'building', 'room'])]
    #----- Fields:
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
    #----- References:
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

    @classmethod
    def by_hash(cls, hash:str):
        return cls.objects.get(hash=hash)

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
        verbose_name = "Familienname / Family name",
        help_text = "Wie im Ausweis angegeben / as shown in your passport",
    )
    street_and_number = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        db_index=True,
        verbose_name = "Straße und Hausnummer / Street and number",
        help_text = "",
    )
    zipcode = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        verbose_name = "Postleitzahl / Postal code",
        db_index=True,
        help_text = "",
        validators = [djcv.RegexValidator(regex=r"^\d{5}$",
                message="5 Ziffern bitte / 5 digits, please")]
    )
    town = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        db_index=True,
        verbose_name = "Ort / Town",
        help_text = "",
    )
    phone = djdm.CharField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        db_index=True,
        verbose_name = "Mobilfunknummer / Mobile phone number",
        help_text = "Mit Ländervorwahl, z.B. +49 151 ... in Deutschland / " +
                       "With country code, starting with '+'",
        validators=[djcv.RegexValidator(regex=r"^\+\d\d[\d /-]+$",
                message= "Falsches Format für eine Telefonnummer" +
                         "Wrong format as a phone number")],
    )
    email = djdm.EmailField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        db_index=True,
        verbose_name = "Emailadresse / Email address",
        help_text = "Bitte immer die gleiche benutzen! / Please use the same one each time",
    )
    submission_dt = djdm.DateTimeField(
        blank=False, null=False,
        max_length=FIELDLENGTH,
        verbose_name = "Anmeldungszeit / Submission time",
        help_text = "",
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
    # ----- References:
    seat = djdm.ForeignKey(
        to=Seat,
        on_delete=djdm.PROTECT)

    def __str__(self):
        return (f"{self.familyname}|{self.email}|"
                f"{aud.dtstring(self.submission_dt, time=True)}")

    def __repr__(self):
        return self.__str__()

