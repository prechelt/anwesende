from collections import OrderedDict
import hashlib
import typing as tg

from django.conf import settings

import anwesende.room.models as arm
import anwesende.utils.excel as aue

class InvalidExcelError(ValueError):
    pass  # no additional logic is needed


def excelerror(row:int=None, column:str=None, 
               expected:str=None, found:str=None
               ) -> str:
    assert found  # the core part, must not be left empty
    result = "Excel error: "
    if row:
        result += f"row {row}  "
    if column:
        result += f"column '{column}'"
    if row or column:
        result += '\n'
    if expected:
        result += f"EXPECTED: {expected}\n"
    if expected:
        result += "FOUND: "
    result += found
    raise InvalidExcelError(result)


def seathash(room: arm.Room, seatnumber: int):
    seat_id = (f"{room.organization}|{room.department}|{room.building}|" +
               f"{room.room}|{seatnumber}|{settings.SECRET_KEY}")
    return hashlib.sha256(seat_id.encode()).hexdigest()[:10]

    
def create_seats_from_excel(filename) -> OrderedDict:
    columnsdict = aue.read_excel_as_columnsdict(filename)
    _validate_room_declarations(columnsdict)
    importstep = _create_importstep()
    rooms, new_roomsN, existing_roomsN = \
            _find_or_create_rooms(columnsdict, importstep)
    seats, new_seatsN, existing_seatsN = _find_or_create_seats(rooms)
    return OrderedDict(number_of_new_rooms=new_roomsN,
                       number_of_existing_rooms=existing_roomsN,
                       number_of_new_seats=new_seatsN,
                       number_of_existing_seats=existing_seatsN,
                       importstep=importstep)


def _validate_room_declarations(columndict: aue.Columnsdict):
    if getattr(columndict, 'has_been_validated', False): return
    _validate_columnlist(columndict)
    _validate_single_department(columndict)
    _validate_seatrange(columndict)
    columndict.has_been_validated = True

def _validate_columnlist(columndict: aue.Columnsdict):
    expected = ('organization', 'department', 'building', 'room',
                'seat_min', 'seat_max')
    found = columndict.keys()
    missing = set(expected) - set(found)
    if missing:
        excelerror(row=1, expected=f"columns {expected}",
                   found=f"some columns are missing: {missing}")
    surprises = set(found) - set(expected)
    if surprises:
        excelerror(row=1, expected=f"columns {expected}",
                   found=f"there are additional columns: {surprises}")


def _validate_single_department(columndict: aue.Columnsdict):
    organizations = set(columndict['organization'])
    departments = set(columndict['department'])
    if len(organizations) > 1:
        excelerror(column='organization', 
                   expected="all values are the same",
                   found=f"multiple different values: {organizations}")
    if len(departments) > 1:
        excelerror(column='department', 
                   expected="all values are the same",
                   found=f"multiple different values: {departments}")


def _validate_seatrange(columndict: aue.Columnsdict):
    mins = columndict['seat_min']
    maxs = columndict['seat_max']
    for index in range(len(columndict['seat_min'])):
        excel_row_number = index + 2
        try:
            _min = int(mins[index])
        except ValueError:
            excelerror(row=excel_row_number, column='seat_min',
                       found=f"Not an integer number: {mins[index]}")
        try:
            _max = int(maxs[index])
        except ValueError:
            excelerror(row=excel_row_number, column='seat_max',
                       found=f"Not an integer number: {maxs[index]}")
        if _min > _max:
            excelerror(row=excel_row_number, column="seat_min/seat_max",
                       expected="seat_max is larger than seat_min",
                       found=f"seat_min={_min}, seat_max={_max}")
        seatsN = _max - _min
        if seatsN > 200:
            remark = ("if you are serious, use several lines with " + 
                      "sub-rooms left/center/right or so")
            excelerror(row=excel_row_number,
                    expected="No room has more than 200 seats in pandemic times",
                    found=f"{seatsN} seats, from {_min} to {_max} ({remark})")


def _create_importstep() -> arm.Importstep:
    result = arm.Importstep()
    result.save()
    return result


def _find_or_create_rooms(
        columnsdict: aue.Columnsdict,
        importstep: arm.Importstep
        ) -> tg.Sequence[arm.Room]:
    _validate_room_declarations(columnsdict)
    result = []
    newN = existingN = 0
    for idx in range(len(columnsdict['room'])):
        col = lambda name: columnsdict[name][idx] 
        room, created = arm.Room.objects.get_or_create(
                organization=col('organization'),
                department=col('department'),
                building=col('building'),
                room=col('room'),
                defaults=dict(seat_min=col('seat_min'),
                              seat_max=col('seat_max'),
                              importstep=importstep)
        )
    result.append(room)
    if created:
        newN += 1
    else:
        existingN += 1
        room.importstep = importstep
        room.save()
    return (result, newN, existingN)


def _find_or_create_seats(rooms: tg.Sequence[arm.Room]):
    result = []
    newN = existingN = 0
    for room in rooms:
        for seatnum in range(room.seat_min, room.seat_max+1):
            seat, created = arm.Seat.objects.get_or_create(
                    number=seatnum,
                    room=room,
                    defaults=dict(hash=seathash(room, seatnum))
            )
    result.append(seat)
    if created:
        newN += 1
    else:
        existingN += 1
    return (result, newN, existingN)

