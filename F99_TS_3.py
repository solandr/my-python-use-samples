#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests

from urllib.parse import quote_plus as up_quote_plus
from Fscl import Fdi, Fhlp
import time
from sys import exit
from datetime import datetime

comp_dict, tp_dict, mrj_dict, v_list = Fdi.get("F99")

BASE_URL = 'https://opt.minsk-lada.by'
AUTH_URL = BASE_URL + '/auth'

session = requests.Session()

session.auth = ('user_name@minsk-lada.by', 'password')

file_url = BASE_URL
resp = session.get(file_url, stream=True, verify=True)
kod_name = "код"
qt_name = "количество"
pr_name = "цена по предоплате"
sc_name = "штрих-код"
dat_name = "дата поставки"
imp_name = "признак импорта (импорт=1)"
mnf_name = "изготовитель"
br_name = "бренд"
cat_name = "категория наименование"
n_name = "наименование"
opr_name = "наша цена"

    
def norm_mnf(inp_mnf):
    return comp_dict.get(inp_mnf, "LADA")
    
def our_cat(cat):
    return tp_dict.get(cat, "пр")
    
def our_marj(pr, dv): # dv - default percent; pr - price
    rv = dv
    for (k, v) in v_list:
        if ((k >= pr) or (k < 0)):
            rv = v
            break
    return pr * (1 + rv)

def max_k1(inds):
    v = -1
    for (kp, k) in inds:
        if kp > v:
            v = kp
    return v

def res_row(cols, indsP, apd, indsA):
    
    i1 = max_k1(indsP)
    i2 = max_k1(indsA)
    i = i1 if i1 > i2 else i2
    vals = [None]*(i + 1)
    
    for (kP, k) in indsP:
        if (kP < 0) or (k < 0):
            continue
        vals[kP] = cols[k]

    for (kP, k) in indsA:
        if (kP < 0) or (k < 0):
            continue
        vals[kP] = apd[k]
        
    return vals

def prep_ts_data(rows, dn, ind_dat, ind_kod, ind_br):
    rd = {}
    dni = dn.items()
    for cols in rows:
        shipment_date = cols[ind_dat]
        shipment_dict = rd.get(shipment_date, None)
        if (shipment_dict == None):
            shipment_dict = {}
            rd[shipment_date] = shipment_dict
        articule = cols[ind_kod]
        good_row = {}
        for (k, v) in dni:
            if v != ind_br:
                good_row[k] = cols[v]
            else:
                good_row[k] = "LADA"
        shipment_dict[articule] = good_row
    return rd

# def build_positions_string(ddv):
#     ind = 0
#     buf = []
#     for kvs in ddv:
#         pd = f"positions[{ind}][{{k}}]={{v}}"
#         bpd = []
#         for k, v in kvs.items():
#             bpd.append(pd.format(k = k, v = up_quote_plus(f"{v}")))
#         bpdstr = "&".join(bpd)
#         buf.append(bpdstr)
#         ind += 1
#     return "&".join(buf)

def delete_priemki(query_args, id_list):
    (cp_username, token, headers) = query_args
    private_url = "https://abcpUSER_ID.public.api.abcp.ru/cp/ts/goodReceipts/delete"
    pref = f"userlogin={cp_username}&userpsw={token}&id={{id}}"
    def del_acc(status, isDelete, id):
        if isDelete:
            return
        if status == 3:
            change_priemka_status(query_args, id, 2, status)
        q = pref.format(id = id)
        post_response = requests.post(private_url, data = q, headers=headers)
        # time.sleep(0.01)
        post_response.json()
    if len(id_list) == 0:
        return
    el = id_list[0]
    if len(el) == 3:
        for id, status, isDelete in id_list:
            del_acc(status, isDelete, id)
    else:
        for id, status, isDelete, buyAmount in id_list:
            del_acc(status, isDelete, id)
        
        
def delete_position(query_args, id_pos):
    (cp_username, token, headers) = query_args
    private_url = "https://abcpUSER_ID.public.api.abcp.ru/cp/ts/goodReceipts/deletePosition"
    q = f"userlogin={cp_username}&userpsw={token}&id={id_pos}"
    post_response = requests.post(private_url, data = q, headers=headers)
    # time.sleep(0.01)
    post_response.json()
    # get_response_json = post_response.json()
    # print(get_response_json)
        
