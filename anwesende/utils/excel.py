import collections
import typing as tg

import openpyxl

Columnsdict = tg.Mapping[str, tg.List]

def read_excel_as_columnsdict(filename: str) -> Columnsdict :
    """
    Return raw data from Excel's active sheet, except strings
    will be stripped of leading/trailing whitespace.
    First row is treated as column headers; column order is kept.
    """
    workbook = openpyxl.load_workbook(filename)
    sheet = workbook.active
    result = collections.OrderedDict()
    for col in sheet.iter_cols(values_only=True):
        colname = col[0]
        assert isinstance(colname, str)
        result[colname] = [_cleansed(cell) for cell in col[1:]]
    return result
    
def _cleansed(cell):
    if isinstance(cell, str): 
        return cell.strip()
    else: 
        return cell  # None or int or what-have-you