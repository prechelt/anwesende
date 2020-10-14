import datetime as dt

import django.utils.timezone as djut


def dtstring(dtobj, date=True, time=False) -> str:
    if date and time:
        format = "%Y-%m-%d %H:%M"
    elif date:
        format = "%Y-%m-%d"
    elif time:
        format = "%H:%M"
    else:
        assert False, "You don't want an empty nowstring, do you?"
    return dtobj.strftime(format)


def nowstring(date=True, time=False) -> str:
    now = djut.now()
    return dtstring(now, date, time)