def get_priemki_ids(query_args, statuses="2,3", output = None):
    print("Collect ids of sepaeated acceptances")
    (cp_username, token, headers) = query_args
    private_url = "https://abcpUSER_ID.public.api.abcp.ru/cp/ts/goodReceipts/get"
    limit = 1000
    skip = 0
    params = {'userlogin':cp_username, 'userpsw': token, 'limit': limit, 'statuses':statuses}
    if output != None:
        params['output'] = output
    sw = True
    res = []
    while sw:
        params["skip"] = skip
        get_response = requests.get(private_url, params = params, headers=headers)
        # time.sleep(0.01)
        get_response_json = get_response.json()
        # print(get_response_json)
        lst = [(it['id'], it['status'], it['isDelete']) for it in get_response_json['list']] \
            if output == None else \
                [(it['id'], it['status'], it['isDelete'], it['buyAmount']) for it in get_response_json['list']]
        res.extend(lst)
        if len(lst) < limit:
            sw = False
        else:
            skip += limit
    res.sort()
    print(f"Collected ids of sepaeated acceptances count {len(res)}")
    return res

def send_to_our_site(priemka):
    private_url = "https://abcpUSER_ID.public.api.abcp.ru/cp/ts/goodReceipts/create"
    cp_username = "api@abcpUSER_ID"
    token = "some_app_token"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    pref = f"userlogin={cp_username}&userpsw={token}&supplierId=8145723"
    query_args = (cp_username, token, headers)
    priemka_cleaner(query_args)
    # count = len(priemka)
    ind = 1
    print("загрузка текущей приемки")
    for td, dd in priemka.items():
        # print(f"priemka {ind} from {count} date: {td}")
        ind += 1
        if len(dd) == 0:
            # print(f"nothing for priemka {ind} from {count} date: {td}")
            continue
        ddv = list(dd.values())
        # positions = build_positions_string(ddv)
        positions = build_acc_positions_string(ddv)
        td_str = td.strftime('%Y-%m-%d+%H%%3A%M%%3A%S')
        q = f"{pref}&supShipmentDate={td_str}&createDate={td_str}&{positions}"
        post_response = requests.post(private_url, data = q, headers=headers)
        # time.sleep(0.01)
        post_response_json = post_response.json()
        id_pr = post_response_json.get('id', 'error')
        if id_pr != 'error':
            # print(f"send_to_our_site: priemka {id_pr}")
            # # logging.info(f"send_to_our_site: priemka {id_pr}")
            change_priemka_status(query_args, id_pr, 2, -1)
            change_priemka_status(query_args, id_pr, 3, 2)
        else:
            print(f"send_to_our_site: {post_response_json}")
            print(f"send_to_our_site: {ddv}")
            # logging.info(f"send_to_our_site: priemka {post_response_json}")
        
def change_priemka_status(query_args, id, status, prev_status):
    (cp_username, token, headers) = query_args
    private_url = "https://abcpUSER_ID.public.api.abcp.ru/cp/ts/goodReceipts/changeStatus"
    q = f"userlogin={cp_username}&userpsw={token}&id={id}&status={status}"
    sw = True
    step = 0
    while sw:
        post_response = requests.post(private_url, data = q, headers=headers)
        # time.sleep(0.01)
        post_response_json = post_response.json()
        res = post_response_json.get('createdItems', 'error')
        if res == 'error':
            if step < 10:
                sw = True
                step += 1
                time.sleep(step)
            else:
                print(f"change_priemka_status of {id} from {prev_status} to {status}: {post_response_json}")
                sw = False
        else:
            sw = False
        
def priemka_cleaner(query_args):
    ids = get_priemki_ids(query_args)
    n = len(ids)
    if n > 0:
        print("очистка прошлой приемки")
        delete_priemki(query_args, ids)

def finish_acceptances(query_args):
    print("Завершение приемки.")
    id_list = get_priemki_ids(query_args, statuses = "1,2,3", output = 's')
    ids_to_del = [el for el in id_list if el[3] == 0]
    print("Очистка пустых приемок.")
    delete_priemki(query_args, ids_to_del)
    id_list = get_priemki_ids(query_args, statuses = "2")
    print("Установка статусов завершения для приемок в работе.")
    for id, status, isDelete in id_list:
        if isDelete:
            continue
        change_priemka_status(query_args, id, 3, status)
    id_list = get_priemki_ids(query_args, statuses = "1")
    print("Установка статусов завершения для вновь созданных приемок.")
    for id, status, isDelete in id_list:
        if isDelete:
            continue
        change_priemka_status(query_args, id, 2, status)
        change_priemka_status(query_args, id, 3, 2)
        
def test_start():
    cp_username = "api@abcpUSER_ID"
    token = "some_app_token"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    query_args = (cp_username, token, headers)
    ids = get_priemki_ids(query_args)
    # print(ids)
    delete_priemki(query_args, ids)
    exit()

