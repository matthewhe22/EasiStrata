#!/usr/bin/env python
# coding: utf-8

# Dec 17 change to connection pool  DBUtils
from dbutils.persistent_db import PersistentDB
import mysql.connector
from mysql.connector import errorcode
import my_project.settings as local
from datetime import datetime





class MySQLClass(object):

    def __init__(self):

        POOL = PersistentDB(
        creator=mysql.connector,  # DB connector used
        maxusage=None,  #most reusable time of one connection
        setsession=[],  # orders to be executed when open a new session
        ping=1,
        # ping mysql server check availability of the DB service 0 = None = never, 1 = default = whenever it is requested, 2 = when a cursor is created, 4 = when a query is executed, 7 = always
        closeable=False,
        # setting to False to ignore conn.close()
        threadlocal=None,
        host=local.DATABASES['default']['HOST'],
        port=3306,
        user=local.DATABASES['default']['USER'],
        password=local.DATABASES['default']['PASSWORD'],
        database=local.DATABASES['default']['NAME'],
        # ssl_ca='/home/hema/my_project/venv/BaltimoreCyberTrustRoot.crt.cer'
        )

        try:
            self.cnx = POOL.connection()

        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                raise Exception('Username or password incorrect')
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                raise Exception('Database does not exist')
            else:
                raise Exception('Error: {}'.format(err))
    def commit(self):
        self.cnx.commit()

    def close(self):
        self.cnx.close()
        print ('connection closed ')
    def executeStatement(self,sql_stmt):
        cursor = self.cnx.cursor()
        cursor.execute(sql_stmt)
        self.cnx.commit()
        number = cursor.rowcount
        cursor.close()
        return number
    def insertData(self,table,data):
        cursor = self.cnx.cursor()
        attributes,values=[],[]
        for attribute in data:
            attributes.append(attribute)
            values.append("%("+attribute+")s")
        attributes="("+(','.join(attributes))+")"
        values="("+(','.join(values))+")"
        add_data = ("INSERT INTO "+table+" "+attributes+" VALUES "+values)
        # print(data)
        # print(add_data)
        cursor.execute(add_data, data)
        cursor.close()
    def insertDataMany(self,table,attributes,data): # attributes:<list of str> data:<list of tuples>
        # print (attributes,data)
        cursor = self.cnx.cursor()
        values=[]
        for attribute in attributes:
            values.append("%s")
        attributes="("+(','.join(attributes))+")"
        values="("+(','.join(values))+")"
        add_data = ("INSERT INTO "+table+" "+attributes+" VALUES "+values)
        # print (f'add data is {add_data}')
        cursor.executemany(add_data, data)
        self.cnx.commit()
        cursor.close()
    def selectData(self,table,fields=None,where=None,data=None):
        cursor = self.cnx.cursor()
        if fields is None:
            projection = "*"
        else:
            if type(fields).__name__=='list':
                projection = ','.join(fields)
            elif type(fields).__name__=='str':
                projection = fields
            else:
                raise Exception('"fields" should be list or string, type {} is not valid'.format(type(fields).__name__))
        if where is None:
            where = ""
        else:
            if type(where).__name__!='str':
                raise Exception('"where" should be string, type {} is not valid'.format(type(where)))
        query = ("SELECT "+projection+" FROM "+table+" "+where)

        if data is None:
            cursor.execute(query)
        else:
            if type(data).__name__ == 'tuple':
                cursor.execute(query,data)
            else:
                raise Exception('"data" should be tuple, type {} is not valid'.format(type(data)))
        records = cursor.fetchall()
        description = [field[0] for field in cursor.description]
        cursor.close()
        return description, records # (['ID','client_code',...],[(4,'ISPT',...),(),...])

    def get_result(self,query):
        cursor = self.cnx.cursor()
        cursor.execute(query)
        records=cursor.fetchall()
        return records


    def datemodel_insert(self,table,attributes,data,user):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        attr_date=['createby','updateby','createtime','updatetime']
        title=attributes+attr_date
        for item in data:
            item=item.extend([user,user,now,now])
        
        self.insertDataMany(table,title,data)


