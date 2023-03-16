import requests
import datetime
import re
import json
from mbot.core.plugins import plugin
from mbot.core.plugins import PluginContext, PluginMeta
from mbot.openapi import mbot_api
from typing import Dict, Any
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
_LOGGER = logging.getLogger(__name__)
server = mbot_api

plugins_name = '「TrueNas Scale 系统通知」'
plugins_path = '/data/plugins/truenas_notify'


@plugin.after_setup
def after_setup(plugin_meta: PluginMeta, config: Dict[str, Any]):
    global message_to_uid, channel, truenas_server, api_token, pic_url
    message_to_uid = config.get('uid')
    if config.get('channel'):
        channel = config.get('channel')
        _LOGGER.info(f'{plugins_name}已切换通知通道至「{channel}」')
    else:
        channel = 'qywx'
    truenas_server = config.get('truenas_server')
    api_token = config.get('api_token')
    pic_url = config.get('pic_url')
    if not message_to_uid:
        _LOGGER.error(f'{plugins_name}获取推送用户失败，可能是设置了没保存成功或者还未设置')

@plugin.config_changed
def config_changed(config: Dict[str, Any]):
    global message_to_uid, channel, truenas_server, api_token, pic_url
    message_to_uid = config.get('uid')
    if config.get('channel'):
        channel = config.get('channel')
        _LOGGER.info(f'{plugins_name}已切换通知通道至「{channel}」')
    else:
        channel = 'qywx'
    truenas_server = config.get('truenas_server')
    api_token = config.get('api_token')
    pic_url = config.get('pic_url')
    if not message_to_uid:
        _LOGGER.error(f'{plugins_name}获取推送用户失败，可能是设置了没保存成功或者还未设置')

@plugin.task('truenas_nofity', 'TrueNas Scale 系统通知', cron_expression='*/1 * * * *')
def task():
    get_truenas_alert()

def progress_ups_text(alert_text):
    battery_charge = re.search(r"battery\.charge:\s*(\d+)", alert_text)
    battery_charge_low = re.search(r"battery\.charge\.low:\s*(\d+)", alert_text)
    battery_runtime = re.search(r"battery\.runtime:\s*(\d+)", alert_text)
    battery_runtime_low = re.search(r"battery\.runtime\.low:\s*(\d+)", alert_text)
    alert_text = f"电池总电量：{battery_charge.group(1)}%\n电池可运行：{battery_runtime.group(1)} 秒\n切换到低电量临界电量：{battery_charge_low.group(1)}%\n切换到低电量等待时间：{battery_runtime_low.group(1)}秒"
    return alert_text

def progress_text(alert_text):
    alert_text = alert_text.replace('NTP health check failed', 'NTP 健康检查失败').replace('Scrub of pool', '存储池').replace('finished', '检查完成').replace('Space usage for pool', 'ZFS 存储池').replace('is', '的空间使用率为').replace('Optimal pool performance requires used space remain below 80%', '为保证最佳池性能，使用空间应保持在 80% 以下')
    alert_text = alert_text.replace('Device:', '设备:').replace('ATA error count increased from', 'ATA 错误计数从').replace(' to ', ' 增加到 ').replace('REJECT', '无法连接')
    alert_text = alert_text.replace('Currently unreadable (pending) sectors', '个当前无法读取的（待处理）扇区').replace('No Active NTP peers', '没有活动的NTP服务器')
    return alert_text
  
def get_truenas_alert():
    # TrueNA Scale的IP地址和端口
    # truenas_server = 'http://10.10.10.10:9999'
    truenas_alert_api_url = f"{truenas_server}/api/v2.0/alert/list"
    # 构建请求头
    headers = {
        'Content-Type': 'application/json',
        "Authorization": f"Bearer {api_token}"
    }
    # 请求系统通知
    response = requests.get(truenas_alert_api_url, headers=headers, timeout=10)
    # 解析请求返回
    json_data = json.loads(response.text)
    
    if json_data:
        alert_num = len(json_data)
        # 遍历所有alert并按alert_time倒序排序
        json_data = sorted(json_data, key=lambda x: x['datetime']['$date'], reverse=True)
        if server.common.get_cache('notify', 'alerts'):
            old_alerts = server.common.get_cache('notify', 'alerts')
        else:
            old_alerts = []
        alerts = []
        for alert in json_data:
            alert_level = alert['level']
            alert_type = alert['klass']
            alert_text = alert['formatted']
            alert_time = datetime.datetime.fromtimestamp(alert['datetime']['$date']/1000).strftime("%Y-%m-%d %H:%M:%S")
            nofity_content = {
                'alert_time': alert_time,
                'alert_level': alert_level,
                'alert_type': alert_type,
                'alert_text': alert_text,
            }
            alerts.append(nofity_content)
        # _LOGGER.info(f'alerts:{alerts}')

        # _LOGGER.info(f'old_alerts:{old_alerts}')
        if old_alerts != alerts:
            server.common.set_cache('notify', 'alerts', alerts)
            dif_alerts = []
            for alert in alerts:
                if alert not in old_alerts:
                    dif_alerts.append(alert)
            dif_alerts_num = len(dif_alerts)
            level_list = {
                'CRITICAL': '‼️',
                'WARNING':'⚠️',
                'NOTICE':'✉️',
                'INFO':'ℹ️'
            }
            type_list = {
                'ScrubFinished': '磁盘检修完成',
                'ZpoolCapacityNotice': '存储池容量提醒',
                'NTPHealthCheck': 'NTP 健康检查',
                'UPSOnline': 'UPS 恢复供电',
                'SMART': 'SMART异常'
            }
            if dif_alerts_num > 1:
                msg_title = f'💌 {dif_alerts_num} 条系统通知'
                msg_digest = ""
                for alert in dif_alerts:
                    alert_level = level_list.get(alert.get('alert_level',''),'')
                    alert_type = type_list.get(alert.get('alert_type', ''),'')
                    alert_text = alert.get('alert_text', '')

                    if 'UPS' in alert_type:
                        alert_text =progress_ups_text(alert_text)
                    else:
                        alert_text =progress_text(alert_text)
                        
                    alert_time = alert.get('alert_time', '')
                    msg_digest += f"{alert_level} {alert_type}\n{alert_text}\n{alert_time}\n\n"
                msg_digest = msg_digest.strip()
            else:
                dif_alert = dif_alerts[0]
                msg_title = f"{level_list.get(dif_alert.get('alert_level',''),'')} {type_list.get(dif_alert.get('alert_type',''),'') }"
                alert_type = dif_alert.get('alert_type', '')
                alert_text = dif_alert.get('alert_text', '')
                
                if 'UPS' in alert_type:
                    alert_text =progress_ups_text(alert_text)
                else:
                    alert_text =progress_text(alert_text)

                msg_digest = f"{alert_text}\n{dif_alert.get('alert_time','')}"

            _LOGGER.info(f'{plugins_name}获取到的系统新通知如下:\n{msg_title}\n{msg_digest}')
            push_msg(msg_title, msg_digest)
            return True
        else:
            # _LOGGER.info(f'没有新通知')
            return False
def push_msg(msg_title, msg_digest):
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

