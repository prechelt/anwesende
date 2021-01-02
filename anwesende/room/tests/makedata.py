import datetime as dt
import random
import typing as tg

import django.utils.timezone as djut

import anwesende.room.models as arm
import anwesende.users.models as aum


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
        room, seats = _make_seats(importstep, f"room{roomI+1}", seat_last)
        rooms.append(room)
        seatgroups.append(seats)
        while visitI < visitsN:
            for visitorI, seat in enumerate(seats):  # make visits
                tfrom = when + visitorI * MINUTE
                _make_visit(seat, tfrom, tfrom + visitlength, visitorI)
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


def _make_seats(importstep: arm.Importstep, roomname: str,
                seat_last: str) -> tg.Tuple[arm.Room, tg.Sequence[arm.Seat]]:
    seats = []
    room = arm.Room(organization=f"org{random.randint(1000,9999)}",
                    department="dep", building="bldg",
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


def _make_visit(seat: arm.Seat, tfrom: dt.datetime, tto: dt.datetime, visitorI: int):
    v = arm.Visit(givenname="V.", familyname=f"Visitor{visitorI}",
                  street_and_number="st", zipcode="12345", town="twn",
                  phone="ph", email=f"visitor{visitorI}@fn.de",
                  submission_dt=tfrom + dt.timedelta(seconds=45),
                  present_from_dt=tfrom, present_to_dt=tto,
                  seat=seat)
    v.save()
