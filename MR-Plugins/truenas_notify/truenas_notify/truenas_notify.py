import requests
import datetime
import time
import re
import json
import websocket
import threading
import ast
from mbot.core.plugins import plugin
from mbot.core.plugins import PluginContext, PluginMeta
from mbot.openapi import mbot_api
from typing import Dict, Any
import logging
import sched
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
_LOGGER = logging.getLogger(__name__)
server = mbot_api
# 禁用websocket模块的信息日志
logging.getLogger("websocket").setLevel(logging.WARNING)
plugins_name = '「TrueNAS 通知」'
plugins_path = '/data/plugins/truenas_notify'

@plugin.after_setup
def after_setup(plugin_meta: PluginMeta, config: Dict[str, Any]):
    global message_to_uid, channel, truenas_server, api_key, pic_url_base
    message_to_uid = config.get('uid')
    if config.get('channel'):
        channel = config.get('channel')
        _LOGGER.info(f'{plugins_name}已切换通知通道至「{channel}」')
    else:
        channel = 'qywx'
    truenas_server = config.get('truenas_server')
    api_key = config.get('api_key')
    pic_url_base = config.get('pic_url_base')
    _LOGGER.info(f'{plugins_name}封面图 URL 前缀：{pic_url_base}')
    if not message_to_uid:
        _LOGGER.error(f'{plugins_name}获取推送用户失败，可能是设置了没保存成功或者还未设置')
    # 启动 ws 线程
    start_get_truenas_alert()

@plugin.config_changed
def config_changed(config: Dict[str, Any]):
    global message_to_uid, channel, truenas_server, api_key, pic_url_base
    message_to_uid = config.get('uid')
    if config.get('channel'):
        channel = config.get('channel')
        _LOGGER.info(f'{plugins_name}已切换通知通道至「{channel}」')
    else:
        channel = 'qywx'
    truenas_server = config.get('truenas_server')
    api_key = config.get('api_key')
    pic_url_base = config.get('pic_url_base')
    _LOGGER.info(f'{plugins_name}封面图 URL 前缀：{pic_url_base}')
    if not message_to_uid:
        _LOGGER.error(f'{plugins_name}获取推送用户失败，可能是设置了没保存成功或者还未设置')
    # 启动 ws 线程
    start_get_truenas_alert()


def convert_seconds_to_mmss(seconds):
    """
    将秒数转换为 mm:ss 的格式。
    """
    seconds = int(seconds)
    minutes = seconds // 60
    seconds = seconds % 60
    return "{:02d} 分 {:02d} 秒".format(minutes, seconds)

def progress_device_text(alert_type, text):
    # 构造正则表达式 'Device: /dev/sdg [SAT], 2 Currently unreadable (pending) sectors.'
    patterns = {
        r"Device: (/dev/sd[a-z]+) \[SAT\], ATA error count increased from (\d+) to (\d+)":
            "设备: {0}, ATA 错误计数从{1}增加到{2}",
        r"Device: (/dev/sd[a-z]+) \[SAT\], (\d+) Currently unreadable \(pending\) sectors\.":
            "设备: {0}, {1}个扇区当前无法读取（挂起）"
    }
    # 使用循环遍历字典中的正则表达式模式
    for pattern, format_str in patterns.items():
        match = re.search(pattern, text)
        if match:
            # 提取设备名和数字
            groups = match.groups()
            # 使用 format 函数将变量插入到字符串模板中
            result = format_str.format(*groups)
            return result
    # 如果没有匹配到，则返回原字符串
    return text

def progress_app_text(alert_type, text):

    patterns = {
        r'An update is available for ["\'](.+?)["\'] application.+':
            "{0} 有更新",
        r"Failed to sync (.+?) catalog:(.+)":
            "同步 {0} 目录失败，原因：\n{1}"
    }

    for pattern, format_str in patterns.items():
        match = re.search(pattern, text)
        if match:
            # 将匹配到的内容传递给模板字符串的format方法，并返回结果
            result = format_str.format(*match.groups())
            return result
    return text

def progress_scrub_text(alert_type, text):
    _LOGGER.error(f'alert_text进入函数后处理前：{text}')
    # 构造正则表达式 started
    pattern = r"Scrub of pool '(.+)' (started|finished)\."
    # 使用正则表达式匹配字符串
    match = re.search(pattern, text)
    if match:
        # 提取池名
        pool_name = match.group(1)
        status = match.group(2)
        statuss={
            "started": "检查开始",
            "finished": "检查完成"
        }
        status = statuss.get(status, "检查状态未知")
        # 重新组合字符串
        result = f"存储池 '{pool_name}' {status}"
    else:
        # 没有匹配到，直接返回原字符串
        result = text
    _LOGGER.error(f'match：{match}')
    _LOGGER.error(f'alert_text进入函数后处理后：{result}')
    return result

