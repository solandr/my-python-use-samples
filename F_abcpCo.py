#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep  4 22:16:53 2022

@author: Andrew Solowey
"""
import xlrd

class AbsbCo:
    
    companies = {}

    @classmethod
    def init_data(cls, file_name):
        def ins_in(rows, main_name, aliases):
            rows[main_name] = main_name
            for alias in aliases:
                if len(alias) == 0:
                    continue
                rows[alias] = main_name
        wb = xlrd.open_workbook(file_name)
        ws = wb[0]
        inp_row_count = ws.nrows
        cols_count = 2
        rows = {}
        for row in range(2, inp_row_count):
            r = ws.row_values(row, start_colx=0, end_colx=cols_count)
            main_name = str(r[0]).upper()
            als = str(r[1]).upper()
            aliases = [x.strip(' ') for x in als.split(",")]
            ins_in(rows, main_name, aliases)
        cls.companies = rows

    @classmethod
    def get_name(cls, comp):
        if len(cls.companies) == 0:
            cls.init_data("etalon_brands.xls")
        c = comp.strip().upper() if isinstance(comp, str) else ''
        cc = cls.companies
        return cc.get(c, 'NONAME')

# etalon_brands.xls