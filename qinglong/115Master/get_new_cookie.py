#!/usr/bin/env python3
# encoding: utf-8

from component import *
from p115.tool import login_scan_cookie
from qinglong_api import QinglongApi

# apps = {web,ios,115ios,android,115android,115ipad,tv,qandroid,windows,mac,linux,wechatmini,alipaymini}

if __name__ == "__main__":
    APP_115 = os.getenv('app_115')

    # 🔥火种源cookie
    cookie = os.getenv('cookie_fire')

    if not cookie or not APP_115:
        raise Exception('请设置【cookie_fire】和【app_115】环境变量')

    new_cookie = login_scan_cookie(cookie, app=APP_115)

    if new_cookie:
        new_envs = [{
            'name': 'cookie_115',
            'value': new_cookie,
            'remarks': '115 cookie',
        }]
        QinglongApi().update_envs(new_envs)
        print(f'更新cookie成功\n新cookie: {new_cookie}')
        if push_notify:
            wecom_notify.send_mpnews(title = f"更新【{APP_115}】新cookie成功", message = new_cookie, media_id = media_id, touser = touser)
    else:
        print('获取新cookie失败')