def test_pos_works():
    t_start = time.time()
    cp_username = "api@abcpUSER_ID"
    token = "some_app_token"
    headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
    query_args = (cp_username, token, headers)

    file_x, date_value = Fhlp.get_last_file("F99", "F99_ext_(", "F99", "xlsx", 2)
    if file_x != None:
        print(f"Get file content. File: {file_x}, Date:{date_value}")
        print(f"Time start: {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}")
        # priemki = Fhlp.get_xlsx_content(file_x, brand_subst="LADA")
        priemki = Fhlp.get_xlsx_content(file_x)

        id_list = get_priemki_ids(query_args)
        for id, status, isDelete in id_list:
            if isDelete:
                continue
            if status == 3:
                change_priemka_status(query_args, id, 2, status)
            update_acceprance_positions(query_args, priemki, id)
        insert_new_goods(query_args, priemki)
        finish_acceptances(query_args)
        
    t_end = time.time()
    t = time.strftime("%H:%M:%S", time.gmtime(t_end - t_start))
    
    print(f"Evaluation time: {t}")
    print(f"Finish time: {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}")
    exit()
    
def insert_new_goods(query_args, priemki):
    sw = True
    acceptances = []
    max_acc_size = 500
    while sw:
        new_acceptance = []
        sw = False
        for key in priemki:
            el = priemki[key]
            for it_key in el:
                it = el[it_key]
                acPos = it
                if acPos.updated: # check updated
                    continue
                # articule = it.position['number']
                # if articule == "8450007313":
                #     print(f"insert_new_goods: key = '{key}'; it_key = '{it_key}'\n" )
                new_acceptance.append(acPos)
                # break # only one position with the same key must be present in one acceptance
            if len(new_acceptance) > max_acc_size:
                acceptances.append(new_acceptance)
                new_acceptance = []
        if len(new_acceptance) > 0:
            acceptances.append(new_acceptance)
        else:
            sw = False
            
    for acp in acceptances:
        send_acc_pos_to_our_site(query_args, acp)
    return

def get_priemki_positions(query_args, opId):
    (cp_username, token, headers) = query_args
    private_url = "https://abcpUSER_ID.public.api.abcp.ru/cp/ts/goodReceipts/getPositions"
    limit = 25
    params = {'userlogin':cp_username, 'userpsw': token, 'limit': limit, 'opId':opId, 'output':'e'}
    sw = True
    skip = 0
    res = []
    while sw:
        params["skip"] = skip
        step = 0
        sw_r = True
        list_json = {}
        while sw_r:
            get_response = requests.get(private_url, params = params, headers=headers)
            # time.sleep(0.1)
            response_json = get_response.json()
            list_json = response_json.get('list', 'error')
            if list_json == 'error':
                print(f"get_priemki_positions of {opId}: {response_json}\nparams:{params}")
                if step < 10:
                    step += 1
                    sw_r = True
                    time.sleep(step)
                else:
                    # print(f"get_priemki_positions of {opId}: {response_json}\nparams:{params}")
                    sw_r = False
                    exit()
            else:
                sw_r = False
        # print(get_response_json)
        lst = [{'id': it['id'], 'productId': it['productId'],
                'quantity': it['quantity'],
                'sellPrice': it['sellPrice'],
                'supBuyPrice': it['supBuyPrice'],
                'buyPrice': it['buyPrice'],
                'manufacturerCountry': it['manufacturerCountry'],
                'product': it['product'],
                'attrs': it['attrs']} for it in list_json]
        res.extend(lst)
        if len(lst) < limit:
            sw = False
        else:
            skip += limit
    return res

def get_from_priemki(pos, priemki):
    prod = pos['product']
    barcodes = set(pos['attrs']['barcodes'].split(" "))
    # articule = prod['numberFix'] #removed slashes
    # print(f"get_from_priemki: numberFix = '{articule}'; number = '{prod['number']}'\n" )
    articule = prod['number']
    brand = prod['brand']
    key = Fhlp.get_row_key(brand, articule)
    if key in priemki:
        el = priemki[key]
        for it_key in el:
            it = el[it_key]
            # if articule == "8450007313":
            #     print(f"get_from_priemki (before update check): key = '{key}'; it_key = '{it_key}'\n" )
            if it.updated: # check updated
                continue
            bcs = it.position["barcodes"]
            # if articule == "8450007313":
            #     print(f"get_from_priemki: key = '{key}'; it_key = '{it_key}'\n" )
            if (len(bcs.intersection(barcodes)) > 0):
                # if articule == "8450007313":
                #     print(f"get_from_priemki (intersection): key = '{key}'; it_key = '{it_key}'\n" )
                #     print(f"get_from_priemki (intersection YES): barcodes = '{barcodes}'; bcs = '{bcs}'\n" )
                return key, it
            # else:
            #     if articule == "8450007313":
            #         print(f"get_from_priemki (intersection NO): barcodes = '{barcodes}'; bcs = '{bcs}'\n" )
                
    return None

def need_update(pos, pos_info):
    np = pos_info[1].position
    return (pos['quantity'] != np['quantity']) or (pos['supBuyPrice'] != np['supBuyPrice'])
