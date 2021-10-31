from django.conf import settings
import django.core.exceptions as djce
import django.utils.timezone as djut
import pytest

import anwesende.room.forms as arf


def test_TimeOnlyDateTimeField_to_python_OK():
    fmt = "%Y-%m-%d %H:%M"
    now = djut.localtime().strftime(fmt)
    for input in ("17:27", "1727"):
        dt_val = arf.TimeOnlyDateTimeField().to_python(input)
        dt_str = dt_val.strftime(fmt)
        print(f"{input} --> {dt_str}")
        assert dt_str[-5:] == "17:27"   # correct time
        assert dt_str[:10] == now[:10]  # today's date


def test_TimeOnlyDateTimeField_to_python_wrong():
    with pytest.raises(djce.ValidationError) as ex:
        dt_val = arf.TimeOnlyDateTimeField().to_python("37:27")  # noqa
    assert "Falsches Uhrzeitformat" in str(ex.value)
