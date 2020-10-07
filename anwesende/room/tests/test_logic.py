import re

import pytest

import anwesende.room.logic as arl
import anwesende.room.models as arm
import anwesende.utils.excel

##### scaffolding:

excel_example_filename = "anwesende/room/tests/data/rooms1.xlsx"


def excel_example_columnsdict():
    # knowledge about file contents is hardcoded in many places
    return anwesende.utils.excel.read_excel_as_columnsdict(excel_example_filename)

def check_error_w_patched_example(patcher, msg_elements):
    example = excel_example_columnsdict()
    patcher(example)
    with pytest.raises(arl.InvalidExcelError) as err:
        arl._validate_room_declarations(example)
    msg = str(err.value)
    for elem in msg_elements:
        assert elem in msg

##### actual tests:
    
def test_validate_rooms_OK():
    example = excel_example_columnsdict()
    arl._validate_room_declarations(example)  # no exception means success


def test_validate_rooms_with_column_missing():
    def patcher(example):
        del example['room']
    check_error_w_patched_example(patcher, ("missing", "room"))


def test_validate_rooms_with_additional_column():
    def patcher(example):
        example['surprisecolumn'] = [1, 2]
    check_error_w_patched_example(patcher, ("additional", "surprisecolumn"))


def test_validate_rooms_with_mixed_organizations():
    def patcher(example):
        example['organization'][1] = "uni-flensburg.de"
    check_error_w_patched_example(patcher, 
            ("multiple", "berlin", "flensburg"))


def test_validate_rooms_with_wrong_seats():
    def patcher1(example):
        example['seat_min'][1] = "abc"
    check_error_w_patched_example(patcher1, 
            ("seat_min", "number", "abc"))
    def patcher2(example):
        example['seat_max'][1] = "def"
    check_error_w_patched_example(patcher2, 
            ("seat_max", "number", "def"))
    def patcher3(example):
        example['seat_min'][1] = "7"
    check_error_w_patched_example(patcher3, 
            ("larger", "seat_min=7", "seat_max"))


@pytest.mark.django_db
def test_create_seats_from_excel():
    stuff = arl.create_seats_from_excel(excel_example_filename)
    print(stuff)
    #----- check importstep:
    assert arm.Importstep.objects.all().count() == 1
    importstep = arm.Importstep.objects.first()
    #----- check rooms:
    assert arm.Room.objects.filter(organization="fu-berlin.de").count() == 2
    qs_room055 = arm.Room.objects.filter(room="055")
    assert qs_room055.count() == 1
    room055: arm.Room = qs_room055.first()
    assert room055.importstep == importstep
    #----- check seats:
    print(list((s.room.room, s.number) for s in arm.Seat.objects.all()))
    assert arm.Seat.objects.count() == 20
    qs_room055_seats = arm.Seat.objects.filter(room=room055)
    assert qs_room055.count() == 14
    assert set(s.number for s in qs_room055) == set(range(1, 14+1))
    myroom2 = qs_room055[2]
    myroom5 = qs_room055[5]
    assert myroom2.number != myroom5.number
    assert myroom2.hash != myroom5.hash
    assert re.fullmatch(r"[0-9a-f]{12}", myroom2.hash)