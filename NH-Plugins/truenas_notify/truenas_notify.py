import os
from fastapi.responses import FileResponse
from fastapi import APIRouter
from notifyhub.controller.schedule import register_cron_job
from notifyhub.plugins.common import after_setup
from notifyhub.controller.server import server
from notifyhub.plugins.utils import (
    get_plugin_data,
    get_plugin_config
)
import datetime
import time
import re
import json
import websocket
import threading
import ast

from typing import Dict, Any
import sched
import ssl

import logging
logger = logging.getLogger(__name__)


plugin_id = "truenas_notify"
plugin_name = "TrueNAS 通知"
pic_url_base = f"https://raw.githubusercontent.com/Alano-i/Plugins/refs/heads/main/TrueNas_notify/img"
try:
    if server.site_url:
        pic_url_base = f"{server.site_url}/api/plugins/{plugin_id}/cover"
    else:
        logger.error(f"「{plugin_name}」未配置 NotifyHub 站点外网访问地址，请前往 系统设置 -> 网络设置 -> 站点访问地址 配置站点外网 URL")

except Exception as e:
    logger.error(f"「{plugin_name}」获取通知封面前缀出错，原因：{e}")

# 禁用websocket模块的信息日志
logging.getLogger("websocket").setLevel(logging.WARNING)
plugins_name = '「TrueNAS 通知」'
plugins_path = '/data/plugins/truenas_notify'

# 获取原始存储数据（含名称等元信息）
data = get_plugin_data(plugin_id)  # 存在时返回字典，不存在返回 None

# 获取配置字典
config = get_plugin_config(plugin_id)  # 返回 dict，不存在时返回空字典 {}

# logger.info(f"「{plugin_name}」原始存储数据（含名称等元信息）: {data}")
# logger.info(f"「{plugin_name}」配置字典: {config}")
logger.info(f"「{plugin_name}」通知封面前缀: {pic_url_base}")

truenas_server = config.get('truenas_server')
api_key = config.get('api_key')
# pic_url_base = config.get('pic_url_base')
notify_switch = config.get('notify_switch', True)
bind_channel = config.get('bind_channel')
logger.info(f'{plugins_name}监控的TrueNAS服务器地址：{truenas_server}')
logger.info(f'{plugins_name}封面图 URL 前缀：{pic_url_base}')

def push_msg(msg_title, msg_digest, pic_url):
    if notify_switch:
        try:
            # 按渠道发送（单个渠道）
            server.send_notify_by_channel(
                channel_name=bind_channel,
                title=msg_title,
                content=msg_digest,
                push_img_url=pic_url,      # 可选
                push_link_url=''           # 可选
            )

            # 按通道发送（通道会绑定一个或多个渠道）
            # server.send_notify_by_router(
            #     route_id=BIND_ROUTES,
            #     title="IPTV 频道更新通知",
            #     content=content,
            #     push_img_url=None, # 可选
            #     push_link_url=None # 可选
            # )
            logger.info(f"「{plugin_name}」✅ 已发送通知")
        except Exception as e:
            logger.error(f"❌ 发送通知失败: {e}")
    else:
        logger.info(f"「{plugin_name}」通知开关未开启，跳过发送通知")


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
    logger.error(f'alert_text进入函数后处理前：{text}')
    # 构造正则表达式 started
    pattern = r"Scrub of pool '(.+)' (?:has )?(started|finished)\."
    # 使用正则表达式匹配字符串
    match = re.search(pattern, text)
    if match:
        # 提取池名
        pool_name = match.group(1)
        status = match.group(2)
        statuss = {
            "started": "检查开始",
            "finished": "检查完成"
        }
        status = statuss.get(status, "检查状态未知")
        # 重新组合字符串
        result = f"存储池 '{pool_name}' {status}，在此期间，性能可能会下降。"
    else:
        # 没有匹配到，直接返回原字符串
        result = text
    logger.error(f'match：{match}')
    logger.error(f'alert_text进入函数后处理后：{result}')
    return result


