#!/usr/bin/env python3
import os
import requests
import re
import time
import json
from mbot.core.plugins import plugin
from mbot.core.plugins import PluginContext, PluginMeta
from mbot.openapi import mbot_api
from typing import Dict, Any
from flask import Blueprint, request
from mbot.common.flaskutils import api_result
from mbot.register.controller_register import login_required
import logging
import datetime

loger = logging.getLogger(__name__)
server = mbot_api
plugins_name = '「通知服务器」'
plugins_path = '/data/plugins/notify_server'

def config_setup(config):
    global message_to_uid, channels
    message_to_uid = config.get('uid', '')
    channels = [config.get(f'channel_{channel_num}', '') for channel_num in range(10)]
    for channel_num, channel in enumerate(channels):
        if channel:
            loger.info(f"{plugins_name}通道 - {channel_num} 已切换通知通道至 ['{channel}']")
        else:
            loger.warning(f'{plugins_name}通道 - {channel_num} 未设置通道')
    if not message_to_uid:
        loger.error(f'{plugins_name}获取推送用户失败，可能是设置了没保存成功或者还未设置')

@plugin.after_setup
def after_setup(plugin_meta: PluginMeta, config: Dict[str, Any]):
    config_setup(config)

@plugin.config_changed
def config_changed(config: Dict[str, Any]):
    config_setup(config)

notify_server_post = Blueprint('notify_server', __name__)
"""
把flask blueprint注册到容器
这个URL访问完整的前缀是 /api/plugins/你设置的前缀
api 请求 url = 'http://localhost:1329/api/plugins/notify_server'
"""
plugin.register_blueprint('notify_server', notify_server_post)

# @notify_server_post.route('/push_msg', methods=['POST', 'GET'])
@notify_server_post.route('', methods=['POST', 'GET'])
@login_required() # 接口access_key鉴权
def notify_server():
    # loger.error(f'request：{request}')
    try:
        notify_data = request.json
    except Exception as e:
        loger.error(f'解析 JSON 数据失败，原因：{e}')
        notify_data = ''
    loger.info(f'原始 notify_data:{notify_data}')
    channel_id, title, description, pic_url, link_url = 0, '', '', '', ''
    try:
        msg_data = notify_data['msg_data']
        channel_id = notify_data['channel_id']
    except Exception as e:
        # 解析uptime
        if 'monitor' in notify_data:
            channel_id = request.args.get('channel_id', notify_data.get('channel_id', request.form.get('channel_id', 0)))
            msg = notify_data.get('msg')
            if "Testing" not in msg:
                name = notify_data.get('monitor', {}).get('name') 
                url = notify_data.get('monitor', {}).get('url')
                status = notify_data.get('heartbeat', {}).get('status')
                time_str = notify_data.get('heartbeat', {}).get('time')
                msg_dsc = notify_data.get('heartbeat', {}).get('msg')
                now_time = get_time(time_str)
                status_text = '上线了' if status else '掉线了'
                msg_dsc = '' if status else f"\n原因：{msg_dsc}"
                title = f"{name} {status_text}"
                description = f"时间：{now_time}\n地址：{url}{msg_dsc}"
                pic_url = ''
                link_url = url
            else:
                title = 'UPtime 网络监控消息测试'
                description = '消息成功推送'

        else:
            # 解析群晖发送的请求
            channel_id = request.args.get('channel_id', notify_data.get('channel_id', request.form.get('channel_id', 0)))
            title = request.args.get('title', notify_data.get('title', request.form.get('title')))
            description = request.args.get('description', notify_data.get('description', request.form.get('description')))
            if description:
                description = description.replace('\\n', '\n')
            pic_url = request.args.get('pic_url', notify_data.get('pic_url', request.form.get('pic_url')))
            link_url = request.args.get('link_url', notify_data.get('link_url', request.form.get('link_url')))
            # Watchtower发送的请求
            if not description:
                message = request.args.get('message', notify_data.get('message', request.form.get('message',))) or ''
                if 'Found new' in message:
                    try:
                        formatted_new, count = extract_and_format_new_images(message)
                        title = f"{count} 个镜像已更新"
                        description = formatted_new
                        try:
                            if 'xiaoyaliu/alist' in description:
                                loger.info(f"{plugins_name}获取到小雅镜像更新了，重置缓存数据版本号")
                                server.common.set_cache('xiaoya_data_version', 'running_version', '' )
                        except Exception as e:
                            loger.error(f"{plugins_name}获取到小雅镜像更新了，重置缓存数据版本号失败，原因：{e}")
                    except Exception as e:
                        loger.error(f"{plugins_name}提取 Watchtower 通知参数出错，原因：{e}")
                        description = message
                else:
                    description = message
                    title = 'Watchtower 自动更新 Docker 启动'

        notify_data = {
            'channel_id': channel_id,
            'msg_data': {
                'title': title,
                'a': description,
                'pic_url': pic_url,
                'link_url': link_url
            }
        }
    loger.info(f'{plugins_name}接收到通知数据 notify_data: {notify_data}')
    try:
        msg_data = notify_data['msg_data']
        channel_id = notify_data['channel_id']
        channel = channels[int(channel_id)]
    except Exception as e:
        loger.info(f"{plugins_name}获取通知数据失败，原因：{e}")
        code = 1
        result = {'state':'失败', 'reason':e}
        return api_result(code=code, message=result, data=notify_data)
    try:
        if message_to_uid:
            for _ in message_to_uid:
                server.notify.send_message_by_tmpl('{{title}}', '{{a}}', msg_data, to_uid=_, to_channel_name = channel)
        else:
            server.notify.send_message_by_tmpl('{{title}}', '{{a}}', msg_data)
        loger.info(f"{plugins_name}已推送消息")
        result = {'state':'成功'}
        code = 0
    except Exception as e:
        loger.error(f'{plugins_name}推送消息异常，原因: {e}')
        code = 1
        result = {'state':'失败', 'reason':e}
    return api_result(code=code, message=result, data=notify_data)

def get_time(time_str):
    date_pattern = re.compile(r'\d{1,4}-\d{1,2}-\d{1,2}')
    time_pattern = re.compile(r'\d{1,2}:\d{1,2}:\d{1,2}')
    date_match = date_pattern.search(time_str)
    time_match = time_pattern.search(time_str)
    date = date_match.group()
    time = time_match.group()
    full_time = f"{date} {time}"
    utc_time = datetime.datetime.strptime(full_time, '%Y-%m-%d %H:%M:%S')
    beijing_time = utc_time + datetime.timedelta(hours=8)
    beijing_time_str = beijing_time.strftime('%Y-%m-%d %H:%M:%S')
    return beijing_time_str

def extract_and_format_new_images(message):
    # Use regex to find all "Found new ..." patterns in the message
    matches = re.findall(r"Found new (.+?):(.+?) image", message)
    # Convert each match to the desired format
    formatted_images = [f"• {match[0].strip()}:{match[1].strip()}" for match in matches]
    # Join the matches into a single string
    formatted_message = '\n'.join(formatted_images)
    # Return the formatted message and the count of updated images
    return formatted_message, len(formatted_images)

# notify_data = {
#     'channel_id': 'channel_1',
#     'msg_data': {
#         'title': msg_title,
#         'a': msg_digest,
#         'pic_url': pic_url,
#         'link_url': link_url,
#         'msgtype': 'mpnews',
#         'mpnews': {
#             "articles": [{
#                 "title": msg_title,
#                 "thumb_media_id": image_path,
#                 "author": author,
#                 "content_source_url": link_url,
#                 "digest": msg_digest,
#                 "content": msg_content
#             }]
#         }
#     }
# }