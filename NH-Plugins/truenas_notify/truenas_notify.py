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
    
def progress_rsync_success_text(alert_type, text):
    if '"PULL"' in text:
        task_type='拉取'
    elif '"PUSH"' in text:
        task_type='推送'
    else:
        task_type=''
    # 提取路径
    path_match = re.search(r'for\s+"([^"]+)"', text)
    path = path_match.group(1) if path_match else None

    if task_type and path:
        text = f'状态：成功✅\n类型：{task_type}\n路径：{path}'
    return text
def progress_rsync_failed_text(alert_type, text):
    if '"PULL"' in text:
        task_type='拉取'
    elif '"PUSH"' in text:
        task_type='推送'
    else:
        task_type=''
    # 提取路径
    path_match = re.search(r'for\s+"([^"]+)"', text)
    path = path_match.group(1) if path_match else None

    if task_type and path:
        text = f'状态：❌失败\n类型：{task_type}\n路径：{path}'
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
        'RsyncSuccess': progress_rsync_success_text,
        'RsyncFailed': progress_rsync_failed_text,
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
        'RsyncSuccess': {
            'title': 'Rsync 备份成功',
            'pic': 'rsync.png',
        },
        'RsyncFailed': {
            'title': 'Rsync 备份失败',
            'pic': 'rsync.png',
        },
    }
    new_alert = alert_content
    new_alert_type = new_alert.get('alert_type', '')
    new_alert_info = alert_mapping.get(new_alert_type, {})
    pic_url = f"{pic_url_base}/{new_alert_info.get('pic', 'default.png')}"
    msg_title = f"{level_list.get(new_alert.get('alert_level', new_alert.get('alert_level')))} {new_alert_info.get('title', new_alert_type)}"
    new_alert_text = new_alert.get('alert_text', '')
    new_alert_text = progress_text(new_alert_type, new_alert_text)

    msg_digest = f"{new_alert_text}\n时间：{new_alert.get('alert_time','')}"
    logger.info(f'{plugins_name}获取到的系统新通知如下:\n{msg_title}\n{msg_digest}')
    push_msg(msg_title, msg_digest, pic_url)


# Connection state management
CONNECTION_STATE_DISCONNECTED = 0
CONNECTION_STATE_CONNECTING = 1
CONNECTION_STATE_CONNECTED = 2

connection_state = CONNECTION_STATE_DISCONNECTED
connection_lock = threading.Lock()
reconnect_attempts = 0
last_reconnect_time = 0
heartbeat_thread = None
heartbeat_stop_event = threading.Event()

# Exponential backoff configuration
MIN_RETRY_DELAY = 5  # seconds
MAX_RETRY_DELAY = 60  # seconds
RETRY_BACKOFF_FACTOR = 2


def get_retry_delay():
    """Calculate retry delay with exponential backoff"""
    global reconnect_attempts
    delay = min(MIN_RETRY_DELAY * (RETRY_BACKOFF_FACTOR ** reconnect_attempts), MAX_RETRY_DELAY)
    return delay


def on_open(ws):
    global connection_state, reconnect_attempts
    # 发送连接请求到服务器
    connect_message = {
        "msg": "connect",
        "version": "1",
        "support": ["1"]
    }
    try:
        ws.send(json.dumps(connect_message))
        with connection_lock:
            connection_state = CONNECTION_STATE_CONNECTING
    except Exception as e:
        logger.error(f'{plugins_name} 发送连接消息失败：{e}')


def on_message(ws, message):
    global session_id, connection_state, reconnect_attempts
    json_data = json.loads(message)
    if json_data['msg'] == 'connected':
        session_id = json_data['session']
        logger.info(f'{plugins_name}连接 WebSocket 成功，session: {session_id}')
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
        if datetime.datetime.now().minute % 15 == 0:
            logger.info(f'{plugins_name}心跳: {heartbeat_result}')
            time.sleep(60)
    elif json_data['msg'] == 'result' and json_data['result'] == True:
        logger.info(f'{plugins_name}WebSocket 身份认证成功')
        # 订阅报警事件
        subscribe_message = {
            "msg": "sub",
            "id": session_id,
            "name": "alert.list"
        }
        ws.send(json.dumps(subscribe_message))
        # 标记为已连接，重置重试计数器
        with connection_lock:
            connection_state = CONNECTION_STATE_CONNECTED
            reconnect_attempts = 0
        # 启动心跳线程
        start_heartbeat()
    # 接收报警信息
    elif json_data['msg'] == 'added' and json_data['collection'] == 'alert.list':
        alert = json_data['fields']
        # 处理报警信息
        progress_alert_text(alert)


def on_error(ws, error):
    global connection_state
    logger.error(f'{plugins_name} WebSocket 错误：{error}')
    with connection_lock:
        connection_state = CONNECTION_STATE_DISCONNECTED


