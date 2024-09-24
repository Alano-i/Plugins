#!/usr/bin/env python3
# encoding: utf-8

import json
import requests
from config import *

class WeComNotify:
    def __init__(self, corpid, corpsecret, agentid, proxy_api_url):
        self.CORPID = corpid
        self.CORPSECRET = corpsecret
        self.AGENTID = agentid
        self.BASE_API_URL = proxy_api_url if proxy_api_url else "https://qyapi.weixin.qq.com"

    def get_access_token(self):
        if not self.CORPID or not self.CORPSECRET or not self.AGENTID:
            print("请配置企业微信通知参数")
            exit()
        url = f"{self.BASE_API_URL}/cgi-bin/gettoken"
        values = {
            "corpid": self.CORPID,
            "corpsecret": self.CORPSECRET,
        }
        req = requests.post(url, params=values)
        data = json.loads(req.text)
        return data["access_token"]

    def upload_media(self, file_path, media_type='image'):
        url = f'{self.BASE_API_URL}/cgi-bin/media/upload?access_token={self.access_token}&type={media_type}'
        with open(file_path, 'rb') as file:
            files = {'media': file}
            response = requests.post(url, files=files).json()
            if 'media_id' in response:
                print(f"上传媒体文件成功: {response['media_id']}")
                return response['media_id']
            else:
                print(f"上传媒体文件失败: {response}")
                return None

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
    def send_text(self, message, touser="@all"):
        send_url = f"{self.BASE_API_URL}/cgi-bin/message/send?access_token={self.get_access_token()}"
        send_values = {
            "touser": touser,
            "msgtype": "text",
            "agentid": self.AGENTID,
            "text": {"content": message},
            "safe": "0",
        }
        send_msges = bytes(json.dumps(send_values), "utf-8")
        respone = requests.post(send_url, send_msges)
        respone = respone.json()
        if respone['errcode'] == 0:
            print(f"微信通知发送成功")
        else:
            print(f"微信通知发送失败，原因：{respone['errmsg']}")
        return respone["errmsg"]

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
    def send_news(self, title, message, link_url, pic_url, touser="@all"):
        send_url = f"{self.BASE_API_URL}/cgi-bin/message/send?access_token={self.get_access_token()}"
        send_values = {
            "touser": touser,
            "msgtype": "news",
            "agentid": self.AGENTID,
            "news": {
                "articles": [
                    {
                        "title": title,
                        "description": message,
                        "url": link_url,
                        "picurl": pic_url,
                    }
                ]
            },
        }
        send_msges = bytes(json.dumps(send_values), "utf-8")
        respone = requests.post(send_url, send_msges)
        respone = respone.json()
        if respone['errcode'] == 0:
            print(f"微信通知发送成功")
        else:
            print(f"微信通知发送失败，原因：{respone['errmsg']}")
        return respone["errmsg"]


    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
    def send_mpnews(self, title, message, media_id, touser="@all",content='',content_source_url=''):
        send_url = f"{self.BASE_API_URL}/cgi-bin/message/send?access_token={self.get_access_token()}"
        send_values = {
            "touser": touser,
            "msgtype": "mpnews",
            "agentid": self.AGENTID,
            "mpnews": {
                "articles": [
                    {
                        "title": title,
                        "thumb_media_id": media_id,
                        "author": "115Master",
                        "content_source_url": content_source_url,
                        "content": message.replace("\n", "<br/>") if not content else content,
                        "digest": message,
                    }
                ]
            },
        }
        send_msges = bytes(json.dumps(send_values), "utf-8")
        respone = requests.post(send_url, send_msges)
        respone = respone.json()
        if respone['errcode'] == 0:
            print(f"微信通知发送成功")
        else:
            print(f"微信通知发送失败，原因：{respone['errmsg']}")
        return respone["errmsg"]

