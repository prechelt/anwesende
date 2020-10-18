import collections
import os
import tempfile

import pytest

import anwesende.utils.excel as aue

the_3by3_file = "anwesende/utils/tests/data/3by3.xlsx"

def test_read_excel_as_columnsdict():
    cd = aue.read_excel_as_columnsdict(the_3by3_file)
    assert set(cd.keys()) == set(["A-str", "B-int", "C-str"])
    assert cd['A-str'] == ["string1", "string2"]
    assert cd['B-int'] == [1, 4711]
    assert cd['C-str'] == [None, 4711]  # Ouch!:
    # the C-str column has cell format "Text", so it should return
    # "4711", not 4711.
    # We better prepare to receive either int or str, which also
    # means we need to rely less on authors not to change the xlsx template
    

def test_write_excel_from_rowslists():
    TestTuple = collections.namedtuple('TestTuple', 'a b c dee')
    testdata = dict(test=[
        TestTuple(a="a1", b="b1", c="c1", dee="d1"),
        TestTuple(a="a2", b="b2", c="c2", dee="d2"),
    ])
    with tempfile.NamedTemporaryFile(prefix="test", suffix=".xlsx", 
                                     delete=False) as fh:
        filename = fh.name  # file is deleted in 'finally' clause
        print(filename)
    try:
        aue.write_excel_from_rowslists(filename, testdata)
        # import time
        # time.sleep(60)
        columns = aue.read_excel_as_columnsdict(filename)
        print(columns)
        assert list(columns.keys()) == ['a', 'b', 'c', 'dee']
        assert len(columns['dee']) == 2
        assert columns['c'][1] == "c2"
    finally:
        os.unlink(filename)