def progress_ups_text(alert_type, text):
    if alert_type == 'UPSCommbad':
        text = '与 UPS 通信丢失，无法获取电池数据'
    else:
        battery_charge = re.search(r"battery\.charge:\s*(\d+)", text)
        battery_charge_low = re.search(r"battery\.charge\.low:\s*(\d+)", text)
        battery_runtime = re.search(r"battery\.runtime:\s*(\d+)", text)
        battery_runtime_low = re.search(
            r"battery\.runtime\.low:\s*(\d+)", text)
        text = f"电池总电量：{battery_charge.group(1)}%\n电池可运行：{convert_seconds_to_mmss(battery_runtime.group(1))}\n低电量模式临界电量：{battery_charge_low.group(1)}%\n低电量模式等待时间：{battery_runtime_low.group(1)}秒"
    return text
    
def progress_sys_update_text(alert_type, text):
    text = '请前往 系统 → 更新 以下载并应用更新。' if 'system update is available' in text else text
    return text
def progress_pool_update_text(alert_type, text):
    # 匹配 pool 名称
    pattern = r"pool '(.+?)'"
    match = re.search(pattern, text)

    if match:
        pool_name = match.group(1)
        # 重新组合字符串
        text_new = f"存储池 '{pool_name}'有新的 ZFS 版本。请注意，升级池是一次性过程，可能会阻止将系统回滚到早期的 TrueNAS 版本。建议在升级池之前阅读 TrueNAS 发布说明，并确认您需要新的 ZFS 功能。"
    else:
        text_new = text  # 没匹配到就保留原文
    return text_new

def progress_volumestatus_text(alert_type, text):
    # 匹配池名和状态
    pool_pattern = r"Pool (\w+) state is (\w+)"
    pool_match = re.search(pool_pattern, text)

    if not pool_match:
        return text  # 没匹配到，原文返回

    pool_name = pool_match.group(1)
    state = pool_match.group(2)

    if state == "DEGRADED":
        # 匹配所有离线磁盘
        disks = re.findall(r"Disk (\d+) is OFFLINE", text)
        if disks:
            disk_msgs = "\n".join([f"硬盘 {d} 已离线" for d in disks])
        else:
            disk_msgs = "存在设备异常（未匹配到具体磁盘）"
        return (f"存储池降级，一个或多个设备当前正在重新同步，"
                f"存储池将继续正常运行但会处于降级状态。\n\n{disk_msgs}")

    elif state == "ONLINE":
        # ONLINE + 不可恢复错误的情况
        return (f"存储池【{pool_name}】上线：一个或多个设备发生了不可恢复的错误。"
                f"已尝试修正该错误。应用程序未受影响。")

    else:
        return f"存储池【{pool_name}】状态：{state}"


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
            result = text.replace(
                "NTP health check failed - No Active NTP peers:", 'NTP 健康检查失败 - 没有活动的NTP服务器')
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
        'AppUpdate': progress_app_text,
        'CatalogSyncFailed': progress_app_text,
        'SMART': progress_device_text,
        'UPSOnline': progress_ups_text,
        'UPSOnBattery': progress_ups_text,
        'UPSCommbad': progress_ups_text,
        'HasUpdate': progress_sys_update_text,
        'PoolUpgraded': progress_pool_update_text,
        'VolumeStatus': progress_volumestatus_text,
    }
    logger.error(f'alert_text处理前：{alert_text}')
    if alert_type in handlers_type:
        alert_text = handlers_type[alert_type](alert_type, alert_text)
    logger.error(f'alert_text处理后：{alert_text}')
    return alert_text


