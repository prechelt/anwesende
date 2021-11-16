"""
Excel import (for creating QR codes) and Excel export (for attenance lists).
Import also validates the proper file format.
Export also controls which groups of visitors to include.
"""
import collections
import os
import re
import tempfile
import typing as tg

import django.db.models.query as djdmq
from django.conf import settings

import anwesende.room.models as arm
import anwesende.users.models as aum
import anwesende.utils.date as aud
import anwesende.utils.excel as aue


class InvalidExcelError(ValueError):
    pass  # no additional logic is needed


def validate_excel_importfile(filename) -> None:
    # may raise InvalidExcelError
    columnsdict = aue.read_excel_as_columnsdict(filename)
    _validate_room_declarations(columnsdict)


def create_seats_from_excel(filename: str, user: aum.User) -> arm.Importstep:
    columnsdict = aue.read_excel_as_columnsdict(filename)
    _validate_room_declarations(columnsdict)
    importstep = _create_importstep(user)
    rooms, importstep.num_new_rooms, importstep.num_existing_rooms = \
        _find_or_create_rooms(columnsdict, importstep)
    seats, importstep.num_new_seats, importstep.num_existing_seats = \
        _find_or_create_seats(rooms)
    importstep.save()
    return importstep


def _validate_room_declarations(columndict: aue.Columnsdict):
    if getattr(columndict, 'has_been_validated', False): 
        return
    _validate_columnlist(columndict)
    _validate_single_department(columndict)
    _validate_dist(columndict, 'row_dist')
    _validate_dist(columndict, 'seat_dist')
    _validate_seatrange(columndict)
    columndict.has_been_validated = True  # type: ignore


def _validate_columnlist(columndict: aue.Columnsdict):
    expected = ('organization', 'department', 'building', 'room', 
                'row_dist', 'seat_dist', 'seat_last')
    found = columndict.keys()
    missing = set(expected) - set(found)
    if missing:
        _excelerror(row=1, expected=f"columns {expected}",
                    found=f"some columns are missing: {missing}")
    surprises = set(found) - set(expected)
    if surprises:
        _excelerror(row=1, expected=f"columns {expected}",
                    found=f"there are additional columns: {surprises}")


def _validate_single_department(columndict: aue.Columnsdict):
    organizations = set(columndict['organization'])
    departments = set(columndict['department'])
    if len(organizations) > 1:
        _excelerror(column='organization',
                    expected="all values are the same",
                    found=f"multiple different values: {organizations}")
    if len(departments) > 1:
        _excelerror(column='department',
                    expected="all values are the same",
                    found=f"multiple different values: {departments}")


def _validate_dist(columndict: aue.Columnsdict, colname: str) -> None:
    assert colname in ['row_dist', 'seat_dist']
    my_dists = columndict[colname]
    my_dist_format = r"\d[\.,]\d\d?"
    for index, my_dist in enumerate(my_dists):
        excel_row_number = index + 2
        try:
            if not re.fullmatch(my_dist_format, my_dist):
                format_msg = "distance value must look like '1.2' or '1,25'"
                _excelerror(row=excel_row_number, column=colname,
                            found=f"'{my_dist}': {format_msg}")
            else:
                my_dist = arm.Room.as_float(my_dist)
                if my_dist < 0.3 or my_dist > 4.0:
                    distance_msg = "distance must be in range 0.3 to 4.0 meters"
                    _excelerror(row=excel_row_number, column=colname,
                                found=f"'{my_dist}': {distance_msg}")
        except Exception as ex:
            if isinstance(ex, InvalidExcelError):
                raise ex
            else:
                _excelerror(row=excel_row_number, column=colname,
                            found=str(ex))


def _validate_seatrange(columndict: aue.Columnsdict):
    last_seats = columndict['seat_last']
    for index in range(len(last_seats)):
        excel_row_number = index + 2
        try:
            entry = last_seats[index]
            maxrow, maxseat = arm.Seat.split_seatname(entry)
            if maxrow*maxseat not in range(1, 2000):
                msg = f"{entry}: rooms must have 1 to 2000 seats, not {maxrow*maxseat}"
                _excelerror(row=excel_row_number, column='seat_last', found=msg)
        except ValueError as ex:
            _excelerror(row=excel_row_number, column='seat_last',
                        found=str(ex))


