import pandas as pd
import numpy as np
from pyxlsb import open_workbook as open_xlsb
import os
import xlrd
import xlsxwriter
from scripts.DB import UtilFiles as UF
from scripts.DB import UtilText as UT


# CUSTOM FUNCTIONS
def markDiffSheet(writer, sheetname, colour):
    worksheet = writer.sheets [sheetname]
    worksheet.set_tab_color(colour)


def markDiffCell(writer, sheetname, cell_position, cell_value, colour):
    worksheet = writer.sheets [sheetname]
    cell_format = writer.book.add_format()
    cell_format.set_bg_color(colour)
    worksheet.write(cell_position, cell_value, cell_format)


class ExcelDoc:
    def __init__(self, file=None):
        self.sheetnames = []
        self.sheets = {}
        if file is None:
            self.root, self.filename = None, None
            self.name, self.filetype = None, None
            self.filepath = None
        else:
            if not UF.doesFileExist(file):
                raise Exception('File "{}" does not exists'.format(file))
            self.root, self.filename = UF.parseFilePath(file)
            self.name, extension = UF.parseFileName(self.filename)
            self.filepath = os.path.join(self.root, self.filename)
            if extension.lower() == 'xlsb':
                with open_xlsb(file) as wb:
                    for sheetname in wb.sheets:
                        self.sheetnames.append(sheetname)
            elif extension.lower() == 'xlsx':
                xlsx = pd.ExcelFile(file)
                self.sheetnames = xlsx.sheet_names
            elif extension.lower() == 'csv':
                pass
            else:
                raise Exception('Extension .{} is not recognised as excel file'.format(extension))
            self.filetype = extension.lower()

    def copy(self):
        ed = ExcelDoc()
        ed.root, ed.filename = self.root, self.filename
        ed.name, ed.filetype = self.name, self.filetype
        ed.filepath = self.filepath
        ed.sheetnames = self.sheetnames
        ed.sheets = {}
        for sheet in self.sheets:
            ed.sheets [sheet] = self.sheets [sheet].copy()
        return ed

    def findValue(self, sheetname, fieldname, row=None):
        if sheetname not in self.sheets:
            self.loadDfSheet(sheetname)
        df = self.sheets [sheetname]
        if row != None:
            df = df.loc [row:row, :]
        try:
            ix, col = UT.findValueInDf(df, fieldname)
            return ix, col
        except LookupError as err:
            raise LookupError("{} in sheet '{}' from file '{}'".format(err, sheetname, self.filename))

    def findValueAll(self, sheetname, fieldname):
        if sheetname not in self.sheets:
            self.loadDfSheet(sheetname)
        df = self.sheets [sheetname]
        return UT.findValueAllInDf(df, fieldname)

    def _getSheetDF(self, sheetname):
        if sheetname not in self.sheets:
            self.loadDfSheet(sheetname)
        return self.sheets [sheetname]

    def loadDfAll(self):
        self.sheets = {}
        for sheetname in self.sheetnames:
            self.loadDfSheet(sheetname)

    def loadDfSheet(self, sheetname):
        if sheetname not in self.sheetnames:
            raise Exception('{} is not in file'.format(sheetname))
        if self.filetype == 'xlsb':
            # TODO:
            with open_xlsb(self.filepath) as wb:
                sheet = wb.get_sheet(sheetname)
                tmpdf = []
                for row in sheet.rows():
                    tmpdf.append([item.v for item in row])
                tmpdf = pd.DataFrame(tmpdf)
                tmpdf.index = np.arange(1, tmpdf.shape [0] + 1)
                tmpdf.columns = [UT.index2letter(i) for i in range(tmpdf.shape [1])]
                self.sheets [sheetname] = tmpdf
        elif self.filetype == 'xlsx':
            with xlrd.open_workbook(self.filepath) as wb:
                tmpdf = []
                sheet = wb.sheet_by_index(self.sheetnames.index(sheetname))
                for row_index in range(sheet.nrows):
                    tmpdf.append(sheet.row_values(row_index))
                tmpdf = pd.DataFrame(tmpdf)
                tmpdf.index = np.arange(1, tmpdf.shape [0] + 1)
                tmpdf.columns = [UT.index2letter(i) for i in range(tmpdf.shape [1])]
                self.sheets [sheetname] = tmpdf
        elif self.filetype == 'csv':
            pass

    def compareSheetNames(self, other):
        if type(other) != ExcelDoc:
            raise Exception('Must compare with another ExcelDoc')
        sheetsSelf, sheetsOther, common_sheets = [], [], []
        for sheetname in self.sheetnames:
            if sheetname not in other.sheetnames:
                sheetsSelf.append(sheetname)
            else:
                common_sheets.append(sheetname)
        for sheetname in other.sheetnames:
            if sheetname not in common_sheets:
                sheetsOther.append(sheetname)
        return common_sheets, sheetsSelf, sheetsOther

    def compareSheetValues(self, other, sheetname, indices=[], selfSheetname=None, withNumbers=False):
        if type(other) != type(self):
            raise Exception('Must compare with another ExcelDoc')
        if type(sheetname) != str:
            raise Exception('Sheetname must be a string')
        if type(indices) != list:
            raise Exception('Indices (3rd parameter) must be a list')
        if len(indices) == 0:
            indices = [None, None, None, None]
        if selfSheetname is None:
            selfSheetname = sheetname
        if selfSheetname not in self.sheets:
            self.loadDfSheet(selfSheetname)
        if sheetname not in other.sheets:
            other.loadDfSheet(sheetname)
        row_start, row_end, column_start, column_end = indices [0], indices [1], indices [2], indices [3]
        selfDf = self.sheets [selfSheetname].loc [row_start:row_end, column_start:column_end]
        otherDf = other.sheets [sheetname].loc [row_start:row_end, column_start:column_end]
        return UT.compareDfs(selfDf, otherDf)

    def compareFiles(self, other, outputPath):
        if not UF.checkIfPathExists(UF.correctPath(outputPath)):
            raise Exception('File "{}" does not exists'.format(file))
        print(outputPath + os.sep + self.name + '_diff.xlsx')
        print(outputPath + os.sep + other.name + '_diff.xlsx')
        common_sheets, sheetsSelf, sheetsOther = self.compareSheetNames(other)
        # Create Summary Sheets Comparison
        sheetsSelf, sheetsOther = UT.compareLists(self.sheetnames,
                                                  other.sheetnames)  # lists of same length with differences
        diff_columns = [self.name, other.name]
        diff_sheets = zip(sheetsSelf, sheetsOther)
        writer_summ = pd.ExcelWriter(outputPath + os.sep + 'Summary_Differences.xlsx', engine='xlsxwriter')
        dfSumm = pd.DataFrame(diff_sheets, columns=diff_columns)
        dfSumm.to_excel(writer_summ, sheet_name='Sheets Summary', index=False)
        writer_summ.save()
        # Duplicate Each File, Marking in Red the Sheets and Cell Differences
        writer_self = pd.ExcelWriter(outputPath + os.sep + self.name + '_diff.xlsx', engine='xlsxwriter')
        writer_other = pd.ExcelWriter(outputPath + os.sep + other.name + '_diff.xlsx', engine='xlsxwriter')
        for sheetname in common_sheets:
            if sheetname not in self.sheets:
                self.loadDfSheet(sheetname)
            if sheetname not in other.sheets:
                other.loadDfSheet(sheetname)
            print('Comparing Sheetname:', sheetname)
            dfself, dfother, diff, hasChanged = self.compareSheetValues(other, sheetname)
            dfself.to_excel(writer_self, sheet_name=sheetname, header=False, index=False)
            dfother.to_excel(writer_other, sheet_name=sheetname, header=False, index=False)
            if hasChanged:
                markDiffSheet(writer_self, sheetname, 'red')
                markDiffSheet(writer_other, sheetname, 'red')
                for ix in diff:
                    cell = diff [ix]
                    writer = writer_self if ix == 1 else writer_other
                    for cell_position in cell:
                        cell_value = cell [cell_position]
                        markDiffCell(writer, sheetname, cell_position, cell_value, 'red')
        #             break
        writer_self.save()
        writer_other.save()
