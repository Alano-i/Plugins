#!/usr/bin/env python3
# encoding: utf-8
from component import *
from p115.tool import crack_captcha

class P115AutoCrack:
    def __init__(self, client):
        self.client = client
        self.pickcode = 'x'

    def check_risk(self):
        # @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
        # def risk():
        #     print(f"开始检测风控...")
        #     return self.client.download_url_web(self.pickcode)
        # try:
        #     return risk()
        # except Exception as e:
        #     print(f"检测风控时发生异常，原因：{e}")
        #     return {}

        result={}
        print(f"开始检测风控...")
        for i in range(3):
            try:
                result = self.client.download_url_web(self.pickcode)
                break
            except Exception as e:
                print(f'第 {i+1}/3 次检测风控时发生异常，原因：{e}')
                time.sleep(3)
                continue
        return result

    def auto_crack(self):
        print("开始识别验证码验证码...")
        # @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
        def crack():
            while not crack_captcha(self.client):
                print("验证码识别失败，正在重试...")
                time.sleep(1)
        try:
            crack()
        except Exception as e:
            print(f"执行破解验证码发生异常，原因：{e}")

    def main(self):
        while True:
            crack_flag = False
            result = self.check_risk()
            if not result: return
            if not result.get('state', True) and result.get('code', 9999) == 911:
                crack_flag = True
                print("检测到风控，尝试破解验证码以解除...")
                if push_notify:
                    wecom_notify.send_news(title="115检测到风控", message="将尝试破解验证码以解除", link_url="", pic_url=pic_url, touser=touser)
                self.auto_crack()
                time.sleep(3)
                result = self.check_risk()
            if (not result.get('state', True) and result.get('msg_code', 9999) == 70005) or (result.get('state', False) and result.get('msg_code', 9999) == 0):
                if crack_flag:
                    print("解除风控成功")
                    if push_notify:
                        wecom_notify.send_news(title="115风控已解除", message="解除风控成功，账号恢复正常", link_url="", pic_url=pic_url, touser=touser)
                else:
                    print("未检测到风控")
                    if push_notify and normal_notify:
                        wecom_notify.send_news(title="115未检测到风控", message="账号正常，无风控", link_url="", pic_url=pic_url, touser=touser)
                break


if __name__ == "__main__":
    for client in clients:
        AutoCrack = P115AutoCrack(client)
        AutoCrack.main()