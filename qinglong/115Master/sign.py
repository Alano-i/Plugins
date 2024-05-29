#!/usr/bin/env python3
# encoding: utf-8
from component import *

class P115AutoSign:
    def __init__(self, client):
        self.client = client

    def auto_sign(self):
        @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
        def sign():
            print(f"开始执行签到...")
            return self.client.user_points_sign_post()
        try:
            return sign()
        except Exception as e:
            print(f"签到时发生异常,(注意不能用web的cookie)，原因：{e}")
            self.reason = e
            return {}

    def main(self):
        result = self.auto_sign()
        if result.get('state', False) and result.get('code',9999) == 0:
            print("签到成功！")
            if push_notify:
                wecom_notify.send_news(title="115今日签到成功", message="", link_url="", pic_url=pic_url, touser=touser)
        else:
            print("签到失败！")
            if push_notify:
                wecom_notify.send_mpnews(title="115今日签到失败", message=str(self.reason), media_id = media_id, touser=touser)

if __name__ == "__main__":
    for client in clients:
        AutoSign = P115AutoSign(client)
        AutoSign.main()