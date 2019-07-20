import re
import os
import urllib
import hashlib
import base64
import requests
import traceback

from aes import PrpCrypt
from bs4 import BeautifulSoup
from selenium import webdriver
from http.cookies import SimpleCookie
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import ChromeOptions as Options


class VideoCrawler:
    """
    a crawler to get video in newcoder
    """

    def __init__(self, path, ts_path, result_path):
        self.path = path
        self.keys = []
        self.ts_list = []
        self.ts_path = ts_path
        self.result_path = result_path
        self.headers = None
        self.m3u8 = None
        self.ts_url_list = None
        self.key_url_dealt = None
        self.iv_dealt = None
        self.video_id = None
        self.key = None
        self.iv = None

    def get(self, url):
        try:
            req = requests.get(url, self.headers)
            req.raise_for_status()
            req.encoding = req.apparent_encoding
            return req.text
        except:
            traceback.print_exc()

    def set_headers(self, referer, user_agent, cookie):
        self.headers = {"Referer": referer,
                        "User-Agent": user_agent,
                        "cookie": cookie}

    def parse_m3u8(self, m3u8):
        self.m3u8 = m3u8
        self.ts_url_list = re.findall(r'http.*\.ts', self.m3u8)
        key_url = re.findall(r'EXT-X-KEY:METHOD=AES-128,URI="http.*"', self.m3u8)[0]
        iv = re.findall(r'IV=0x.{32}', self.m3u8)[0]

        self.key = key_url[30:-1]
        self.iv = iv[5:]

    def save_ts_url(self, url):
        name = url.split("/")[-1]
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        try:
            req = requests.get(url)
            req.raise_for_status()
            filepath = self.path + os.path.sep + name
            print("download", filepath)
            if not os.path.exists(filepath):
                with open(filepath, 'wb') as f:
                    f.write(req.content)
            return req.content
        except:
            traceback.print_exc()

    @staticmethod
    def save_content(name, content, path):
        if type(content) == str:
            content = content.encode('utf-8')
        if not os.path.exists(path):
            os.makedirs(path)
        filepath = path + os.path.sep + name
        print(filepath)
        if not os.path.exists(filepath):
            with open(filepath, 'wb') as f:
                f.write(content)

    def get_body(self, video_id):
        content = self.get_content("https://player.polyv.net/secure/" + video_id + ".json")
        content = str(content)
        regex = re.compile(r'body": ".*"')
        content = regex.findall(content)[0][8:-1]
        return content

    @staticmethod
    def b(e, t=None):
        if t is None or t.lower().replace(" ", "").replace("-", "") == "utf8":
            i = []
            r = 0
            while r < len(e):
                n = ord(e[r:r + 1])
                if n == 37:
                    n = hex(int(e[r:r + 2]))
                    i.append(n)
                else:
                    i.append(n)
                r += 1
            return i
        elif t.lower() == "hex":
            i = []
            r = 0
            while r < len(e):
                n = ord(e[r:r + 1])
                n = hex(int(e[r:r + 2]))
                i.append(n)
                r += 1
            return i
        else:
            i = []
            return i

    @staticmethod
    def funa(e):
        """两位16进制转10进制"""
        t = []
        i = 0
        dic = {"0": 0,
               "1": 1,
               "2": 2,
               "3": 3,
               "4": 4,
               "5": 5,
               "6": 6,
               "7": 7,
               "8": 8,
               "9": 9,
               "a": 10,
               "b": 11,
               "c": 12,
               "d": 13,
               "e": 14,
               "f": 15}
        while i < len(e):
            a = dic[e[i]]
            b = dic[e[i + 1]]
            t.append(a * 16 + b)
            i += 2
        return t

    def decrypt_video_json(self, video_id, body):
        t = video_id
        m2 = hashlib.md5()
        m2.update(t.encode('utf-8'))
        i = m2.hexdigest()
        r = self.b(i[0:16])
        r = bytes(r)
        n = self.b(i[16:32])
        n = bytes(n)
        a = self.funa(body)
        a = bytes(a)
        pc = PrpCrypt(r, n)
        result = pc.decrypt(a)
        result = base64.b64decode(result)
        return result

    def parse_key(self, key):
        body = self.get_body(self.video_id)
        json = self.decrypt_video_json(self.video_id, body)
        json = str(json, encoding="utf8")
        regex = re.compile(r'seed_const":.*?,')
        seed_const = regex.findall(json)[0][12:-1]
        m2 = hashlib.md5()
        m2.update(seed_const.encode('utf-8'))
        i = m2.hexdigest()
        i = i[0:16]
        i = bytes(i, encoding="utf8")
        iv = [1, 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 7, 5, 3, 2, 1]
        iv = bytes(iv)
        pc = PrpCrypt(i, iv)
        key = pc.decrypt(key)[0:16]
        return key

    def get_key_request_param(self, ori_url):
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            prefs = {'profile.managed_default_content_settings.images': 2}
            chrome_options.add_experimental_option('prefs', prefs)
            browser = webdriver.Chrome(chrome_options=chrome_options)
            # browser = webdriver.Firefox()
            cookie = self.headers["cookie"]
            simple_cookie = SimpleCookie(cookie)
            browser.get(ori_url)
            format_cookie = {}
            for item in simple_cookie:
                format_cookie['name'] = item
                format_cookie['value'] = simple_cookie[item].value
                browser.add_cookie(cookie_dict=format_cookie)

            browser.get(ori_url)
            soup = BeautifulSoup(browser.page_source, "html.parser")
            titles = soup.select("body  script")
            stri = titles[-2].get_text()
            browser.close()
            regex = re.compile(r"videoId: '.*'")
            video_id = regex.findall(stri)[0][10:-1]
            regex = re.compile(r"videoPlaySafe: '.*'")
            video_play_safe = regex.findall(stri)[0][16:-1]
            return video_id, video_play_safe
        except:
            traceback.print_exc()

    def get_vid_krp(self, ori_url):
        self.video_id, key_request_param = self.get_key_request_param(ori_url)
        post_params = {
            "token": key_request_param
        }
        key_request_param = urllib.parse.urlencode(post_params)
        self.key = self.key.split(".net")[0] + ".net/playsafe" + self.key.split(".net")[1]
        self.key = self.key + "?" + key_request_param

    def get_content(self, url):
        try:
            req = requests.get(url, self.headers)
            req.raise_for_status()
            return req.content
        except:
            traceback.print_exc()

    def decoding(self):
        key_name = "key.key"
        iv_name = "iv.iv"
        video_id_name = "video_id"
        key_content = self.get_content(self.key)
        iv = self.iv
        self.save_content(key_name, key_content, self.path)
        self.save_content(iv_name, iv, self.path)
        self.save_content(video_id_name, self.video_id, self.path)
        key = self.parse_key(key_content)
        iv = [182, 225, 80, 143, 231, 211, 167, 164, 71, 64, 110, 174, 127, 230, 89, 117]
        iv = bytes(iv)

        for i in range(0, len(self.ts_url_list)):
            ts_url = self.ts_url_list[i]
            print("No", i, "file\t", ts_url)
            ts = self.save_ts_url(ts_url)
            ts_name = ts_url.split("/")[-1].split(".ts")[0] + "_convert.ts"

            # iv = a2b_hex(iv)
            pc = PrpCrypt(key, iv)
            result = pc.decrypt(ts)
            with open(self.ts_path + "\\" + ts_name, 'wb') as f:
                f.write(result)
            self.ts_list.append(result)

    def merge_ts(self):
        out_file = open(self.result_path + os.path.sep + "1.ts", "wb")

        for i in range(0, len(self.ts_list)):
            in_file = self.ts_list[i]
            out_file.write(in_file)
        out_file.close()