def progress_alert_text(alert):
    alert_level = alert['level']
    alert_type = alert['klass']
    alert_text = alert['formatted']
    alert_time = datetime.datetime.fromtimestamp(
        alert['datetime']['$date']/1000).strftime("%Y-%m-%d %H:%M:%S")
    alert_content = {
        'alert_time': alert_time,
        'alert_level': alert_level,
        'alert_type': alert_type,
        'alert_text': alert_text,
    }
    logger.info(f"alert_content: {alert_content}")
    level_list = {
        'CRITICAL': '‼️',
        'WARNING': '⚠️',
        'NOTICE': '✉️',
        'INFO': 'ℹ️'
    }


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
        'AppUpdate': {
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
        'SMBPath': {
            'title': 'SMB共享存在与路径相关的配置问题',
            'pic': 'default.png',
        },
        'PoolUpgraded': {
            'title': 'ZFS版本升级',
            'pic': 'default.png',
        },
        'VolumeStatus': {
            'title': '存储池状态异常',
            'pic': 'default.png',
        },
        'HasUpdate': {
            'title': 'TrueNAS 系统有更新',
            'pic': 'sys_update.png',
        },
    }
    new_alert = alert_content
    new_alert_type = new_alert.get('alert_type', '')
    new_alert_info = alert_mapping.get(new_alert_type, {})
    pic_url = f"{pic_url_base}/{new_alert_info.get('pic', 'default.png')}"
    msg_title = f"{level_list.get(new_alert.get('alert_level', new_alert.get('alert_level')))} {new_alert_info.get('title', new_alert_type)}"
    new_alert_text = new_alert.get('alert_text', '')
    new_alert_text = progress_text(new_alert_type, new_alert_text)

    msg_digest = f"{new_alert_text}\n{new_alert.get('alert_time','')}"
    logger.info(f'{plugins_name}获取到的系统新通知如下:\n{msg_title}\n{msg_digest}')
    push_msg(msg_title, msg_digest, pic_url)


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
        # logger.info(f'{plugins_name}连接 websocket 成功')
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
            logger.info(f'{plugins_name}心跳: {heartbeat_result}')
            time.sleep(60)
    elif json_data['msg'] == 'result' and json_data['result'] == True:
        # logger.info(f'{plugins_name}websocket 身份认证成功')
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
    logger.error(f'{plugins_name} 连接 WebSocket 出错了：{error} 关闭后重新连接')
    time.sleep(60)
    try:
        ws.close()
        # ws.run_forever()
        start_get_truenas_alert()
    except Exception as e:
        logger.info(f"{plugins_name} 重连 WebSocket 失败，原因：{e}")


def on_close(ws, close_status_code, close_msg):
    logger.info(
        f"{plugins_name}关闭 Websocket 连接，close_status_code:{close_status_code}, close_msg:{close_msg}")


def start_get_truenas_alert():
    global ws
    try:
        if ws and ws.sock:
            ws.close()
            logger.info("get_truenas_alert 线程正在运行，终止当前线程重新启动。")
    except Exception as e:
        logger.warning(
            f"{plugins_name} get_truenas_alert 线程没有运行，等待定时任务，将重新启动新线程。原因：{e}")
    # 启动新线程
    thread = threading.Thread(target=get_truenas_alert)
    thread.start()


def get_truenas_alert():
    global ws
    try:
        websocket_url = f"{truenas_server}/websocket"
        ws = websocket.WebSocketApp(websocket_url,
                                    on_open=on_open,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
        # ws.run_forever()
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})  # 忽略证书验证
    except Exception as e:
        logger.error(f'{plugins_name} 启动 WebSocket 异常，原因：{e}')
        start_get_truenas_alert()


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
        logger.error(f'{plugins_name}心跳异常，原因: {e}')
        start_get_truenas_alert()
    scheduler.enter(50, 1, send_heartbeat)


def task():
    get_truenas_alert()
    scheduler.enter(0, 1, send_heartbeat)
    scheduler.run()


# 在 after_setup 中注册定时任务（同步）
@after_setup(plugin_id=plugin_id, desc="TrueNAS 通知")
def setup_cron_jobs():
    logger.info(f"「{plugin_name}」注册定时查询任务...")
    # 注册定时任务，支持 cron 表达式
    register_cron_job('*/1 * * * *', "TrueNAS 通知", task, random_delay_seconds=10)


truenas_notify_router = APIRouter(prefix="/truenas_notify", tags=["truenas_notify"])


@truenas_notify_router.get("/cover/{filename}")
async def cover(filename: str):
    # 图片在当前插件目录下的 cover 目录中
    file_path = os.path.join(plugins_path, 'cover', filename)
    logger.info(f"「{plugin_name}」收到请求图片: {file_path}")
    if os.path.exists(file_path) and os.path.isfile(file_path):
        # 自动根据后缀推断类型
        ext = os.path.splitext(filename)[-1].lower()
        media_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
        }.get(ext, "application/octet-stream")
        # return FileResponse(file_path, media_type=media_type, filename=filename)  # filename 参数用于下载时的默认文件名，浏览器下载图片
        response = FileResponse(file_path, media_type=media_type)   # 浏览器直接显示图片
        # 设置缓存头，比如缓存 7 天
        response.headers["Cache-Control"] = "public, max-age=604800"
        return response
    else:
        return {"error": "Image not found"}
