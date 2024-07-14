import pyodbc
from string import Template


class db_server:
    
    connection_template = Template(r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=$db_path")
    
    def __init__(self, db_path) -> None:
        self.db_path = db_path
        
    def read_definitions(self):
        try:
            cnxn = pyodbc.connect(self.connection_template.substitute(db_path=self.db_path))
            cursor = cnxn.cursor()
            tbs = {}
            for row in cursor.tables( None, tableType='TABLE'):
                t = row.table_name
                columns = list()
                tbs[t] = columns
                for row_i in cursor.columns(table=t):
                    column_name = row_i.column_name
                    columns.append(column_name)
        except :
            return None
        finally:
            if cnxn != None:
                cnxn.close()
        return tbs
    
    def execute_query(self, Query):
        try:
            cnxn = pyodbc.connect(self.connection_template.substitute(db_path=self.db_path))
            cursor = cnxn.cursor()
            for row in cursor.execute(Query):
                yield row, cursor
        except :
            return False
        finally:
            if cnxn != None:
                cnxn.close()
        return True