def progress_ups_text(alert_type, text):
    if alert_type == 'UPSCommbad':
        text = '与 UPS 通信丢失，无法获取电池数据'
    else:
        battery_charge = re.search(r"battery\.charge:\s*(\d+)", text)
        battery_charge_low = re.search(r"battery\.charge\.low:\s*(\d+)", text)
        battery_runtime = re.search(r"battery\.runtime:\s*(\d+)", text)
        battery_runtime_low = re.search(r"battery\.runtime\.low:\s*(\d+)", text)
        text = f"电池总电量：{battery_charge.group(1)}%\n电池可运行：{convert_seconds_to_mmss(battery_runtime.group(1))}\n低电量模式临界电量：{battery_charge_low.group(1)}%\n低电量模式等待时间：{battery_runtime_low.group(1)}秒"
    return text

def progress_space_text(alert_type, text):
    patterns = {
        r'Space usage for pool (["\'])(.+)\1 is (\d+)%\. Optimal pool performance requires used space remain below 80%\.':
            'ZFS 存储池 "{1}" 的空间使用达到 {2}%. 为保证最佳池性能，使用空间应保持在 80% 以下.',
        r"Failed to check for alert ZpoolCapacity:(.+)":
            "检查存储池容量失败，原因：\n{0}"
    }

    for pattern, format_str in patterns.items():
        match = re.search(pattern, text)
        if match:
            # 将匹配到的内容传递给模板字符串的format方法，并返回结果
            result = format_str.format(*match.groups())
            return result
    return result

    # # 构造正则表达式
    # pattern = r'Space usage for pool (["\'])(.+)\1 is (\d+)%\. Optimal pool performance requires used space remain below 80%\.'
    # # 使用正则表达式匹配字符串
    # match = re.search(pattern, text)
    # if match:
    #     # 提取池名和空间使用率
    #     pool_name = match.group(2)
    #     usage_percent = match.group(3)
    #     # 重新组合字符串
    #     result = f'ZFS 存储池 "{pool_name}" 的空间使用达到 {usage_percent}%. 为保证最佳池性能，使用空间应保持在 80% 以下.'
    # else:
    #     # 没有匹配到，直接返回原字符串
    #     result = text
    # return result

def progress_ntp_text(alert_type, text):
    # 构造正则表达式
    pattern = r"NTP health check failed - No Active NTP peers: (\[.*\])"
    match = re.search(pattern, text)
    if match:
        peers_str = match.group(1)
        peers = ast.literal_eval(peers_str)
        try:
            ip_list = [list(peer.keys())[0] for peer in peers]
            return "NTP 健康检查失败，以下 NTP 都无法连接：\n" + ", ".join(ip_list)
        except Exception as e:
            result = text.replace("NTP health check failed - No Active NTP peers:", 'NTP 健康检查失败 - 没有活动的NTP服务器')
    else:
        # 没有匹配到，直接返回原字符串
        result = text
    return result

def progress_text(alert_type, alert_text):
    handlers_type = {
        'ScrubFinished': progress_scrub_text,
        'ScrubStarted': progress_scrub_text,
        'ZpoolCapacityNotice': progress_space_text,
        'ZpoolCapacityWarning': progress_space_text,
        'NTPHealthCheck': progress_ntp_text,
        'ChartReleaseUpdate': progress_app_text,
        'CatalogSyncFailed': progress_app_text,
        'SMART': progress_device_text,
        'UPSOnline': progress_ups_text,
        'UPSOnBattery': progress_ups_text,
        'UPSCommbad': progress_ups_text,
    }
    _LOGGER.error(f'alert_text处理前：{alert_text}')
    if alert_type in handlers_type:
        alert_text = handlers_type[alert_type](alert_type, alert_text)
    _LOGGER.error(f'alert_text处理后：{alert_text}')
    return alert_text

