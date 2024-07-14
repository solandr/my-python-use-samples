import datetime
import numpy as np
from pandas._libs.lib import is_list_like

class giz_view(object):
    def __init__(self, data_frame) -> None:
        self.source = data_frame
        data_frame['region_ind'] = data_frame['SOATO'].apply(lambda s: int(s[0]) if isinstance(s, str) else 0)
        data_frame.set_index(['region_ind'],drop=True)
        data_frame['s1'] = np.where(data_frame['SVovlech'] == 1, data_frame['Area_ga'], np.nan)
        data_frame['s2'] = np.where(data_frame['SVovlech'] == 2, data_frame['Area_ga'], np.nan)
        data_frame['s3'] = np.where(data_frame['SVovlech'] == 3, data_frame['Area_ga'], np.nan)
        data_frame['s4'] = np.where(data_frame['SVovlech'] == 4, data_frame['Area_ga'], np.nan)
        data_frame['s5'] = np.where(data_frame['SVovlech'] == 5, data_frame['Area_ga'], np.nan)
        data_frame['s6'] = np.where(data_frame['SVovlech'] == 6, data_frame['Area_ga'], np.nan)
        data_frame['s7'] = np.where(data_frame['SVovlech'] == 7, data_frame['Area_ga'], np.nan)
        data_frame['s8'] = np.where(data_frame['SVovlech'] == 8, data_frame['Area_ga'], np.nan)
        data_frame['s9'] = np.where(data_frame['SVovlech'] == 9, data_frame['Area_ga'], np.nan)
        data_frame['s0'] = np.where(data_frame['SVovlech'] == 0, data_frame['Area_ga'], np.nan)

    def prepare(self, region_ind:int, period=None, land_use_categories=None):
        self.region_ind = region_ind
        self.period = period
        self.land_use_categories = land_use_categories
        src = self.source
        d1, d2 = period if isinstance(period,  (list, tuple)) else (None, None)
        if isinstance(d1, datetime.datetime):
            q1 =  src['Data_Vvoda'].isin(period) if isinstance(d2, datetime.datetime) else src['Data_Vvoda'] >= d1
        else:
            q1 =  src['Data_Vvoda'] <= d2 if isinstance(d2, datetime.datetime) else None
        q2 = src['Forma22'].isin(land_use_categories) if isinstance(land_use_categories,  (list, tuple)) else None
        q = (src['region_ind'] == region_ind)
        if q1 != None and q2 != None:
            q = q & q1 & q2
        else:
            if q1 != None:
                q = q & q1 & q2
            else:
                if q2 != None:
                    q = q & q2
        
        if isinstance(d1, datetime.datetime):
            q1 =  'Data_Vvoda.isin(@period)' if isinstance(d2, datetime.datetime) else 'Data_Vvoda >= @d1'
        else:
            q1 =  'Data_Vvoda <= @d2' if isinstance(d2, datetime.datetime) else ''
        q2 = 'Forma22.isin(@land_use_categories)' if isinstance(land_use_categories,  (list, tuple)) else ''
        q = ('region_ind == @region_ind')
        if q1 != '' and q2 != '':
            q = q & q1 & q2
        else:
            if q1 != '':
                q = q & q1 & q2
            else:
                if q2 != '':
                    q = q & q2
         
        s1 = src.shape

        self.source = src.query(q)

        self.source.set_index(['region_ind'],drop=True)
        s2 = self.source.shape

        return self.source

    def collect_data(self, indices):
        df = self.source
        columns = ['s_sum', 's_count', 's1_sum', 's1_count', 's2_sum', 's2_count', 's3_sum', 's3_count',
                     's4_sum', 's4_count', 's5_sum', 's5_count', 's6_sum', 's6_count',
                     's7_sum', 's7_count', 's8_sum', 's8_count', 's9_sum', 's9_count']
        aggs = df.groupby(indices).agg(
            s_sum  = ('Area_ga', 'sum'), s_count  = ('Area_ga', 'count'),
            s1_sum = ('s1', 'sum'), s1_count = ('s1', 'count'),
            s2_sum = ('s2', 'sum'), s2_count = ('s2', 'count'),
            s3_sum = ('s3', 'sum'), s3_count = ('s3', 'count'),
            s4_sum = ('s4', 'sum'), s4_count = ('s4', 'count'),
            s5_sum = ('s5', 'sum'), s5_count = ('s5', 'count'),
            s6_sum = ('s6', 'sum'), s6_count = ('s6', 'count'),
            s7_sum = ('s7', 'sum'), s7_count = ('s7', 'count'),
            s8_sum = ('s8', 'sum'), s8_count = ('s8', 'count'),
            s9_sum = ('s9', 'sum'), s9_count = ('s9', 'count'),
            s0_sum = ('s0', 'sum'), s0_count = ('s0', 'count'))
        return aggs[columns]
