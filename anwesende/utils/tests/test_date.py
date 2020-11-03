import datetime as dt
import re

import django.utils.timezone as djut
import pytest
import pytz
from django.conf import settings

import anwesende.utils.date as aud


def test_nowstring():
    d_only = aud.nowstring()
    t_only = aud.nowstring(date=False, time=True)
    both = aud.nowstring(date=True, time=True)
    assert re.match(r"^\d\d\d\d-\d\d-\d\d$", d_only),\
           f"wrong d_only nowstring '{d_only}'"
    assert re.match(r"^\d\d:\d\d$", t_only),\
           f"wrong t_only nowstring '{t_only}'"
    assert re.match(r"^\d\d\d\d-\d\d-\d\d \d\d:\d\d$", both),\
           f"wrong both nowstring '{both}'"
    

def test_make_dt_with_tz():
    tzname = djut.get_current_timezone_name()
    now = djut.localtime()
    result = aud.make_dt(now, "12:34")
    print(tzname, now.tzname(), result.tzname())
    assert result.tzinfo.utcoffset(result) == \
           pytz.timezone(settings.TIME_ZONE).utcoffset(result)
    assert result.day == now.day
    assert result.hour == 12
    assert result.minute == 34
    assert result.second == 0


def test_make_dt_naive():
    with pytest.raises(AssertionError):
        aud.make_dt(dt.datetime.now(), "01:23")


def test_make_dt_illformed():
    with pytest.raises(AssertionError) as ex:
        aud.make_dt(djut.localtime(), "23.45")
    assert "hh:mm" in str(ex.value)
