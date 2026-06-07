#!/usr/bin/env python

from .DBClass import MySQLClass as MySQLDb
from .TAClasses import *
from scripts.utils.str_utils import tuple_cell_to_list
from scripts.utils.date_utils import get_today
from base.models import DataSource, DataSourceRule

import scripts.DB.UtilFiles as UF
from datetime import date
import my_project.settings as local


# VALIDATION RULES- TODO already moved to the validutils.py
def validateFile(file):
    if not UF.doesFileExist(file):
        raise FileNotFoundError("File {} does not exist".format(file))
    # TODO: Change to check CONFIG FILE
    valid_extensions = ['xlsb', 'xlsx']
    valid_extensions = [ext.lower().strip() for ext in valid_extensions]
    extension = file.split('.') [-1].lower()
    if extension not in valid_extensions:
        raise TypeError(
            "Extension {} is invalid. Please use the same data format in your config file".format(extension))


def matchSheetname(sheetname, pattern):
    if pattern.startswith('%'):
        if pattern.endswith('%'):
            pattern = pattern [1:-1]
        else:
            pattern = pattern [1:]
    elif pattern.endswith('%'):
        pattern = pattern [:-1]
    if pattern in sheetname:
        return True
    return False


def loadSheets(excel_doc, sheet_mode, sheet_name):
    if sheet_mode == "ALL":
        excel_doc.loadDfAll()
    elif sheet_mode == "SINGLE":
        excel_doc.loadDfSheet(sheet_name)
    elif sheet_mode == "MATCH":
        for name in excel_doc.sheetnames:
            if matchSheetname(name, sheet_name):
                excel_doc.loadDfSheet(name)
    else:
        raise Exception("Sheet not found")


import pandas as pd


def buildIsTransDf(df, dict_info_trans):
    fields = []
    for value in dict_info_trans.values():
        if value ['map_field'] not in fields:
            fields.append(value ['map_field'])
    df_columns = ['ix', 'trans_field']
    for field in fields:
        df_columns.append(field)
    datarow = []
    for ix, row in df.iterrows():
        for col, value in row.items():
            col_name = dict_info_trans [col] ['src_header']
            field_name = dict_info_trans [col] ['map_field']
            tmp_row = [None] * len(df_columns)
            tmp_row [0], tmp_row [1] = ix, col_name
            tmp_row [df_columns.index(field_name)] = value
            datarow.append(tmp_row)
    return pd.DataFrame(datarow, columns=df_columns)


'''
Clean Dataframes in ed with only attributes in datasource rule,
ed contains only No Trans dataframes 
and returns Trans Datarame (is_trans=1) 
'''


def parseSheetDataframe(ed, sheetname, tdatasrc):
    row_ix = None
    list_columns, list_columns_trans, dict_info_trans = [], [], {}
    column_map = {}  # {'A':'property_code'}
    # Check src_header and is_trans for every rule
    for t_rule in tdatasrc:
        fieldname = t_rule.src_header
        is_trans = t_rule.is_trans
        # Skip if is a calculation
        rule_datatype = t_rule.ftype
        if rule_datatype == 'cal':
            continue
        # Return row and column index at first occurrence
        row_ix, column_ix = ed.findValue(sheetname, fieldname, row=row_ix)
        if is_trans == 0:
            column_map [column_ix] = t_rule.map_field
            list_columns.append(column_ix)
        else:
            column_map [column_ix] = t_rule.src_header
            list_columns_trans.append(column_ix)
            dict_info_trans [column_ix] = {'src_header': fieldname
                , 'map_field': t_rule.map_field}
    # Filter dataframe with only list_columns
    df_sheet = ed.sheets [sheetname]
    # Remove duplicates (for repeated headers)
    df_sheet.drop_duplicates(inplace=True)
    df_sheet = df_sheet.loc [row_ix + 1:, list_columns + list_columns_trans]
    # Replace empty with None
    df_sheet = df_sheet.where(df_sheet != '', None)
    # Remove empty rows from dataframe
    df_sheet.dropna(axis='rows', how='all', inplace=True)
    # Remove rows that have at least 2 empty cells
    # df_sheet.dropna(axis='rows', thresh=df_sheet.shape [1] - 2, inplace=True)
    # Get No Trans DF (is_trans=0)
    df_sheet_notrans = df_sheet.loc [:, list_columns].copy()
    # Change headers No Trans
    df_sheet_notrans.rename(columns=column_map, inplace=True)
    # Get Trans DF (is_trans=1)
    df_sheet_trans = None
    if len(list_columns_trans) > 0:
        # Convert No Trans DF index as column 'ix'
        df_sheet_notrans ['ix'] = df_sheet_notrans.index
        df_sheet_trans = df_sheet.loc [row_ix + 1:, list_columns_trans].copy()
        df_sheet_trans = buildIsTransDf(df_sheet_trans, dict_info_trans)
        df_sheet_notrans = pd.merge(df_sheet_notrans, df_sheet_trans, on='ix')
        # Drop column 'ix'
        df_sheet_notrans.drop(columns=['ix'], inplace=True)
    ed.sheets [sheetname] = df_sheet_notrans
    return df_sheet_notrans


