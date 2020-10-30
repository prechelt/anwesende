import datetime as dt
import random
import typing as tg

import django.utils.timezone as djut

import anwesende.room.models as arm
import anwesende.users.models as aum

def make_user_rooms_seats_visits(seatsN: int, visitsN: int) -> \
        tg.Tuple[arm.Importstep, arm.Room, tg.Sequence[arm.Visit]]:
    """
    Creates 2 Rooms, each with seatsN Seats, and visitsN Visits for each Room,
    of which groups of seatsN overlap and the next group is an hour later.
    seatsN different people are used round-robin for these Visits.
    The first Visit is 24h ago, each visit is 30 minutes and starts one minute
    after the previous one in the group.
    In room2, everything happens 10 minutes later than in room1.
    """
    MINUTE = dt.timedelta(minutes=1)
    user = aum.User.objects.create(username=f"datenverw{random.randint(1000,9999)}")
    visitlength = dt.timedelta(minutes=30)
    importstep = arm.Importstep(user=user)
    importstep.save()
    rooms = []
    seatgroups = []
    for roomI in range(2):
        when = djut.now() - dt.timedelta(hours=24) + dt.timedelta(minutes=roomI*10)
        visitI = 0
        room, seats = _make_seats(importstep, f"room{roomI+1}", seatsN)
        rooms.append(room)
        seatgroups.append(seats)
        while visitI < visitsN:
            for visitorI, seat in enumerate(seats):  # make visits
                tfrom = when + visitorI * MINUTE
                _make_visit(seat, tfrom, tfrom + visitlength, visitorI)
                visitI += 1
                if visitI == visitsN:
                    break;
            when += dt.timedelta(hours=1)  # next group one hour later
    return (rooms, seatgroups)


def _make_seats(importstep: arm.Importstep, roomname: str,
                numseats: int) -> tg.Tuple[arm.Room, tg.Sequence[arm.Seat]]:
    seats = []
    room = arm.Room(organization=f"org{random.randint(1000,9999)}",
                    department="dep", building="bldg",
                    room=roomname, seat_min=1, seat_max=numseats,
                    importstep=importstep)
    room.save()
    for i in range(numseats):
        seat = arm.Seat(hash=arm.Seat.seathash(room, i), number=i,
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