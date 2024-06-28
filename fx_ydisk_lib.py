#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 30 15:07:05 2022

@author: Andrew Solowey
"""

import requests
from os.path import exists
from PIL import Image # $ pip install pillow
try:
    from PIL.Image.Resampling import LANCZOS
except ModuleNotFoundError: # for pre 2023 versions of PIL
    import warnings
    with warnings.catch_warnings():
        from PIL.Image import LANCZOS

def depricated(a):
    dl = ("ARW-AV-02", "AT-02", "САИ 250", "САИ 190", "САИ 160")
    return a in dl

class FYD:
    URL = r'https://cloud-api.yandex.net/v1/disk/resources'
    TOKEN = r'AQAEA_some_user_ap_token_0L0k'   # different for yandex users
    # get it with url:
    # https://oauth.yandex.ru/authorize?response_type=token&client_id=f67cebfcAAAAAAAda39623c0671
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth {TOKEN}'}
    
    SOURCE_DIR = r"/home/andrew/delme/"
    TARGET_DIR = r"F-ки/spec/"
    PICS_DIR = r"ФОТО/"
    PICS_LOCAL_PATH = r"/media/andrew/My Passport/from seagate/our_site.by/Foto/tar/F0"
    
    watermark = None
    wm_sz = 0
    
    def get_items(path, what):   # what = file|dir
        js = requests.get(f'{FYD.URL}?path={path}&limit=-1', headers=FYD.headers).json()
        items = js["_embedded"]["items"]
        its = []
        for it in items:
            if it['type'] == what :
                its.append(it["name"])
        return its
    
    def create_dir(dir_name):
        print(f"create_dir: /{dir_name}")
        response = requests.put(f'{FYD.URL}?path={dir_name}', headers=FYD.headers)
        if response.status_code >= 200 and response.status_code < 300:
            print("Created. Yes.")
            return True
        else:
            print("Unsuccesfully. No.")
            return False
        
    def upload_file(loadfile, savefile, replace=False):
        """Загрузка файла.
        savefile: Путь к файлу на Диске
        loadfile: Путь к загружаемому файлу
        replace: true or false Замена файла на Диске"""
        print(f"upload_file: {loadfile}\nto Yandex-disk file\n{savefile}")
        res = requests.get(f'{FYD.URL}/upload?path={savefile}&overwrite={replace}', headers=FYD.headers).json()
        with open(loadfile, 'rb') as f:
            try:
                requests.put(res['href'], files={'file':f})
                print("uploaded.")
            except KeyError:
                print(res)
                
    def dir_exist(path, dir_name):
        its = FYD.get_items(path, 'dir')
        return dir_name in its
                
    def run(seller, file_name):
        main_dir = FYD.TARGET_DIR
        dir_name = seller
        exist_d = FYD.dir_exist(main_dir, dir_name)
        if exist_d:
            print(f"{dir_name} exist.")
        else:
            print(f"{dir_name} not exist.")
            FYD.create_dir(f"{main_dir}{dir_name}")
        FYD.get_items(fr"{main_dir}{dir_name}", "dir")
         FYD.upload_file(fr"{FYD.SOURCE_DIR}{seller}/{file_name}", fr"{main_dir}{dir_name}/{file_name}", True)
                
    def run1(seller, file_name, main_dir = TARGET_DIR, subdir = ""):
        subdir = seller if subdir == "" else subdir
        exist_d = FYD.dir_exist(main_dir, subdir)
        if exist_d:
            print(f"{subdir} exist.")
        else:
            print(f"{subdir} not exist.")
            FYD.create_dir(f"{main_dir}{subdir}")
        FYD.upload_file(fr"{FYD.SOURCE_DIR}{seller}/{file_name}", fr"{main_dir}{subdir}/{file_name}", True)
        
    @classmethod
    def get_new_pics(cls, pic_path = PICS_LOCAL_PATH, remove_ext = True):
        js = requests.get(f'{FYD.URL}?path={FYD.PICS_DIR}&limit=-1', headers=FYD.headers).json()
        items = js["_embedded"]["items"]
        its = {}
        for it in items:
            if it['type'] == 'file' and it['media_type'] == 'image' :
                pic = it["name"].lower().split('.')[0] if remove_ext else it["name"]
                if not cls.have_image(pic, pic_path, remove_ext):
                    its[pic] = it["file"]
        return its        
        
    @staticmethod
    def image_path(fileName, path, remove_ext = True):
        if remove_ext:
            return f"{path}/{fileName}.jpg" if not path.endswith("/") else f"{path}{fileName}.jpg"
        else:
            return f"{path}/{fileName}" if not path.endswith("/") else f"{path}{fileName}"

    @classmethod
    def have_image(cls, fileName, path, remove_ext = True):
        file_path = cls.image_path(fileName, path, remove_ext)
        return exists(file_path)
    
    @classmethod
    def downlod_pics(cls, pics):
        with requests.Session() as session:
            for pic_name, pic_path in pics.items():
                file_tar = cls.image_path(pic_name, cls.PICS_LOCAL_PATH)
                cls.load_picture(pic_path, file_tar, pic_name, session)
        return

    @classmethod
    def load_picture(cls, pic_url, pic_path_tar, pic_name, session):
        def make_transparent(img):
            rgba = img.convert("RGBA")
            datas = rgba.getdata()
            newData = []
            for item in datas:
                if item[0] == 0 and item[1] == 0 and item[2] == 0:  # finding black colour by its RGB value
                    # storing a transparent value when we find a black colour
                    newData.append((255, 255, 255, 0))
                else:
                    newData.append(item)  # other colours remain unchanged
              
            rgba.putdata(newData)
            return rgba
        try:
            print(f'load_picture. request: {pic_name}')
            r = session.get(pic_url, headers={'User-agent': 'Mozilla/5.0'},
                            stream=True, timeout=10)
            if r.status_code == 200:
                r.raw.decode_content = True # Content-Encoding
                with Image.open(r.raw) as im: #NOTE: it requires pillow 2.8+
                    if cls.watermark == None:
                        cls.watermark = make_transparent(Image.open("StampReady.png"))
                        cls.wm_sz = cls.watermark.size
                    color = im.getpixel((0, 0))
                    wm_sz = cls.wm_sz
                    watermark = cls.watermark
                    with Image.new(im.mode, wm_sz, color) as wp:
                        im.thumbnail(wm_sz)
                        x0, y0 = wm_sz
                        x, y = im.size
                        scale = min(float(x0)/x, float(y0)/y)
                        with im.resize((int(scale*x),int(scale*y)), LANCZOS) as resized_im:
                            wp.paste(resized_im, (1, 1))
                            resized_im.close()
                        wp.paste(watermark, (0, 0), watermark)                        
                        with wp.convert('RGB') as ci:
                            ci.save(pic_path_tar)
                            print('load_picture. saved: OK')
                            ci.close()
                        wp.close()
                    return True
            else:
                print(f'load_picture. No. status code: {r.status_code}')
        except Exception as exc:
            print(f'load_picture. Error: {str(exc)}')
        return False