# FUNCTION get datasource column rules (regex, calculate)
import re
from ast import literal_eval


def applyRuleFormula(rule, value):
    result = value
    if 'regex' in rule:
        arr_regx = literal_eval(rule ['regex'])
        joiners = arr_regx [1:]
        value = 'IR809399'  # dummy
        rex = arr_regx [0]
        m = re.search(rex, value)
        if m:
            result = m.group(1)
            for ix, joiner in enumerate(joiners):
                result = joiner.join([result, m.group(ix + 2)])
    return result


class Node:
    def __init__(self, field, formula):
        self.level = 0
        self.field = field
        self.formula = formula
        self.children = []

    def addChild(self, newChild):
        self.children.append(newChild)
        newChild._updateLevel(self)

    def _updateLevel(self, node):
        self.level = max(node.level + 1, self.level)
        for child in self.children:
            child._updateLevel(self)

    def __str__(self):
        return self.field


class GraphAttributes:
    def __init__(self, colFormulaCalExp):
        self.nodes = {}  # {"A":Node('A'),...}
        self.independentNodes = []
        self._buildGraph(colFormulaCalExp)

    def _getFieldsFromFormula(formula):
        fields = []
        tmplist = list(map(lambda x: x.strip(), re.split('[-+*/()]', formula)))
        for attrib in tmplist:
            if attrib != '' and not attrib.isnumeric():
                fields.append(attrib)
        return fields

    def _buildGraph(self, colFormulaCalExp):
        for field, formula in colFormulaCalExp.items():
            self.nodes [field] = Node(field, formula)
        for field, node in self.nodes.items():
            formulaFields = GraphAttributes._getFieldsFromFormula(colFormulaCalExp [field])
            for formulaField in formulaFields:
                if formulaField in colFormulaCalExp.keys():
                    node.addChild(self.nodes [formulaField])
                elif formulaField not in self.independentNodes:
                    self.independentNodes.append(formulaField)

    def getOrderedAttributes(self):
        orderedNodes = list(self.nodes.values())
        orderedNodes.sort(key=lambda x: x.level, reverse=True)
        orderedNodes = [node.field for node in orderedNodes]
        return orderedNodes


# FUNCTION importData
from scripts.DB import ExcelDoc as ED
from datetime import datetime

edd = None
keyParameters = ['client_code', 'file_path', 'datasource']


def importData(importParameters):
    if not isinstance(importParameters, dict):
        raise Exception("Parameters must be given in a dictionary")
    file_path = importParameters ['file_path']
    if type(file_path) != str:
        raise Exception("Input should be a path or a file")
    ##### VALIDATE DATAFILES:  input = file_path (string that could be file or a path)
    valid_files, invalid_files = [], []
    if UF.isFile(file_path):
        validateFile(file_path)
        valid_files.append(file_path)
    elif UF.isDirectory(file_path):
        files = UF.getAbsoluteFilepathFromDirectory(file_path)
        for file in files:
            try:
                validateFile(file)
                valid_files.append(file)
            except TypeError as e:
                invalid_files.append(file)
        if len(valid_files) == 0:
            raise Exception("There are no valid files in directory", file_path)
        for file in invalid_files:
            print("WARNING: File", file, "is not a valid file format")
    if len(valid_files) == 0:
        raise Exception("{} is not a valid file".format(file_path))

    for file in valid_files:
        importDataFile(importParameters)


