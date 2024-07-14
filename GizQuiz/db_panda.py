from string import Template
import pandas as pd
import pyodbc
import warnings
warnings.filterwarnings('ignore') # пр€чем. вызов pd.read_sql генерит предупреждение о непротестированном на стороне pandas драйвере 

class DBpanda:
    connection_template = Template(r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=$db_path;Charset=utf-8")
    
    def __init__(self, access_db_path, table_name):
        self.access_db_path = access_db_path
        self.table_name = table_name
        self.engine = None
    
    @classmethod
    def connect_odbc(cls, access_db_path, table_name):
        cnxn = pyodbc.connect(cls.connection_template.substitute(db_path=access_db_path))
        cursor = cnxn.cursor()
        columns = "ObjectId, LandType, LandCode, Username, Ball_PlPoch, NDohod_d, SOATO, Area_ga, MelioCode, Forma22, Oblast, Rayon, R_zem, Data_Vvoda, SVovlech, Note_, Shape_Length, Shape_Area"
        sql = f"SELECT {columns} FROM {table_name}"
        data = pd.read_sql(sql,cnxn)
        return data
