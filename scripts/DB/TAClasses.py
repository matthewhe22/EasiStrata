#!/usr/bin/env python

class TDB:
    def __init__(self,createby,createtime,updateby,updatetime):
        self.createby = createby
        self.createtime = createtime
        self.updateby = updateby
        self.updatetime = updatetime

from .DBClass import MySQLClass as MySQLDb

class TClient:
    fields = ['id','client_name','ABN','TFN','Address','telephone','email','IsDeleted','post_adr']
    table = 'base_client'
    def __init__(self,id):
        for field in TClient.fields:
            setattr(self,field,None) #create class attribute dynamically
        self.id = id
        self.client = {} # JSON object of client
        self.datasources=[] # list of TDataSrc
        self.glrules=[] # list of TGlRules
    def getClientFromDB(self): # SEARCH FOR TClient in DB
        #TODO: Change where clause
        where_clause = "where id='"+str(self.id)+"'"
        description, records = MySQLDb().selectData(TClient.table,fields=TClient.fields,where=where_clause)
        if len(records)==0:
            raise Exception("No client with client_code {} was found in DB".format(self.client_code))
        elif len(records)!=1:
            raise Exception("Multiple clients with client_code {} were found in DB".format(self.client_code))
        self.client = {} # Reset clients
        for index,field in enumerate(description):
            setattr(self,field,records[0][index])
            self.client[field] = records[0][index]
    def getDatasourcesFromDB(self,datasource=None):
        where_clause = "where client_ref="+str(self.id)
        if datasource is not None:
            where_clause += " AND data_src='"+datasource+"'"
        description, records = MySQLDb().selectData(TDataSrc.table,fields=TDataSrc.fields,where=where_clause)
        self.datasources=[] # Reset datasources
        for index,row in enumerate(records):
            datasource = {}
            for ix,field in enumerate(description):
                datasource[field] = row[ix]
            datasource = TDataSrc(datasource)
            self.datasources.append(datasource)


class TDataSrc(TDB):
    fields = ['id','data_src','filetype','sheet_mode','sheet_name','db_table','client_ref']
    table = 'base_datasource'
    def __init__(self,datasource={}):
        for field in TClient.fields:
            if field not in datasource:
                setattr(self,field,None)
            else:
                setattr(self,field,datasource[field])
        self.datasource = datasource
        self.rules = [] # list of TDataSrcRule
    def getDataSrcFromDB(self,client_code): # SEARCH FOR TDataSrc in DB by client_code
        pass # TODO:
    def getRulesFromDB(self,src_ref): # SEARCH FOR TDataSrc in DB by client_code
        where_clause = "where src_ref="+str(src_ref)
        description, records = MySQLDb().selectData(TDataSrcRule.table,fields=TDataSrcRule.fields,where=where_clause)
        self.rules=[] # Reset rules
        for index,row in enumerate(records):
            rule = {}
            for ix,field in enumerate(description):
                rule[field] = row[ix]
            rule = TDataSrcRule(rule)
            self.rules.append(rule)
    def __str__(self):
        return self.datasource

class TDataSrcRule(TDB):
    fields = ['id','src_header','ftype','cal_exp','map_field','is_trans',
              'reg_exp','src_ref']
    table = 'base_datasourcerule'
    def __init__(self,rule={}):
        for field in TDataSrcRule.fields:
            if field not in rule:
                setattr(self,field,None)
            else:
                setattr(self,field,rule[field])
        self.rule=rule
    def __str__(self):
        return self.rule

class TTb(TDB):
    fields = ['id','acc_code','acc_name','trust_code','property_code','beg_bal','end_bal',
                'movement','adj_code','period','ownership','client_ref','InforequestId','Version','COACd'] 
    table = 'base_tb'
    def __init__(self,tb={}):
        for field in TClient.fields:
            if field not in tb:
                setattr(self,field,None)
            else:
                setattr(self,field,tb[field])
        self.tb = tb

class TFaList(TDB):
    fields = ['id','Version','InforequestId','trust_code','fa_code','fa_location','fa_name','map_field1',
              'map_field2','map_field3','amount','note','src_ref','trans_field']
    table = 'trust_falist'
    def __init__(self,falist={}):
        for field in TFaList.fields:
            if field not in falist:
                setattr(self,field,None)
            else:
                setattr(self,field,falist[field])
        self.falist=falist
    def __str__(self):
        return self.falist

class TTaxInput(TDB):
    fields = ['id','adj_code','map_field1','map_field2','map_field3','adj_amount','trust_code','src_ref',
              'map_field10','map_field4','map_field5','map_field6','map_field7','map_field8','map_field9',
              'amount','property_code','InforequestId','Version','comments','desc']
    table = 'trust_taxinput'
    def __init__(self,taxinput={}):
        for field in TTaxInput.fields:
            if field not in taxinput:
                setattr(self,field,None)
            else:
                setattr(self,field,taxinput[field])
        self.taxinput=taxinput
    def __str__(self):
        return self.taxinput

class TImportLog(TDB):
    fields = ['id','doc','status','error_code','error_code','src_ref','InforequestId','Version']
    table = 'base_importlog'
    def __init__(self,importlog={}):
        for field in TImportLog.fields:
            if field not in importlog:
                setattr(self,field,None)
            else:
                setattr(self,field,importlog[field])
        self.importlog=importlog
    def __str__(self):
        return self.importlog

# class TGls(TDB):
#     fields = ['ID','client_ref','fund_code','trust_code','doc_num','doc_date','acc_code','acc_name',
#               'desc1','desc2','desc3','amount','adj_code','adj_code_manual','adj_amount',
#               'adj_amount_manual','period']
#     table = 't_gls'
#     def __init__(self,gls={}):
#         for field in TGls.fields:
#             if field not in gls:
#                 setattr(self,field,None)
#             else:
#                 setattr(self,field,gls[field])
#         self.gls=gls
#     def __str__(self):
#         return self.gls

# class TGlRules(TDB):
#     fields = ['ID','client_ref','seq_num','acc_code','keyword1','map_field1','keyword2','map_field2',
#               'keyword3','map_field3','threshold1','operator1','logic_oper','threshold2','operator2',
#               'adj_code','cal_method','is_valid']
#     table = 't_gl_rules'
#     def __init__(self,glrules={}):
#         for field in TGlRules.fields:
#             if field not in glrules:
#                 setattr(self,field,None)
#             else:
#                 setattr(self,field,glrules[field])
#         self.glrules=glrules
#     def __str__(self):
#         return self.glrules

TABLE_MAPPING = {
    TTb.table: TTb.fields,
    TFaList.table: TFaList.fields,
    TTaxInput.table: TTaxInput.fields,
    TImportLog.table: TImportLog.fields
}