# FUNCTION importDataFile
def importDataFile(importParameters):
    # GET META DB STRUCTURE, name with fields
    TABLE_MAPPING = get_table_mapping()

    # Get parameters from dictionary
    datasource = importParameters ['datasource']
    filepath = importParameters ['file_path']
    user = importParameters ['user']
    ed = ED.ExcelDoc(filepath)
    data_source = DataSource.objects.get(pk=datasource)

    sheet_mode, sheet_name = data_source.sheet_mode, data_source.sheet_name
    # Get column rules (regex, calculate)
    colFormulaRegex = {}
    colFormulaCalExp = {}
    cal_exp_indep_attr, cal_exp_dep_attr = [], []  # lists of all/dependent attributes for cal_exp
    data_rules = DataSourceRule.objects.filter(src_ref_id=datasource)
    field_attr = {}
    for trule in data_rules:
        field_attr [trule.map_field] = trule.ftype
        if trule.reg_exp not in [None, '']:
            colFormulaRegex [trule.map_field] = trule.reg_exp
        elif trule.cal_exp not in [None, '']:
            # Add rule attributes to cal_exp_attributes list
            colFormulaCalExp [trule.map_field] = trule.cal_exp

    # Get independent and dependent attributes for all cal_exp
    if len(colFormulaCalExp) > 0:
        ga = GraphAttributes(colFormulaCalExp)
        cal_exp_indep_attr = ga.independentNodes
        cal_exp_dep_attr = ga.getOrderedAttributes()

    print("Loading sheets")
    loadSheets(ed, sheet_mode, sheet_name)  # load sheets from file
    ##### is_trans function included in parseSheetDataframe
    # ed_trans = ed.copy()
    # trans_sheets = []
    ## Modify df sheets for all ed
    for sheet in ed.sheets:
        ## modify ed sheet dataframe
        sheetname = sheet
        df_trans = parseSheetDataframe(ed, sheetname, data_rules)
    ##### VALIDATE RULES: input = ed,dsource (<ExcelDoc>,<TDataSrc>) If error->finish
    table_ds = data_source.db_table
    # get extra column names and values
    extra_col_value = extra_col(importParameters, TABLE_MAPPING [table_ds], user, datasource)
    extra_col_name = extra_col_value [0]
    extra_row_value = extra_col_value [1]

    for sheet in ed.sheets:
        df_sheet = ed.sheets [sheet]
        attrib_insert, data_insert = [], []

        attrib_insert.extend(list(df_sheet.columns))

        attrib_insert.extend(cal_exp_dep_attr)
        # update by AL for extra column names
        attrib_insert.extend(extra_col_name)

        roundNumber = 1
        for ix, row in df_sheet.iterrows():
            datarow = []
            for col, value in row.items():

                if type(value).__name__ == "str":
                    value = value.strip()

                # update by AL to tackle the number being recognized as integer
                if field_attr.get(col) == 'string' and type(value).__name__ == "float":
                    value = str(int(value))

                datarow.append(value)

                # update by AL for extra value for each row

            datarow.extend(extra_row_value)

            data_insert.append(tuple(datarow))
            if ix > roundNumber * 4000:
                roundNumber += 1

                MySQLDb().insertDataMany(table_ds, attrib_insert, data_insert)
                data_insert = []
        # Insert Final Rows in DB
        print(f'and data is {data_insert [0]}')
        MySQLDb().insertDataMany(table_ds, attrib_insert, data_insert)


def get_table_mapping():
    table_mapping = {}
    schema = local.DATABASES ['default'] ['NAME']
    sql_stat = 'SELECT table_name FROM information_schema.tables where table_schema="%s"'
    sql_stat = sql_stat % (schema)

    table_list = MySQLDb().get_result(sql_stat)

    for table in table_list:
        sql_stat = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = '%s' and table_name='%s'"
        sql_stat = sql_stat % (schema, table [0])
        field_list = MySQLDb().get_result(sql_stat)
        # convert tuple cells to normal list
        field_list = tuple_cell_to_list(field_list)
        table_mapping [table [0]] = field_list

    return table_mapping


def extra_col(import_para, ds_structure, user, ds_id):
    """

    :param import_para: import file dict
    :param ds_structure: target table data structure
    :param user: import user
    :return: list1, extra col name , list2, extra col value
    """
    extra_col_name = []
    extra_row_value = []
    ds_rules = DataSourceRule.objects.filter(src_ref_id=ds_id)
    # col_list is the column name list from excel file
    col_list = []
    for item in ds_rules:
        col_list.append(item.map_field)

    for item in ds_structure:
        if item in import_para and item not in col_list:
            extra_col_name.append(item)
            extra_row_value.append(import_para [item])

    extra_col_name.extend(['createby', 'updateby', 'createtime', 'updatetime'])
    extra_row_value.extend([user, user, get_today(), get_today()])

    return extra_col_name, extra_row_value