def update_pos(query_args, pos, pos_info):
    private_url = "https://abcpUSER_ID.public.api.abcp.ru/cp/ts/goodReceipts/updatePosition"
    (cp_username, token, headers) = query_args
    np = pos_info[1].position
    q =f"userlogin='{cp_username}'&userpsw='{token}'&brand='{up_quote_plus(np['brand'])}'&number='{np['number']}'&quantity='{np['quantity']}'&supBuyPrice='{np['supBuyPrice']}'&barcodes='{up_quote_plus(' '.join(np['barcodes']))}'&descr='{up_quote_plus(np['descr'])}'"
    
    try:
        requests.post(private_url, data = q, headers=headers)
    except UnicodeEncodeError:
        print(f"update_pos: try decode from latin1: {np['descr']}")
        descr = up_quote_plus(np['descr'], encoding='utf-8')
        print(f"update_pos: try decode result: '{descr}'")
        # descr = codecs.decode(np['descr'].encode('cp1251'), 'utf8')
        # descr = np['descr'].encode('cp1251').decode('utf8', errors='ignore')
        q =f"userlogin='{cp_username}'&userpsw='{token}'&brand='{up_quote_plus(np['brand'])}'&number='{np['number']}'&quantity='{np['quantity']}'&supBuyPrice='{np['supBuyPrice']}'&barcodes='{up_quote_plus(' '.join(np['barcodes']))}'&descr='{descr}'"
        time.sleep(1)
        requests.post(private_url, data = q.encode(), headers=headers)
    # post_response = requests.post(private_url, data = q, headers=headers)
    # get_response_json = post_response.json()
    pos_info[1].updated = True # mark as updated
    # print(get_response_json)

def update_positions(query_args, pps, priemki):
    for pos in pps:
        # if pos['id'] == 782330:
        #     x = True
        pos_info = get_from_priemki(pos, priemki)
        if pos_info == None:
            delete_position(query_args, pos['id'])
        else:
            if need_update(pos, pos_info):
                update_pos(query_args, pos, pos_info)
            else:
                pos_info[1].updated = True
    
def update_acceprance_positions(query_args, priemki, opId):
    # print(f"Update acceprance positions: acceptance id = {id}")
    pps = get_priemki_positions(query_args, opId)
    # print(f"Update acceprance positions count: {len(pps)}")
    update_positions(query_args, pps, priemki)
    # print(f"Updated acceprance positions count: {len(new_pos_list)}")
    return pps

def build_acc_positions_string(lst):
    ind = 0
    buf = []
    for accPos in lst:
        pd = f"positions[{ind}][{{k}}]={{v}}"
        bpd = []
        for k in accPos.position:
            v = accPos.position[k]
            if isinstance(v, set):
                v = " ".join(v)
            bpd.append(pd.format(k = k, v = up_quote_plus(f"{v}")))
        bpdstr = "&".join(bpd)
        buf.append(bpdstr)
        ind += 1
    return "&".join(buf)

def send_acc_pos_to_our_site(query_args, lst):
    private_url = "https://abcpUSER_ID.public.api.abcp.ru/cp/ts/goodReceipts/create"
    (cp_username, token, headers) = query_args
    pref = f"userlogin={cp_username}&userpsw={token}&supplierId=8145723"
    query_args = (cp_username, token, headers)
    # print(f"send_acc_pos_to_our_site: crearte acceptance with {len(lst)} positions.")
    positions = build_acc_positions_string(lst)
    td_str = datetime.today().strftime('%Y-%m-%d+%H%%3A%M%%3A%S')
    q = f"{pref}&supShipmentDate={td_str}&createDate={td_str}&{positions}"
    # print(f"send_acc_pos_to_our_site: q = {q}")
    post_response = requests.post(private_url, data = q, headers=headers)
    # time.sleep(0.01)
    post_response_json = post_response.json()
    id_pr = post_response_json.get('id', 'error')
    # if id_pr == 'error':
    #     print(f"send_to_our_site: {post_response_json}")
    # post_response = requests.post(private_url, data = q, headers=headers, timeout=150)
    if id_pr != 'error':
        # print(f"send_to_our_site: priemka {id_pr}")
        # # logging.info(f"send_to_our_site: priemka {id_pr}")
        change_priemka_status(query_args, id_pr, 2, -1)
        # change_priemka_status(query_args, id_pr, 3)
    else:
        print(f"send_to_our_site: {post_response_json}")

# test_start()
test_pos_works()

# start_time = time.time()

# file_x, date_value = Fhlp.get_last_file("F99", "F99_ext_(", "F99", "xlsx", 2)
# if file_x != None:
#     priemka = Fhlp.get_xlsx_content(file_x, brand_subst="LADA")
#     send_to_our_site(priemka)
    
# end_time = time.time()
# print(f"Evaluation time: {end_time - start_time}")

