import datetime as dt
import random
import typing as tg

from django.conf import settings
import django.utils.timezone as djut

import anwesende.room.models as arm
import anwesende.users.models as aum
import anwesende.utils.date as aud

# Alas, two sets of operations with similar purposes.

def make_organizations(descr) -> None:
    """descr is a nested dict describing orgs, deps, rooms, #seats, like an xlsx."""
    persons = ("p1", "p2", "p3", "p4")
    personindex = 0
    for orgname, orgdescr in descr.items():
        for depname, depdescr in orgdescr.items():
            for roomname, roomdescr in depdescr.items():
                numseats, numvisits = roomdescr
                seats = make_seats(roomname, numseats, organization=orgname,
                                   department=depname)
                for i in range(numvisits):
                    make_visit(seats[i%len(seats)],
                               persons[personindex%len(persons)])
                    personindex += 1


def make_seats(roomname: str, numseats: int, organization="org",
               department="dep") -> tg.Tuple[arm.Seat, ...]:
    importstep = arm.Importstep.objects.first()  # reuse existing, if any
    if not importstep:
        user = aum.User.objects.first() or aum.User.objects.create(name="x")
        importstep = arm.Importstep(user=user)
        importstep.save()
    results = []
    room = arm.Room(organization=organization, department=department,
                    building="bldg",
                    room=roomname,
                    row_dist=1.3, seat_dist=0.8,
                    seat_last=arm.Seat.form_seatname(1, numseats),
                    importstep=importstep)
    room.save()
    for i in range(numseats):
        seat = arm.Seat(
            hash=arm.Seat.seathash(room, arm.Seat.form_seatname(1, i + 1)),
            rownumber=1, seatnumber=i + 1, room=room)
        seat.save()
        results.append(seat)
    return tuple(results)


def make_visit(seat: arm.Seat, person: str, tfrom="03:00",
               tto="04:00") -> arm.Visit:
    now = djut.localtime()
    present_from = aud.make_dt(now, tfrom)
    present_to = aud.make_dt(now, tto)
    assert present_from < present_to
    v = arm.Visit(givenname=person, familyname="fn",
                  street_and_number="sn", zipcode="12345", town="t",
                  phone=person, email=f"{person}@fn.de",
                  status_3g=arm.G_IMPFT,
                  submission_dt=now,
                  present_from_dt=present_from, present_to_dt=present_to,
                  seat=seat)
    v.save()
    return v


def make_user_rooms_seats_visits(seat_last: str, visitsN: int) -> \
        tg.Tuple[tg.Sequence[arm.Room], tg.Sequence[tg.Sequence[arm.Seat]]]:
    """
    Creates 2 Rooms, each with #seats Seats from 'r1s1' to seat_last, and 
    visitsN 30-minute Visits for each Room,
    of which groups of #seats overlap and the next group is an hour later.
    #seats different people are used round-robin for these Visits.
    The first Visit is 24h ago, 
    each visit starts one minute after the previous one in the group.
    In room2, everything happens 10 minutes later than in room1.
    """
    MINUTE = dt.timedelta(minutes=1)
    user = make_datenverwalter_user()
    visitlength = dt.timedelta(minutes=30)
    importstep = arm.Importstep(user=user)
    importstep.save()
    rooms = []
    seatgroups = []
    for roomI in range(2):
        when = djut.localtime() - dt.timedelta(hours=24) + dt.timedelta(minutes=roomI * 10)
        visitI = 0
        room, seats = _mursv_seats(importstep, f"room{roomI + 1}", seat_last)
        rooms.append(room)
        seatgroups.append(seats)
        while visitI < visitsN:
            for visitorI, seat in enumerate(seats):  # make visits
                tfrom = when + visitorI * MINUTE
                _mursv_visit(seat, tfrom, tfrom + visitlength, visitorI)
                visitI += 1
                if visitI == visitsN:
                    break
            when += dt.timedelta(hours=1)  # next group one hour later
    return (rooms, seatgroups)


def make_datenverwalter_user(username=None, password=None) -> aum.User:
    number = random.randint(1000, 9999)
    username = username or f"datenverw{number}"
    user = aum.User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password=password or "1234")
    user.assign_datenverwalter_group()
    return user


def _mursv_seats(importstep: arm.Importstep, roomname: str,
                 seat_last: str) -> tg.Tuple[arm.Room, tg.Sequence[arm.Seat]]:
    seats = []
    room = arm.Room(organization=f"org{random.randint(1000,9999)}",
                    department="dep", building="bldg",
                    row_dist=1.2, seat_dist=0.7,
                    room=roomname, seat_last=seat_last,
                    importstep=importstep)
    room.save()
    maxrow, maxseat = arm.Seat.split_seatname(seat_last)
    for r in range(1, maxrow + 1):
        for s in range(1, maxseat + 1):
            seatname = arm.Seat.form_seatname(r, s)
            seat = arm.Seat(hash=arm.Seat.seathash(room, seatname), 
                            rownumber=r, seatnumber=s,
                            room=room)
            seat.save()
            seats.append(seat)
    return (room, seats)


def _mursv_visit(seat: arm.Seat, tfrom: dt.datetime, tto: dt.datetime, visitorI: int):
    v = arm.Visit(givenname="V.", familyname=f"Visitor{visitorI}",
                  street_and_number="st", zipcode="12345", town="twn",
                  phone="ph", email=f"visitor{visitorI}@fn.de",
                  status_3g=arm.G_IMPFT if settings.USE_STATUS_3G_FIELD else arm.G_UNKNOWN,
                  submission_dt=tfrom + dt.timedelta(seconds=45),
                  present_from_dt=tfrom, present_to_dt=tto,
                  seat=seat)
    v.save()
