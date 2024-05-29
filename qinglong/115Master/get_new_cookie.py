#!/usr/bin/env python3
# encoding: utf-8

from component import *
from p115.tool import login_scan_cookie

new_cookie = login_scan_cookie(cookie, app="qandroid")

# client = P115Client(login_app='web')
print(f'新cookie: {new_cookie}')
if push_notify:
    wecom_notify.send_mpnews(title = "获取新cookie成功", message = new_cookie, media_id = media_id, touser = touser)