def on_close(ws, close_status_code, close_msg):
    global connection_state
    logger.info(
        f"{plugins_name}关闭 WebSocket 连接，close_status_code:{close_status_code}, close_msg:{close_msg}")
    with connection_lock:
        connection_state = CONNECTION_STATE_DISCONNECTED
    # 停止心跳
    stop_heartbeat()


def start_get_truenas_alert():
    global ws, reconnect_attempts, last_reconnect_time, connection_state
    
    with connection_lock:
        # 防止多个线程同时尝试重连
        if connection_state == CONNECTION_STATE_CONNECTING:
            logger.info(f"{plugins_name} 已有连接正在尝试中，跳过本次重连")
            return
        
        connection_state = CONNECTION_STATE_CONNECTING
        reconnect_attempts += 1
    
    # 计算重试延迟
    current_time = time.time()
    time_since_last_reconnect = current_time - last_reconnect_time
    retry_delay = get_retry_delay()
    
    if time_since_last_reconnect < retry_delay:
        wait_time = retry_delay - time_since_last_reconnect
        logger.info(f"{plugins_name} 等待 {wait_time:.1f} 秒后重连（第 {reconnect_attempts} 次尝试）")
        time.sleep(wait_time)
    
    last_reconnect_time = time.time()
    
    # 清理旧连接
    try:
        if ws and hasattr(ws, 'sock') and ws.sock:
            ws.close()
            logger.info(f"{plugins_name} 已关闭旧的 WebSocket 连接")
    except Exception as e:
        logger.debug(f"{plugins_name} 清理旧连接时出错（可忽略）：{e}")
    
    # 启动新线程
    thread = threading.Thread(target=get_truenas_alert, daemon=True)
    thread.start()


def get_truenas_alert():
    global ws
    try:
        websocket_url = f"{truenas_server}/websocket"
        logger.info(f"{plugins_name} 正在连接到 {websocket_url}")
        ws = websocket.WebSocketApp(websocket_url,
                                    on_open=on_open,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
        # 不使用 websocket 库的自动 ping/pong，因为 TrueNAS 使用 JSON-RPC 的 core.ping
        # 我们的自定义心跳线程会处理心跳
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    except Exception as e:
        logger.error(f'{plugins_name} WebSocket 连接异常：{e}')
        with connection_lock:
            connection_state = CONNECTION_STATE_DISCONNECTED
        # 尝试重连
        start_get_truenas_alert()


def start_heartbeat():
    """启动心跳线程"""
    global heartbeat_thread, heartbeat_stop_event
    
    # 停止旧的心跳线程
    stop_heartbeat()
    
    # 创建新的心跳线程
    heartbeat_stop_event.clear()
    heartbeat_thread = threading.Thread(target=send_heartbeat_loop, daemon=True)
    heartbeat_thread.start()
    logger.info(f"{plugins_name} 心跳线程已启动")


def stop_heartbeat():
    """停止心跳线程"""
    global heartbeat_stop_event
    if heartbeat_stop_event:
        heartbeat_stop_event.set()


def send_heartbeat_loop():
    """心跳循环，每 50 秒发送一次"""
    global ws, connection_state
    
    while not heartbeat_stop_event.is_set():
        # 等待 50 秒或直到收到停止信号
        if heartbeat_stop_event.wait(50):
            break
        
        # 检查连接状态
        with connection_lock:
            if connection_state != CONNECTION_STATE_CONNECTED:
                logger.debug(f"{plugins_name} 连接未就绪，跳过心跳")
                continue
        
        # 发送心跳
        ping_message = {
            "id": 'heartbeat-ping-pong',
            "msg": "method",
            "method": "core.ping"
        }
        try:
            if ws and hasattr(ws, 'sock') and ws.sock:
                ws.send(json.dumps(ping_message))
            else:
                logger.warning(f'{plugins_name} WebSocket 未连接，跳过心跳')
        except Exception as e:
            logger.error(f'{plugins_name} 心跳发送失败：{e}')
            # 心跳失败，触发重连
            with connection_lock:
                connection_state = CONNECTION_STATE_DISCONNECTED
            start_get_truenas_alert()
            break
    
    logger.info(f"{plugins_name} 心跳线程已停止")


def task():
    """定时任务入口点，确保 WebSocket 连接始终运行"""
    global connection_state
    
    with connection_lock:
        current_state = connection_state
    
    # 如果未连接，启动连接
    if current_state == CONNECTION_STATE_DISCONNECTED:
        logger.info(f"{plugins_name} 定时任务检测到连接断开，启动连接")
        start_get_truenas_alert()
    else:
        logger.debug(f"{plugins_name} 定时任务检测，连接状态正常")


# 在 after_setup 中注册定时任务（同步）
@after_setup(plugin_id=plugin_id, desc="TrueNAS 通知")
def setup_cron_jobs():
    logger.info(f"「{plugin_name}」注册定时查询任务...")
    # 注册定时任务，支持 cron 表达式
    register_cron_job('*/1 * * * *', "TrueNAS 通知", task, random_delay_seconds=10)



