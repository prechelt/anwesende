import re
import typing as tg

import pytest

import anwesende.room.excel as are
import anwesende.room.models as arm
import anwesende.room.tests.makedata as artm
import anwesende.users.models as aum
import anwesende.utils.excel

# #### scaffolding:

excel_rooms1_filename = "anwesende/room/tests/data/rooms1.xlsx"
excel_rooms2_filename = "anwesende/room/tests/data/rooms2.xlsx"


def excel_example_columnsdict():
    # knowledge about file contents is hardcoded in many places
    return anwesende.utils.excel.read_excel_as_columnsdict(excel_rooms1_filename)


def check_error_w_patched_example(patcher, msg_elements):
    example = excel_example_columnsdict()
    patcher(example)
    with pytest.raises(are.InvalidExcelError) as err:
        are._validate_room_declarations(example)
    msg = str(err.value)
    for elem in msg_elements:
        assert elem in msg

# #### actual tests:


def test_validate_rooms_OK():
    example = excel_example_columnsdict()
    are._validate_room_declarations(example)  # no exception means success


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
        example['seat_last'][1] = "Z1S3"

    check_error_w_patched_example(patcher1, 
            ("seat_last", "Format", "Z1S3"))

    def patcher2(example):
        example['seat_last'][1] = "r0s1"

    check_error_w_patched_example(patcher2,
                                  ("seat_last", "row r must", "r0s1"))

    def patcher3(example):
        example['seat_last'][1] = "r100s1"

    check_error_w_patched_example(patcher3,
                                  ("seat_last", "row r must", "r100s1"))

    def patcher4(example):
        example['seat_last'][1] = "r2s0"

    check_error_w_patched_example(patcher4,
                                  ("seat_last", "seat s must", "r2s0"))


@pytest.mark.django_db
def test_create_seats_from_excel():
    user = aum.User.objects.create(name="x")
    stuff = are.create_seats_from_excel(excel_rooms1_filename, user)
    print(stuff)
    importstep = arm.Importstep.objects.first()
    # ----- check rooms:
    all_rooms = arm.Room.objects.filter(organization="fu-berlin.de")
    assert all_rooms.count() == 2
    print(list(all_rooms))
    qs_room055 = arm.Room.objects.filter(room="055")
    assert qs_room055.count() == 1
    room055: tg.Optional[arm.Room] = qs_room055.first()
    assert room055 and room055.importstep == importstep
    # ----- check seats:
    print(list(str(s) for s in arm.Seat.objects.all()))
    assert arm.Seat.objects.count() == 20
    qs_room055_seats = arm.Seat.objects.filter(room=room055)
    assert qs_room055_seats.count() == 14
    assert set(s.seatname for s in qs_room055_seats) == set((
        "r1s1", "r1s2", "r1s3", "r1s4", "r1s5", "r1s6", "r1s7",
        "r2s1", "r2s2", "r2s3", "r2s4", "r2s5", "r2s6", "r2s7"))
    myseat2 = qs_room055_seats[2]
    myseat5 = qs_room055_seats[5]
    assert myseat2.seatname != myseat5.seatname
    assert myseat2.hash != myseat5.hash
    assert re.fullmatch(r"[0-9a-f]{10}", myseat2.hash)


@pytest.mark.django_db
def test_collect_visitgroups():
    artm.make_user_rooms_seats_visits("r2s2", visitsN=4)
    targetvisit = arm.Visit.objects.filter(pk=arm.Visit.objects.first().pk)  # type: ignore
    vrows = are._as_vgrouprows(are.collect_visitgroups(targetvisit))
    result = set()
    for vr in vrows:
        vrowstr = f"{vr.familyname}: {vr.room}.{vr.seat}{vr.distance}"  # type: ignore
        result.add(vrowstr)
    should = set([
        "Visitor0: room1.r1s1  0.0m",
        "Visitor1: room1.r1s2  1.4m",
        "Visitor2: room1.r2s1  1.4m",
        "Visitor3: room1.r2s2  2.0m",
    ])
    assert result == should
