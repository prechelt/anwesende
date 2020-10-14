import pytest

import anwesende.utils.excel

the_3by3_file = "anwesende/utils/tests/data/3by3.xlsx"

def test_read_excel_as_columnsdict():
    cd = anwesende.utils.excel.read_excel_as_columnsdict(the_3by3_file)
    assert set(cd.keys()) == set(["A-str", "B-int", "C-str"])
    assert cd['A-str'] == ["string1", "string2"]
    assert cd['B-int'] == [1, 4711]
    assert cd['C-str'] == [None, 4711]  # Ouch!:
    # the C-str column has cell format "Text", so it should return
    # "4711", not 4711.
    # We better prepare to receive either int or str, which also
    # means we need to rely less on authors not to change the xlsx template
    
    