def main():
    url = "https://hls.videocc.net/c7d3982d0d/4/c7d3982d0d5bfeeb27a988dbcfec9d34_2.m3u8?pid=1563516640906X1000101&" \
          "device=desktop"
    referer = "https://www.nowcoder.com/study/vod/1041/1/1"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/" \
                 "75.0.3770.100 Safari/537.36"
    cookie = "NOWCODERCLINETID=7E576843AAD6A48C69C4FEC9C5D2784F; _ga=GA1.2.271210318.1552288354; NOWCODERUID=817D39" \
             "0DB96D8CAE2C9F7E1E554F6A28; gdxidpyhxdE=uGcyhoRXafAcuWdzdtT8vRBgDHVmvYC5AV82O5MCXuukixnAP%2B6pfRN3kHb" \
             "WRKlICIEDCst7Za5I6ID%2BiEcuz7b2WEaIvIg1y4y9UpkaAE%2F0MQvys%5CZdf1Y0ovff398cpGkbSwnfLZ9GL1uogPjEkQG0JM" \
             "kOHCpsr2pq8lTfOw8Jp5dI%3A1563357666843; _9755xjdesxxd_=32; t=4DDC7495990D299B219F4F01B383BA3B; gr_use" \
             "r_id=4505d2e5-9b6b-4064-a202-40e66dd0432b; c196c3667d214851b11233f5c17f99d5_gr_last_sent_cs1=11343379" \
             "0; grwng_uid=6097ead7-9a65-4d18-9b1e-2ad15975cd9b; c196c3667d214851b11233f5c17f99d5_gr_session_id=f9f" \
             "a5545-4744-4f62-98b1-a84e62b2f7aa; c196c3667d214851b11233f5c17f99d5_gr_last_sent_sid_with_cs1=f9fa554" \
             "5-4744-4f62-98b1-a84e62b2f7aa; c196c3667d214851b11233f5c17f99d5_gr_session_id_f9fa5545-4744-4f62-98b1" \
             "-a84e62b2f7aa=true; Hm_lvt_a808a1326b6c06c437de769d1b85b870=1562662728,1563152190,1563351717,15634183" \
             "06; c196c3667d214851b11233f5c17f99d5_gr_cs1=113433790; Hm_lpvt_a808a1326b6c06c437de769d1b85b870=15634" \
             "18970; SERVERID=aff739a092fc0d444b24c3a30d4864b6|1563419037|1563418307"
    ori_url = "https://www.nowcoder.com/study/vod/1041/3/1"
    save_path = "E:\\song\\m3u8\\newcoder_video\\test"
    ts_path = "E:\\song\\m3u8\\newcoder_video\\convert"
    result_path = "E:\\song\\m3u8\\newcoder_video"

    if not os.path.exists(save_path):
        os.makedirs(save_path)
    if not os.path.exists(ts_path):
        os.makedirs(ts_path)
    if not os.path.exists(result_path):
        os.makedirs(result_path)

    crawler = VideoCrawler(save_path, ts_path, result_path)
    crawler.set_headers(referer, user_agent, cookie)
    m3u8 = crawler.get(url)
    if not os.path.exists(save_path + "\\list2.m3u8"):
        with open(save_path + "\\list2.m3u8", "w") as f:
            f.write(m3u8)
    crawler.parse_m3u8(m3u8)
    crawler.get_vid_krp(ori_url)
    crawler.decoding()
    crawler.merge_ts()


if __name__ == "__main__":
    main()