def progress_alert_text(alert):
    alert_level = alert['level']
    alert_type = alert['klass']
    alert_text = alert['formatted']
    alert_time = datetime.datetime.fromtimestamp(alert['datetime']['$date']/1000).strftime("%Y-%m-%d %H:%M:%S")
    alert_content = {
        'alert_time': alert_time,
        'alert_level': alert_level,
        'alert_type': alert_type,
        'alert_text': alert_text,
    }
    _LOGGER.info(f"alert_content: {alert_content}")
    level_list = {
        'CRITICAL': '‼️',
        'WARNING':'⚠️',
        'NOTICE':'✉️',
        'INFO':'ℹ️'
    }
    # type_list = {
    #     'ScrubFinished': '磁盘检修完成',
    #     'ScrubStarted': '磁盘检修开始',
    #     'ZpoolCapacityNotice': '存储池容量提醒',
    #     'ZpoolCapacityWarning': '存储池容量警告',
    #     'NTPHealthCheck': 'NTP 健康检查',
    #     'UPSOnline': 'UPS 恢复供电',
    #     'UPSOnBattery': 'UPS 进入电池供电',
    #     'UPSCommbad': 'UPS 断开连接',
    #     'ChartReleaseUpdate': '应用有更新',
    #     'CatalogSyncFailed': '应用目录同步失败',
    #     'SMART': 'SMART异常'
    # }
    # pic_url_list = {
    #     'ScrubFinished': 'scrub.png',
    #     'ScrubStarted': 'scrub.png',
    #     'ZpoolCapacityNotice': 'space.png',
    #     'ZpoolCapacityWarning': 'space.png',
    #     'NTPHealthCheck': 'ntp.png',
    #     'UPSOnline': 'ups_on.png',
    #     'UPSOnBattery': 'ups_battery.png',
    #     'UPSCommbad': 'ups_lost.png',
    #     'ChartReleaseUpdate': 'update.png',
    #     'CatalogSyncFailed': 'update.png',
    #     'SMART': 'smart.png'
    # }
    # new_alert = alert_content
    # pic_url = f"{pic_url_base}/{pic_url_list.get(new_alert.get('alert_type', ''), 'default.png')}"
    
    # msg_title = f"{level_list.get(new_alert.get('alert_level',''), new_alert.get('alert_level',''))} {type_list.get(new_alert.get('alert_type',''), new_alert.get('alert_type', ''))}"
    # new_alert_type = new_alert.get('alert_type', '')
    # new_alert_text = new_alert.get('alert_text', '')

    # 将type_list和pic_url_list合并为一个字典
    alert_mapping = {
        'ScrubFinished': {
            'title': '磁盘检修完成',
            'pic': 'scrub.png',
        },
        'ScrubStarted': {
            'title': '磁盘检修开始',
            'pic': 'scrub.png',
        },
        'ZpoolCapacityNotice': {
            'title': '存储池容量提醒',
            'pic': 'space.png',
        },
        'ZpoolCapacityWarning': {
            'title': '存储池容量警告',
            'pic': 'space.png',
        },
        'NTPHealthCheck': {
            'title': 'NTP 健康检查',
            'pic': 'ntp.png',
        },
        'UPSOnline': {
            'title': 'UPS 恢复供电',
            'pic': 'ups_on.png',
        },
        'UPSOnBattery': {
            'title': 'UPS 进入电池供电',
            'pic': 'ups_battery.png',
        },
        'UPSCommbad': {
            'title': 'UPS 断开连接',
            'pic': 'ups_lost.png',
        },
        'ChartReleaseUpdate': {
            'title': '应用有更新',
            'pic': 'update.png',
        },
        'CatalogSyncFailed': {
            'title': '应用目录同步失败',
            'pic': 'update.png',
        },
        'SMART': {
            'title': 'SMART异常',
            'pic': 'smart.png',
        },
        'AlertSourceRunFailed': {
            'title': '警报源运行失败',
            'pic': 'default.png',
        },
    }
    new_alert = alert_content
    new_alert_type = new_alert.get('alert_type', '')
    new_alert_info = alert_mapping.get(new_alert_type, {})
    pic_url = f"{pic_url_base}/{new_alert_info.get('pic', 'default.png')}"
    msg_title = f"{level_list.get(new_alert.get('alert_level', new_alert.get('alert_level')))} {new_alert_info.get('title', new_alert_type)}"
    new_alert_text = new_alert.get('alert_text', '')
    
    # if 'UPS' in new_alert_type:
    #     new_alert_text =progress_ups_text(new_alert_type, new_alert_text)
    # else:
    #     new_alert_text =progress_text(new_alert_type, new_alert_text)
    new_alert_text =progress_text(new_alert_type, new_alert_text)

    msg_digest = f"{new_alert_text}\n{new_alert.get('alert_time','')}"
    _LOGGER.info(f'{plugins_name}获取到的系统新通知如下:\n{msg_title}\n{msg_digest}')
    push_msg_to_mbot(msg_title, msg_digest, pic_url)

