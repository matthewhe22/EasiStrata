
print('__file__={0:<35} | __name__={1:<20} | __package__={2:<20}'.format(__file__,__name__,str(__package__)))
from python import *
from python.calculation.backorder import *
from python.calculation.adj_cal import *
from python.calculation.cal_utils import * 
from python.calculation.trust_cal import *
from python.validation import *
from python.DBClass import MySQLClass
from python.calculation.backorder import get_cal_seq



# class created for debugging , subject to removal when triggered by django
class tmp_request():
    def __init__(self):
        self.client_ref=tmp_client()
        self.tax_year=2019
        self.cy_infoid=1
        self.cy_version=1
        self.py_infoid=2
        self.py_version=1
        self.fund_code='ISPT No.2'
        self.pk=2



class tmp_client():
    def __init__(self):
        self.pk=1



user_name='luoaa'


cal_task=tmp_request()


main_cal(cal_task,user_name)
