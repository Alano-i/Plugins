#!/usr/bin/env python3
# encoding: utf-8
import os
from tenacity import retry, stop_after_attempt, wait_random_exponential

cookies = os.getenv('cookie_115')
touser = os.getenv('touser', '@all')
corpid = os.getenv('corpid')
corpsecret = os.getenv('corpsecret')
agentid = os.getenv('agentid')
pic_url = os.getenv('pic_url_115') or 'https://raw.githubusercontent.com/Alano-i/Plugins/main/MR-Plugins/115_tools/logo.jpg'
media_id = os.getenv('media_id_115')
del_root_id = os.getenv('del_root_id')
proxy_api_url = os.getenv('wecom_proxy_api_url')
push_notify = os.environ.get('push_notify_115', 'True').lower() in ['true', '1', 'on', 'yes']
normal_notify = os.environ.get('normal_notify_115', '关掉,不准通知').lower() in ['true', '1', 'on', 'yes']