def _create_importstep(user: aum.User) -> arm.Importstep:
    result = arm.Importstep(user=user)
    result.save()
    return result


def _find_or_create_rooms(
        columnsdict: aue.Columnsdict,
        importstep: arm.Importstep) -> tg.Tuple[tg.Sequence[arm.Room], int, int]:
    _validate_room_declarations(columnsdict)
    result = []
    newN = existingN = 0
    for idx in range(len(columnsdict['room'])):
        def col(name): 
            return columnsdict[name][idx] 
        room, created = arm.Room.objects.get_or_create(
            organization=col('organization'),
            department=col('department'),
            building=col('building'),
            room=col('room'),
            defaults=dict(row_dist=arm.Room.as_float(col('row_dist')), 
                          seat_dist=arm.Room.as_float(col('seat_dist')),
                          seat_last=col('seat_last'),
                          importstep=importstep)
        )
        if created:
            newN += 1
        else:
            existingN += 1
            room.importstep = importstep
            #--- some fields can be modified by re-imports:
            room.row_dist = arm.Room.as_float(col('row_dist'))
            room.seat_dist = arm.Room.as_float(col('seat_dist'))
            room.seat_last = col('seat_last')
            room.save()
        result.append(room)
    return (result, newN, existingN)


def _find_or_create_seats(rooms: tg.Sequence[arm.Room]) \
        -> tg.Tuple[tg.Sequence[arm.Seat], int, int]:
    result = []
    newN = existingN = 0
    for room in rooms:
        maxrow, maxseat = arm.Seat.split_seatname(room.seat_last)
        for rownum in range(1, maxrow + 1):
            for seatnum in range(1, maxseat + 1):
                seat, created = arm.Seat.objects.get_or_create(
                    rownumber=rownum,
                    seatnumber=seatnum,
                    room=room,
                    defaults=dict(hash=arm.Seat.seathash(
                        room, arm.Seat.form_seatname(rownum, seatnum)))
                )
                result.append(seat)
                if created:
                    newN += 1
                else:
                    existingN += 1
    return (result, newN, existingN)


def _excelerror(row: int = None, column: str = None,
                expected: str = None, found: str = None
                ):
    assert found  # the core part, must not be left empty
    result = "Excel error: "
    if row:
        result += f"row {row}  "
    if column:
        result += f"column '{column}':"
    if row or column:
        result += '\n'
    if expected:
        result += f"EXPECTED: {expected}.\n"
    if expected:
        result += "FOUND: "
    result += found
    raise InvalidExcelError(result)


VGroupRow = collections.namedtuple('VGroupRow',  # noqa
    'familyname givenname email phone street_and_nr zipcode town '
    'status_3g '
    'cookie '
    'distance '
    'when from_time to_time '
    'organization department building room seat ')


Visits = tg.List[tg.Optional[arm.Visit]]


Expl = collections.namedtuple('Expl', ("Erklaerung", ))