def on_open(ws):
    # 发送连接请求到服务器
    connect_message = {
        "msg": "connect",
        "version": "1",
        "support": ["1"]
    }
    ws.send(json.dumps(connect_message))
def on_message(ws, message):
    global session_id
    json_data = json.loads(message)
    if json_data['msg'] == 'connected':
        session_id = json_data['session']
        # _LOGGER.info(f'{plugins_name}连接 websocket 成功')
        # 通过api_key进行身份验证
        auth_message = {
            "id": session_id,
            "msg": "method",
            "method": "auth.login_with_api_key",
            "params": [api_key]
        }
        ws.send(json.dumps(auth_message))
    elif json_data['msg'] == 'result' and json_data['result'] == 'pong':
        heartbeat_result = json_data
        # 接收心跳返回结果
        # if datetime.datetime.now().minute in [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]:
        if datetime.datetime.now().minute % 5 == 0:
            _LOGGER.info(f'{plugins_name}心跳: {heartbeat_result}')
            time.sleep(60)
    elif json_data['msg'] == 'result' and json_data['result'] == True:
        # _LOGGER.info(f'{plugins_name}websocket 身份认证成功')
        # 订阅报警事件
        subscribe_message = {
            "msg": "sub",
            "id": session_id,
            "name": "alert.list"
        }
        ws.send(json.dumps(subscribe_message))
    # 接收报警信息
    elif json_data['msg'] == 'added' and json_data['collection'] == 'alert.list':
        alert = json_data['fields']
        # 处理报警信息
        progress_alert_text(alert)


def on_error(ws, error):
    _LOGGER.error(f'{plugins_name}连接 Websocket 出错了：{error} 关闭后重新连接')
    try:
        ws.close()
        ws.run_forever()
    except Exception as e:
        _LOGGER.info(f"{plugins_name}重连 Websocket 失败, 原因：{e}")

def on_close(ws, close_status_code, close_msg):
    _LOGGER.info(f"{plugins_name}关闭 Websocket 连接，close_status_code:{close_status_code}, close_msg:{close_msg}")

def push_msg_to_mbot(msg_title, msg_digest, pic_url):
    msg_data = {
        'title': msg_title,
        'a': msg_digest,
        'pic_url': pic_url,
        'link_url': '',
    }
    try:
        if message_to_uid:
            for _ in message_to_uid:
                server.notify.send_message_by_tmpl('{{title}}', '{{a}}', msg_data, to_uid=_, to_channel_name = channel)
        else:
            server.notify.send_message_by_tmpl('{{title}}', '{{a}}', msg_data)
        _LOGGER.info(f'{plugins_name}已推送消息')
        return
    except Exception as e:
        _LOGGER.error(f'{plugins_name}推送消息异常，原因: {e}')

def start_get_truenas_alert():
    try:
        ws.close()
        _LOGGER.info("get_truenas_alert 线程正在运行, 终止当前线程重新启动.")
    except Exception as e:
        _LOGGER.error(f"{plugins_name}get_truenas_alert 线程没有运行, 等待定时任务，将重新启动新线程。原因：{e}")
    # 启动新线程
    thread = threading.Thread(target=get_truenas_alert)
    thread.start()
    
def get_truenas_alert():
    global ws
    try:
        websocket_url = f"wss://{truenas_server}/websocket"
        ws = websocket.WebSocketApp(websocket_url,
                                    on_open=on_open,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
        ws.run_forever()
    except Exception as e:
        websocket_url = f"ws://{truenas_server}/websocket"
        ws = websocket.WebSocketApp(websocket_url,
                                    on_open=on_open,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
        ws.run_forever()

# sched模块实现每隔 50 秒执行一次心跳，原来的1分钟执行一次的cron不受影响，自动计算每隔 50 秒下一次执行时间
scheduler = sched.scheduler(time.time, time.sleep)
def send_heartbeat():
    ping_message = {
        "id": 'heartbeat-ping-pong',
        "msg": "method",
        "method": "core.ping"
    }
    try:
        ws.send(json.dumps(ping_message))
    except Exception as e:
        _LOGGER.error(f'{plugins_name}心跳异常，原因: {e}')
        start_get_truenas_alert()
    scheduler.enter(50, 1, send_heartbeat)

@plugin.task('truenas_heartbeat', 'TrueNAS Websocket 心跳', cron_expression='*/1 * * * *')
def task():
    scheduler.enter(0, 1, send_heartbeat)
    scheduler.run()
