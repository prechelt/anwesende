import urllib.parse

import django.urls as dju
import pytest

import anwesende.room.utils as aru


def test_escape_slash():
    # We use URLs containing path elements containing non-ASCII characters and '/'.
    # The former are handled by Django, but '/' is left as is. See here:
    assert dju.reverse('room:visit', args=['a b']) == "/Sa%20b"
    assert dju.reverse('room:visit', args=['a%b']) == "/Sa%25b"
    assert dju.reverse('room:visit', args=['Ä']) == "/S%C3%84"
    assert dju.reverse('room:visit', args=['a%20b']) == "/Sa%2520b"
    with pytest.raises(dju.exceptions.NoReverseMatch):
        assert dju.reverse('room:visit', args=['a/b']) == "/Sa%2fb"
        # not found: It has two path elements, not just one

    # Our approach is to replace slashes in such URL parts with a slash-like
    # character and reverse the replacement before we use the value:
    kwargs = dict(organization="myorg", department="Zentrale Räume",
                  building="A/vorne")
    # The following transformation would be done in a template in the call
    # of {% url ... %} by applying the same-named template filter.
    # See show_rooms.html for examples.
    kwargs = { key: aru.escape_slash(value) 
               for key, value in kwargs.items() }
    url = dju.reverse('room:show-rooms-building', kwargs=kwargs)  # does not fail! 
    print(url)
    match = dju.resolve(urllib.parse.unquote(url))
    assert aru.unescape_slash(match.kwargs['organization']) == 'myorg'
    assert aru.unescape_slash(match.kwargs['building']) == 'A/vorne'