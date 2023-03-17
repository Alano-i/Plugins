#!/usr/bin/env python3
# Author: Alano
# Date: 2023/03/16
# 获取 TrueNA Scale 系统通知并推送到微信

import requests
import datetime
import json
import time
import os
import re
import ast

##################################### 设置 #####################################
# server = mbot_api
plugins_name = 'TrueNA Scale 系统通知'
# TrueNA Scale 的IP地址或域名
truenas_server = 'https://truenas.xxx.com:8888'
# TrueNA Scale API TOKEN,在web页右上角，点击用户头像，选API密钥
api_token = ""
# 企业微信代理，按需设置
wecom_proxy_url = ''
#企业微信 touser
touser = ''
#企业微信 corpid
corpid = ''
#企业微信 corpsecret
corpsecret = ''
#企业微信 agentid
agentid = ''
#微信推送封面
pic_url = 'https://raw.githubusercontent.com/Alano-i/wecom-notification/main/TrueNas_notify/truenas_notify_logo.jpg'
##################################### 设置 #####################################

def convert_seconds_to_mmss(seconds):
    """
    将秒数转换为 mm:ss 的格式。
    """
    minutes = seconds // 60
    seconds = seconds % 60
    return "{:02d} 分 {:02d} 秒".format(minutes, seconds)

def progress_device_text(text):
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

def progress_scrub_text(text):
    # 构造正则表达式
    pattern = r"Scrub of pool '(.+)' finished\."
    # 使用正则表达式匹配字符串
    match = re.search(pattern, text)
    if match:
        # 提取池名
        pool_name = match.group(1)
        # 重新组合字符串
        result = f"存储池'{pool_name}'检查完成"
    else:
        # 没有匹配到，直接返回原字符串
        result = text
    return result

def progress_ups_text(alert_text):
    battery_charge = re.search(r"battery\.charge:\s*(\d+)", alert_text)
    battery_charge_low = re.search(r"battery\.charge\.low:\s*(\d+)", alert_text)
    battery_runtime = re.search(r"battery\.runtime:\s*(\d+)", alert_text)
    battery_runtime_low = re.search(r"battery\.runtime\.low:\s*(\d+)", alert_text)
    alert_text = f"电池总电量：{battery_charge.group(1)}%\n电池可运行：{convert_seconds_to_mmss(battery_runtime.group(1))}\n切换到低电量临界电量：{battery_charge_low.group(1)}%\n切换到低电量等待时间：{battery_runtime_low.group(1)}秒"
    return alert_text

def progress_space_text(text):
    # 构造正则表达式
    pattern = r'Space usage for pool (["\'])(.+)\1 is (\d+)%\. Optimal pool performance requires used space remain below 80%\.'

    # 使用正则表达式匹配字符串
    match = re.search(pattern, text)

    if match:
        # 提取池名和空间使用率
        pool_name = match.group(2)
        usage_percent = match.group(3)

        # 重新组合字符串
        result = f'ZFS 存储池 "{pool_name}" 的空间使用达到 {usage_percent}%. 为保证最佳池性能，使用空间应保持在 80% 以下.'
    else:
        # 没有匹配到，直接返回原字符串
        result = text

    return result

def progress_ntp_text(text):
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

def progress_text(alert_text):
    alert_text = progress_scrub_text(alert_text)
    alert_text = progress_space_text(alert_text)
    alert_text = progress_device_text(alert_text)
    alert_text = progress_ntp_text(alert_text)
    return alert_text

