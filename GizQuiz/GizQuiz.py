import os
import sys
import getopt

from datetime import datetime
import time

from giz_view import giz_view
from report_class import report
from db_panda import DBpanda

class giz_quiz:
    def __init__(self, mdb_file_path = 'DKR.mdb', table_name = 'dkr_table',
                 results_folder = '', temlate_path = 'template.xlsx',
                 result_file_prefix = 'gis_lands'):
        self.mdb_file_path = mdb_file_path              # путь к БД mdb 
        self.table_name = table_name                    # имя таблицы из файла БД mdb
        self.results_folder = results_folder            # папка, куда складываются документы, генерируемые программой
        self.temlate_path = temlate_path                # файл-шаблон генерируемого документа
        self.result_file_prefix = result_file_prefix    # префикс имени генерируемого документа
        
    def eval(self, region_ind = 1): # region_ind: в данной версии скрипта возможно формировать выборку только с указанием идентификатора региона
        # собираем данные из базы MS Access
        df = DBpanda.connect_odbc(self.mdb_file_path, self.table_name)  # Evaluation time: 39.46103763580322
        print(f"Rows count: {df.shape[0]}")
        # формирование наборов данных, используемых при построении отчета
        giz = giz_view(df)
        # если будет необходимость, спискок полей первичной фильтрации наборов данных может быть расширен
        gs = giz.prepare(region_ind)
        gs = giz.source
        # построение используемых наборов аргрегатных данных
        cd1 = giz.collect_data(["region_ind", "Rayon"])
        cd2 = giz.collect_data(["Rayon", "Forma22"])
        cd3 = giz.collect_data(["region_ind"])
        cd4 = giz.collect_data(["Forma22"])
        op = self.results_folder   # папка, куда складываются документы, генерируемые программой
        tp = self.temlate_path # файл-шаблон генерируемого документа
        tn = self.result_file_prefix # префикс имени генерируемого документа
        rm = report(tn, tp, op) # построитель отчета - документа
        rm.set_field_values({
            'dates':None,"region_id": region_ind, # список полей, которые подставляются в формируемый документ
            'Form22':None,
            'date':datetime.now().strftime('%d-%m-%Y'),
            'cd1':cd1, 'cd2':cd2, 'cd3':cd3, 'cd4':cd4}) # наборы данных, используемые при постороеним документа
        result_file = rm.run()
        print(f"Сформирован файл {result_file}")

start = time.time()

def get_args(argv = None):
    if argv == None:
        argv = sys.argv
    opt_dir = {}
    arg_help = "{0} -d <mdb database path> -t <table name> -r <results directory> -e <path to excel file with report template> -p <report file prefix> -i <index number of region>".format(argv[0])
    try:
        oa = getopt.getopt(argv[1:], "d:t:r:e:p:i:h", ["db=", "table=", "res_dir=", "rep_template=", "rep_pref=", "region_ind=", "help"])
        opts, args = oa
        if len(opts) == 0:
            print(arg_help)  # print the help message
            sys.exit(2)
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(arg_help)  # print the help message
                sys.exit(2)
            elif opt in ("-d", "--db"):
                if arg != None and arg != '':
                    opt_dir['db'] = arg
            elif opt in ("-t", "--table"):
                if arg != None and arg != '':
                    opt_dir['table'] = arg
            elif opt in ("-r", "--res_dir"):
                if arg != None and arg != '':
                    opt_dir['res_dir'] = arg
            elif opt in ("-r", "--res_dir"):
                if arg != None and arg != '':
                    opt_dir['res_dir'] = arg
            elif opt in ("-e", "--rep_template"):
                if arg != None and arg != '':
                    opt_dir['rep_template'] = arg
            elif opt in ("-p", "--rep_pref"):
                if arg != None and arg != '':
                    opt_dir['rep_pref'] = arg
            elif opt in ("-i", "--region_ind"):
                if arg != None and arg != '':
                   opt_dir['region_ind'] = int(arg)
        if not 'region_ind' in opt_dir:
            print(arg_help)
            sys.exit(2)
        return opt_dir
    except:
        print(arg_help)
        sys.exit(2)

