from tenacity import retry, stop_after_attempt, wait_random_exponential
from config import *
import time
from p115 import P115Client
from notify_server import WeComNotify

if push_notify:        
    wecom_notify = WeComNotify(corpid=corpid, corpsecret=corpsecret, agentid=agentid, proxy_api_url=proxy_api_url)
    
cookies = cookies.split('\n')
clients = []
for cookie in cookies:
    for i in range(3):
        try:
            client = P115Client(cookie)
            clients.append(client)
            break
        except Exception as e:
            print(f'第 {i+1}/3 次构建115客户端发生异常，原因：{e}')
            if isinstance(e.args[0], dict):
                if not e.args[0].get('state', False) and e.args[0].get('errno', 99) == 99:
                    print(f'115 cookie 已失效，请重新获取')
                    if push_notify:
                        wecom_notify.send_news(title="115 cookie 已失效", message="无法检测到账号状态，请更换cookie", link_url="", pic_url=pic_url, touser=touser)
                    exit()
            time.sleep(3)
            continue