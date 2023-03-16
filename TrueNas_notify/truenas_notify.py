#!/usr/bin/env python3
# Author: Alano
# Date: 2023/03/16
# 获取 TrueNA Scale 系统通知并推送到微信

import requests
import datetime
import json
import time
import os

##################################### 设置 #####################################
# server = mbot_api
plugins_name = 'TrueNA Scale 系统通知'
# TrueNA Scale 的IP地址或域名
truenas_server = 'https://truenas.xxx.com:9001'
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
            level = {
                'CRITICAL': '‼️ 严重',
                'WARNING':'⚠️ 警告',
                'NOTICE':'✉️ 通知',
                'INFO':'ℹ️ 信息'
            }
            type = {
                'ScrubFinished': '磁盘检修完成',
                'ZpoolCapacityNotice': '存储池容量提醒',
                'NTPHealthCheck': 'NTP 健康检查',
                'SMART': 'SMART异常'
            }
            if dif_alerts_num > 1:
                msg_title = f'💌 {dif_alerts_num} 条系统通知'
                msg_digest = ""
                for alert in dif_alerts:
                    alert_level = level.get(alert.get('alert_level',''),'')
                    alert_type = type.get(alert.get('alert_type', ''),'')

                    alert_text = alert.get('alert_text', '').replace('NTP health check failed', 'NTP 健康检查失败').replace('Scrub of pool', '存储池').replace('finished', '检查完成').replace('Space usage for pool', 'ZFS 存储池').replace('is', '的空间使用率为').replace('Optimal pool performance requires used space remain below 80%', '为保证最佳池性能，使用空间应保持在 80% 以下')
                    alert_text = alert_text.replace('Device:', '设备:').replace('ATA error count increased from', 'ATA 错误计数从').replace(' to ', ' 增加到 ').replace('REJECT', '无法连接')
                    alert_text = alert_text.replace('Currently unreadable (pending) sectors', '个当前无法读取的（待处理）扇区').replace('No Active NTP peers', '没有活动的NTP服务器')
                    
                    alert_time = alert.get('alert_time', '')
                    msg_digest += f"{alert_level} {alert_type}\n{alert_text}\n{alert_time}\n\n"
                msg_digest = msg_digest.strip()
            else:
                dif_alert = dif_alerts[0]
                msg_title = f"{level.get(dif_alert.get('alert_level',''),'')} {type.get(dif_alert.get('alert_type',''),'') }"
                
                alert_text = dif_alert.get('alert_text', '').replace('NTP health check failed', 'NTP 健康检查失败').replace('Scrub of pool', '存储池').replace('finished', '检查完成').replace('Space usage for pool', 'ZFS 存储池').replace('is', '的空间使用率为').replace('Optimal pool performance requires used space remain below 80%', '为保证最佳池性能，使用空间应保持在 80% 以下')
                alert_text = alert_text.replace('Device:', '设备:').replace('ATA error count increased from', 'ATA 错误计数从').replace(' to ', ' 增加到 ').replace('REJECT', '无法连接')
                alert_text = alert_text.replace('Currently unreadable (pending) sectors', '个当前无法读取的（待处理）扇区').replace('No Active NTP peers', '没有活动的NTP服务器')
                
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