explanations = [
    Expl("Jede Zeile im Tabellenblatt 'Daten' ist ein Besuch einer Person."),
    Expl("Die Spalten beschreiben die Person, dann die Zeit, dann den Ort."),
    Expl("" if settings.USE_EMAIL_FIELD
         else "(Spalte 'email' ist abgeschaltet.)"),
    Expl("Leere Zeilen trennen Gruppen von Personen. Die Mitglieder einer Gruppe "
         "sind einander laut ihren Angaben mindestens "
         f"{settings.MIN_OVERLAP_MINUTES} Minuten im gleichen Raum begegnet."),
    Expl(""),
    Expl("**cookie**: Die Daten enthalten meist viele Personen mehrfach."),
    Expl("Um diese Duplikate zu überblicken, kann man nach Spalte "
         "'cookie' sortieren."),
    Expl("Das selbe Cookie steht meist für die selbe Person."),
    Expl("Eine Person hat mehrere verschiedene Cookies, wenn sie "
         "das Cookie gelöscht oder mehrere Geräte oder Browser benutzt hat."),
    Expl("Zwei Personen können das selbe Cookie haben, wenn eine Person "
         "ihr Gerät verleiht."),
    Expl("Wenn viele Personen mit fragwürdigen Angaben das selbe Cookie "
         "haben, sind die Daten vielleicht Fantasie-Angaben."),
    Expl("" if settings.COOKIE_WITH_RANDOMSTRING
         else "(Die Funktion ist abgeschaltet)"),
    Expl("**when**: Spalte 'when' enthält den Zeitpunkt der Meldung und "),
    Expl("'from' und 'to' die vom Besucher manuell eingegebenen Werte "
         "für den Zeitraum."),
    Expl("**distance**: Abstand vom Sitzplatz der infizierten Person"),
    Expl(""),
]


def collect_visitgroups(primary_visits: djdmq.QuerySet
                        ) -> Visits:
    result = []
    visit_pks_seen = set()  # all contacts of primary visits
    primary_visit_pks_seen = set()  # only primary visits
    primary_visits = list(primary_visits)  # retrieve them only once
    primary_visit_pks_all = { pvisit.pk for pvisit in primary_visits }
    for pvisit in primary_visits:
        pvisit.distance = pvisit.seat.distance_in_m(pvisit.seat)  # add attr
        if pvisit.pk not in primary_visit_pks_seen:
            primary_visit_pks_seen.add(pvisit.pk)
        else:
            continue  # pvisit was already mentioned in a previous group
        visit_pks_seen.add(pvisit.pk)
        group = pvisit.get_overlapping_visits()
        for visit in group:
            visit.distance = visit.seat.distance_in_m(pvisit.seat)  # add attr
            must_not_be_suppressed = (visit.pk == pvisit.pk)
            is_new = visit.pk not in visit_pks_seen
            if is_new or must_not_be_suppressed:
                result.append(visit)
            if visit.pk in primary_visit_pks_all:  # make no separate group for visit.pk
                primary_visit_pks_seen.add(visit.pk)  
        result.append(None)  # empty row as separator
    if len(result) > 0:
        del result[-1]  # remove trailing empty row
    return result


def get_excel_download(visits: Visits) -> bytes:
    rows = _as_vgrouprows(visits)
    rowslists = dict(Daten=rows, Erklaerungen=explanations)
    with tempfile.NamedTemporaryFile(prefix="export_", suffix=".xlsx",
                                     delete=False) as fh:
        filename = fh.name  # file is deleted in 'finally' clause
    try:
        aue.write_excel_from_rowslists(filename, rowslists,  # type: ignore
                                       indexcolumn=True)
        with open(filename, 'rb') as file:
            excelbytes = file.read()  # slurp. Won't be very large.
    finally:
        os.unlink(filename)
    return excelbytes


def _as_vgrouprows(visits) -> tg.List[tg.Optional[VGroupRow]]:
    vgrouprows: tg.List[tg.Optional[VGroupRow]] = []
    v: arm.Visit
    for idx, v in enumerate(visits):
        if v is None:
            row = None
        else:
            distance = getattr(v, 'distance', None)
            distance = "%5.1fm" % v.distance if distance is not None else "?"
            row = VGroupRow(
                v.familyname, v.givenname, v.email, v.phone,
                v.street_and_number, v.zipcode, v.town, 
                v.status_3g_txt,
                v.cookie, distance,  # type: ignore
                aud.dtstring(v.submission_dt, time=True), 
                aud.dtstring(v.present_from_dt, date=False, time=True),
                aud.dtstring(v.present_to_dt, date=False, time=True),
                v.seat.room.organization, v.seat.room.department, 
                v.seat.room.building, v.seat.room.room,
                v.seat.seatname)
        vgrouprows.append(row)
    return vgrouprows
