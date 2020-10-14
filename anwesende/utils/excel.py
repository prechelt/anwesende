import collections
import typing as tg

import openpyxl

Columnsdict = tg.Mapping[str, tg.List]

def read_excel_as_columnsdict(filename: str) -> Columnsdict:
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
    

RowsListsType = tg.Mapping[str, tg.List[tg.Optional[tg.NamedTuple]]]


def write_excel_from_rowslists(filename: str, rowslists: RowsListsType) -> None:
    workbook = openpyxl.Workbook()
    for sheetname, rows in rowslists.items():
        sheet = workbook.create_sheet(sheetname)
        _write_column_headings(sheet, rows[0], rownum=1)
        for rownum, row in enumerate(rows, start=2):
            _write_row(sheet, row, rownum)
    del workbook["Sheet"]  # get rid of initial default sheet
    workbook.save(filename)

 
def _write_column_headings(sheet, tupl: tg.NamedTuple, rownum: int):
    # use the tuple's element names as headings
    for colnum, colname in enumerate(tupl._fields, start=1):
        sheet.cell(column=colnum, row=rownum, value=colname)


def _write_row(sheet, tupl: tg.NamedTuple, rownum: int):
    for colnum, value in enumerate(tupl, start=1):
        sheet.cell(column=colnum, row=rownum, value=value)
