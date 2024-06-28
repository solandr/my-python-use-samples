#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  5 20:23:57 2022

author: Andrew Solowey
"""
import re
import pytz
from datetime import datetime
import glob
import requests
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.parse import parse_qs
import os
import paramiko

class InjWork:

    base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources'
    public_key = 'https://disk.yandex.by/d/KJBj-GnrR_MD6w'
    ftmpl = r"message\s(?P<d>\d+)[\,\.,\-](?P<m>\d+)[\,\.,\-](?P<y>\d+)(\s+(?P<h>\d+)[\-:\.](?P<mm>\d+))*\.txt"
    
    @classmethod
    def get_cur_mes_file(cls):
        xlsxFiles = glob.glob('message*.txt')
        valid = re.compile(cls.ftmpl)
        utc=pytz.UTC
        last_d = utc.localize(datetime.min)
        res = None
        for f in xlsxFiles:
            match = valid.match(f)
            if match != None and len(match.groupdict()) > 2:
                d = match.group('d')
                m = match.group('m')
                y = match.group('y')

                if match.group('h') != None:
                    h = match.group('h')[0:2]
                    mm = match.group('mm')[0:2]
                    date = utc.localize(datetime.fromisoformat(f'{y}-{m}-{d} {h}:{mm}'))
                else:
                    date = utc.localize(datetime.fromisoformat(f'{y}-{m}-{d}'))

                if date > last_d:
                    res = f
                    last_d = date

        return (res, last_d)
    
    @classmethod
    def get_mes_path(cls):
        cfile, cdate = cls.get_cur_mes_file()
        
        valid = re.compile(cls.ftmpl)
        utc=pytz.UTC
        # Получаем загрузочную ссылку
        ypath = '/';
        
        yfields = '_embedded.items.name,_embedded.items.type';
         
        ylimit = 100;
        
        p1 = urlencode(dict(path=ypath))
        p2 = urlencode(dict(public_key=cls.public_key))
        final_url = f"{cls.base_url}??{p1}&{p2}&fields={yfields}&limit={ylimit}"
        
        response = requests.get(final_url)
        js = response.json()
        items = js["_embedded"]["items"]
        pk = js["_embedded"]["public_key"]
        p0 = urlencode(dict(public_key=pk))
        last_d = cdate
        res = None
        for it in items:
            if it['type'] != 'file' : continue
            it_name = it["name"]
            match = valid.match(it_name)
            if match != None and len(match.groupdict()) > 2:
                d = match.group('d')
                m = match.group('m')
                y = match.group('y')
                date = utc.localize(datetime.fromisoformat(f'{y}-{m}-{d}'))
                if date > last_d:
                    res = it_name
                    last_d = date
     
    # exists_for_real = os.path.isfile(file_path) and os.path.getsize(file_path) > 0
        
        if res == None:
            return (cfile, cdate, False)
        
        p02 = urlencode(dict(path=f'/{res}'))
        
        file_url = f"{cls.base_url}/download?{p02}&{p0}"
        response = requests.get(file_url)
        
        js = response.json()
        
        download_url = js['href']
        
        parsed_url = urlparse(download_url)
        file_name = parse_qs(parsed_url.query)['filename'][0]
        print(f"get message from file: {file_name}")
        
        file_nameR = file_name
        exists_for_real = os.path.isfile(file_nameR) and os.path.getsize(file_nameR) > 0
        
        if exists_for_real:
            return file_nameR
        
        download_response = requests.get(download_url)
        open(file_nameR, 'wb').write(download_response.content)
                    
        return file_name, last_d, True
    
    @classmethod
    def init_data(cls):
        fn, fd, need_refresh = cls.get_mes_path()
        if need_refresh:
            cls.send_sql_to_server(fn)
    
    @classmethod
    def send_sql_to_server(cls, ofile):
        host = "123.12.34.37"
        port = 52222
        username = "root"
        password = "password"
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port, username, password)
        
        sftp = ssh.open_sftp()
        basenameF = os.path.basename(ofile)
        host_mes_path = '/var/www/www-root/data/www/some_site.by/parts/info.mes'
        localpath = ofile
        sftp.put(localpath, host_mes_path)
        sftp.close()
        
        print(f'{basenameF} sended on server.')    
        
        ssh.close()
        return

# Текущий файл сообщений с именем вида message 30-03-2023.txt
# нужно полоэжить на янжекс-диск, берем оттуда для сайта.
# в локальную папку не надо ложить: оттуда смотрится текущая дата файла
# после закачки с яндекс-диска, он туда будет помещен системой
# содержимое файла - два поля (заголовок и описание)
# сожержимое полей разделено в файле знаком |
InjWork.init_data()