def run_query(d):
    def d_dir(fn):
        full_path = os.path.realpath(__file__)
        dir_f = os.path.dirname(full_path)
        return os.path.join(dir_f, fn)
    # собираем данные из базы MS Access
    df = DBpanda.connect_odbc(d.get('db', d_dir('DKR.mdb')), d.get('table', 'dkr_table'))
    print(f"Rows count: {df.shape[0]}")
    # формирование наборов данных, используемых при построении отчета
    giz = giz_view(df)
    region_ind = d.get('region_ind', 1)  # в данной версии скрипта возможно формировать выборку только с указанием идентификатора региона
    # если будет необходимость, спискок полей первичной фильтрации наборов данных может быть расширен
    gs = giz.prepare(region_ind)
    gs = giz.source
    # построение используемых наборов аргрегатных данных
    cd1 = giz.collect_data(["region_ind", "Rayon"])
    cd2 = giz.collect_data(["Rayon", "Forma22"])
    cd3 = giz.collect_data(["region_ind"])
    cd4 = giz.collect_data(["Forma22"])
    res_dir = d.get('res_dir', d_dir(''))
    op = res_dir   # папка, куда складываются документы, генерируемые программой
    rep_template = d.get('rep_template', d_dir('template.xlsx'))
    tp = rep_template # файл-шаблон генерируемого документа
    rep_pref = d.get('rep_pref', 'gis_lands')
    tn = rep_pref # префикс имени генерируемого документа
    rm = report(tn, tp, op) # построитель отчета - документа
    rm.set_field_values({
        'dates':None,"region_id": region_ind, # список полей, которые подставляются в формируемый документ
        'Form22':None,
        'date':datetime.now().strftime('%d-%m-%Y'),
        'cd1':cd1, 'cd2':cd2, 'cd3':cd3, 'cd4':cd4}) # наборы данных, используемые при постороеним документа
    rm.run()
    

# # собираем данные из базы MS Access
# df = DBpanda.connect_odbc('C:\Dev\python\GizQuiz\db\DKR.mdb', 'dkr_table')  # Evaluation time: 39.46103763580322
# print(f"Rows count: {df.shape[0]}")
# # формирование наборов данных, используемых при построении отчета
# giz = giz_view(df)
# region_ind = 1  # в данной версии скрипта возможно формировать выборку только с указанием идентификатора региона
# # если будет необходимость, спискок полей первичной фильтрации наборов данных может быть расширен
# gs = giz.prepare(region_ind)
# gs = giz.source
# # построение используемых наборов аргрегатных данных
# cd1 = giz.collect_data(["region_ind", "Rayon"])
# cd2 = giz.collect_data(["Rayon", "Forma22"])
# cd3 = giz.collect_data(["region_ind"])
# cd4 = giz.collect_data(["Forma22"])

# op = r"C:\Dev\Задание тестовое\results"   # папка, куда складываются документы, генерируемые программой
# tp = r"C:\Dev\Задание тестовое\template.xlsx" # файл-шаблон генерируемого документа
# tn = 'gis_lands' # префикс имени генерируемого документа
# rm = report(tn, tp, op) # построитель отчета - документа
# rm.set_field_values({
#     'dates':None,"region_id": region_ind, # список полей, которые подставляются в формируемый документ
#     'Form22':None,
#     'date':datetime.now().strftime('%d-%m-%Y'),
#     'cd1':cd1, 'cd2':cd2, 'cd3':cd3, 'cd4':cd4}) # наборы данных, используемые при постороеним документа
# rm.run()

# sample call:
#           
d = get_args()
run_query(d)

end = time.time()
print(f"Evaluation time: {end - start}")