def get_truenas_alert():
    truenas_alert_api_url = f"{truenas_server}/api/v2.0/alert/list"
    # 构建请求头
    headers = {
        'Content-Type': 'application/json',
        "Authorization": f"Bearer {api_token}"
    }
    # 请求系统通知
    response = requests.get(truenas_alert_api_url, headers=headers, timeout=20)
    # 解析请求返回
    json_data = json.loads(response.text)
    if json_data:
        alert_num = len(json_data)
        try:
            # 从文件中读取缓存内容并存储到old_alerts变量中
            if not os.path.exists("truenas_alerts_cache.txt"):
                with open("truenas_alerts_cache.txt", "w") as f:
                    f.write("")
            with open("truenas_alerts_cache.txt") as f:
                old_alerts = json.loads(f.read())
        except Exception as e:
            print(f'{plugins_name}读取缓存异常，原因: {e}')
            old_alerts = []
        
        # 遍历所有alert并按alert_time倒序排序
        json_data = sorted(json_data, key=lambda x: x['datetime']['$date'], reverse=True)
        # old_alerts = server.common.get_cache('notify', 'alerts')
        # old_alerts = []
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
        if old_alerts != alerts:
            # server.common.set_cache('notify', 'alerts', alerts)
            try:
                # 从文件中读取缓存内容并存储到old_alerts变量中
                with open("truenas_alerts_cache.txt", "w") as f:
                    f.write(json.dumps(alerts))
            except Exception as e:
                print(f'{plugins_name}写入缓存异常，原因: {e}')

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
                'UPSCommbad': 'UPS 断开连接',
                'SMART': 'SMART异常'
            }
            if dif_alerts_num > 1:
                msg_title = f'💌 {dif_alerts_num} 条系统通知'
                msg_digest = ""
                for alert in dif_alerts:
                    alert_level = level_list.get(alert.get('alert_level',''), alert.get('alert_level',''))
                    alert_type = type_list.get(alert.get('alert_type', ''), alert.get('alert_type', ''))
                    alert_text = alert.get('alert_text', '')

                    if 'UPS' in alert_type:
                        if alert_type == 'UPSCommbad':
                            alert_text = '与 UPS 通信丢失，无法获取电池数据'
                        else:
                            alert_text =progress_ups_text(alert_text)
                    else:
                        alert_text =progress_text(alert_text)
                        
                    alert_time = alert.get('alert_time', '')
                    msg_digest += f"{alert_level} {alert_type}\n{alert_text}\n{alert_time}\n\n"
                msg_digest = msg_digest.strip()
            
            else:
                if not dif_alerts:
                    print('没有获取到新通知')
                    return
                dif_alert = dif_alerts[0]
                msg_title = f"{level_list.get(dif_alert.get('alert_level',''), alert.get('alert_level',''))} {type_list.get(dif_alert.get('alert_type',''), alert.get('alert_type', '')) }"
                alert_type = dif_alert.get('alert_type', '')
                alert_text = dif_alert.get('alert_text', '')
                
                if 'UPS' in alert_type:
                    if alert_type == 'UPSCommbad':
                        alert_text = '与 UPS 通信丢失，无法获取电池数据'
                    else:
                        alert_text =progress_ups_text(alert_text)
                else:
                    alert_text =progress_text(alert_text)

                msg_digest = f"{alert_text}\n{dif_alert.get('alert_time','')}"
            push_msg_wx(msg_title, msg_digest)
            print(f"{msg_title}\n{msg_digest}")
        else:
            print('获取到的通知与相同，不发送通知')

def getToken(corpid, corpsecret, wecom_api_url):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.50'}
    url = f'{wecom_api_url}/cgi-bin/gettoken?corpid={corpid}&corpsecret={corpsecret}'
    MAX_RETRIES = 3
    for i in range(MAX_RETRIES):
        try:
            r = requests.get(url, headers=headers, timeout=20)
            # print(f'{plugins_name}尝试 {i+1} 次后，请求「获取token接口」成功')
            break
        except requests.RequestException as e:
            print(f'{plugins_name}第 {i+1} 次尝试，请求「获取token接口」异常，原因：{e}')
            time.sleep(2)
    if r.json()['errcode'] == 0:
        access_token = r.json()['access_token']
        return access_token
    else:
        print(f'{plugins_name}请求企业微信「access_token」失败')
        return ''

                
def push_msg_wx(msg_title, msg_digest):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.50'}
    wecom_api_url = 'https://qyapi.weixin.qq.com'
    if wecom_proxy_url:
        wecom_api_url = wecom_proxy_url
    access_token = getToken(corpid, corpsecret, wecom_api_url)

    url = f'{wecom_api_url}/cgi-bin/message/send?access_token={access_token}'
    
    data = {
        "touser": touser,
        "msgtype": "news",
        "agentid": agentid,
        "news": {
            "articles": [
                {
                    "title" : msg_title,
                    "description" : msg_digest,
                    "url" : '',
                    "picurl" : pic_url,
                }
            ]
        },
        "safe": 0,
        "enable_id_trans": 0,
        "enable_duplicate_check": 0,
        "duplicate_check_interval": 1800
    }
    MAX_RETRIES = 3
    for i in range(MAX_RETRIES):
        try:
            r = requests.post(url, json=data, headers=headers, timeout=20)
            # print(f'{plugins_name}尝试 {i+1} 次后，请求【推送接口】成功')
            break
        except requests.RequestException as e:
            print(f'{plugins_name}第 {i+1} 次尝试，请求【推送接口】异常，原因：{e}')
            time.sleep(2)
    if r is None:
        print(f'{plugins_name}请求【推送接口】失败')
    elif r.json()['errcode'] != 0:
        print(f'{plugins_name}通过设置的微信参数推送失败')
    elif r.json()['errcode'] == 0:
        print(f'{plugins_name}通过设置的微信参数推送消息成功')

if __name__ == '__main__':
    get_truenas_alert()
