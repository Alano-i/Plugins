#!/usr/bin/env python3
# encoding: utf-8
from component import *

class P115AutoSign:
    def __init__(self, client):
        self.client = client

    def auto_sign(self):
        result={}
        self.reason = '未知，请查看日志！'
        for i in range(3):
            try:
                print(f"开始执行签到...")
                result = self.client.user_points_sign_post()
                break
            except Exception as e:
                print(f'第 {i+1}/3 次签到时发生异常,(注意不能用web的cookie进行签到)，原因：{e}')
                self.reason = e
                time.sleep(3)
                continue
        return result

    def main(self):
        result = self.auto_sign()
        title=''
        if result.get('state', False) and result.get('code',9999) == 0:
            continuous_day = result.get('data', {}).get('continuous_day', None)
            message = f"已连续签到 {continuous_day} 天" if continuous_day else ''
            if result.get('data', {}).get('first_require_sign', None) == 1:
                print(f"签到成功！{message}")
                title="115今日签到成功"
            else:
                print(f"今天已经签过到了！{message}")
                title="115今日已经签过到了"
            if push_notify:
                wecom_notify.send_news(title=title, message=message, link_url="", pic_url=pic_url, touser=touser)
        else:
            print("签到失败！")
            print(f'result:{result}')
            if push_notify:
                wecom_notify.send_mpnews(title="115今日签到失败", message=str(self.reason), media_id = media_id, touser=touser)

if __name__ == "__main__":
    for client in clients:
        AutoSign = P115AutoSign(client)
        AutoSign.main()