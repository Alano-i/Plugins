#!/usr/bin/env python3
from mbot.core.plugins import plugin
from mbot.core.plugins import PluginContext, PluginMeta
from mbot.openapi import mbot_api
from typing import Dict, Any
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import time
import os
# import sys
import yaml
from datetime import datetime
import re
import random
import requests
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
server = mbot_api
_LOGGER = logging.getLogger(__name__)

site_url = {
    'chdbits': 'https://chdbits.co',
    'HDHome': 'https://hdhome.org',
    'hdsky': 'https://hdsky.me',
    'hdchina': 'https://hdchina.org',
    'mteam': 'https://kp.m-team.cc',
    'lemonhd': 'https://lemonhd.org',
    'ourbits': 'https://ourbits.club',
    'ssd': 'https://springsunday.net',
    'keepfrds': 'https://pt.keepfrds.com',
    'pterclub': 'https://pterclub.com',
    'hdatmos': 'https://hdatmos.club',
    'beitai': 'https://beitai.pt',
    'soulvoice': 'https://pt.soulvoice.club',
    'audiences': 'https://audiences.me',
    'nicept': 'https://nicept.net',
    'pthome': 'https://pthome.net',
    'HDarea': 'https://hdarea.co',
    'HDTime': 'https://hdtime.org',
    'hd4fans': 'https://hd4fans.org',
    'hddolby': 'https://hddolby.com',
    'eastgame': 'https://pt.eastgame.org',
    'hdfans': 'https://hdfans.org',
    'discfan': 'https://discfan.net',
    'btschool': 'https://pt.btschool.club',
    'HDZone': 'https://hdzone.me',
    'gainbound': 'https://gainbound.net',
    'azusa': 'https://azusa.wiki',
    'ultrahd': 'https://ultrahd.net',
    'hhan': 'https://hhanclub.top',
    'hares': 'https://club.hares.top',
    'tjupt': 'https://tjupt.org',
    'leaves': 'https://leaves.red'
}

@plugin.after_setup
def after_setup(plugin_meta: PluginMeta, config: Dict[str, Any]):
    global words,user_id,wecom_proxy_url,message_to_uid,qywx_channel_extra,corpid_extra,corpsecret_extra,agentid_extra,touser_extra

    message_to_uid = config.get('uid')
    qywx_channel_extra = config.get('qywx_channel_extra')
    corpid_extra = config.get('corpid_extra')
    corpsecret_extra = config.get('corpsecret_extra')
    agentid_extra = config.get('agentid_extra')
    touser_extra = config.get('touser_extra')
    words = config.get('word_ignore')
    wecom_proxy_url = config.get('wecom_proxy_url')
    if message_to_uid:
        user_id = message_to_uid[0]
    else:
         _LOGGER.error('「PT站内信推送」获取推送用户失败，可能是设置了没保存或者还未设置')
         _LOGGER.error('「PT站内信推送」PS:设置保存后必须重启才会生效！')
         user_id = ''

    # msg_media_id = config.get('msg_media_id')
    # notice_media_id = config.get('notice_media_id')

@plugin.config_changed
def config_changed(config: Dict[str, Any]):
    global words,user_id,wecom_proxy_url,message_to_uid,qywx_channel_extra,corpid_extra,corpsecret_extra,agentid_extra,touser_extra

    message_to_uid = config.get('uid')
    qywx_channel_extra = config.get('qywx_channel_extra')
    corpid_extra = config.get('corpid_extra')
    corpsecret_extra = config.get('corpsecret_extra')
    agentid_extra = config.get('agentid_extra')
    touser_extra = config.get('touser_extra')
    words = config.get('word_ignore')
    wecom_proxy_url = config.get('wecom_proxy_url')
    if message_to_uid:
        user_id = message_to_uid[0]
    else:
         _LOGGER.error('「PT站内信推送」获取推送用户失败，可能是设置了没保存成功或者还未设置')
         user_id = ''
    
@plugin.task('sites_message_wx', 'PT站内信推送', cron_expression='0 9,19 * * *')
def task():
    time.sleep(random.randint(1, 120))
    _LOGGER.info('开始获取站内信和公告')
    main()
    _LOGGER.info('所有站点站内信和公告获取完成')

def sites_message():
    push_wx = True
    extra_flag = True
    if qywx_channel_extra:
        if corpid_extra and agentid_extra and corpsecret_extra and touser_extra:
            corpid = corpid_extra
            agentid = agentid_extra
            corpsecret = corpsecret_extra
            touser = touser_extra
            _LOGGER.error(f'设置的独立微信应用参数:「agentid: {agentid} corpid: {corpid} corpsecret: {corpsecret} touser: {touser}」')
        else:
            _LOGGER.error(f'设置的独立微信应用参数不完整，将采用默认消息通道推送')
            push_wx = False
            extra_flag = False

    if user_id and not qywx_channel_extra:
        corpid, agentid, corpsecret = get_qywx_info()
        # touser = get_qywx_user(user_id)
        touser = server.user.get(user_id).qywx_user
        _LOGGER.info(f'获取到 MR 系统主干设置的的企业微信信息:「agentid: {agentid} corpid: {corpid} corpsecret: {corpsecret} touser: {touser}」')
        if not agentid or not corpid or not corpsecret or not touser:
            _LOGGER.error('企业微信信息获取失败或填写不完整')
            _LOGGER.error('在设置-设置企业微信页设置：「agentid」，「corpid」，「corpsecret」')
            _LOGGER.error('在用户管理页设置微信账号，获取方法参考: https://alanoo.notion.site/thumb_media_id-64f170f7dcd14202ac5abd6d0e5031fb')
            _LOGGER.error('本插件选用微信通道推送消息效果最佳，但现在没获取到，将采用默认消息通道推送')
            _LOGGER.error('默认消息通道推送：每个站点封面图无法一站一图，都是统一的')
            push_wx = False
            # sys.exit()
    elif not user_id and not qywx_channel_extra:
        _LOGGER.error('未设置推送人，也没有设置独立微信应用参数，将采用默认消息通道推送')
        _LOGGER.error('默认消息通道推送：每个站点封面图无法一站一图，都是统一的')
        push_wx = False

    if (push_wx or qywx_channel_extra) and extra_flag:
       
        wecom_api_url = 'https://qyapi.weixin.qq.com'
        if wecom_proxy_url:
            _LOGGER.info(f'设置了微信白名单代理，地址是：{wecom_proxy_url}')
            wecom_api_url = wecom_proxy_url
        else:
            _LOGGER.info('未设置微信白名单代理，使用官方 api 地址: https://qyapi.weixin.qq.com')
        access_token, push_wx = getToken(corpid, corpsecret, wecom_api_url)

    site_list = server.site.list()
    for site in site_list:
        site_id = site.site_id
        site_name = site.site_name
        if not site_id:
            continue
        if site_id not in site_url:
            continue
        _LOGGER.info(f'开始获取「{site_name}」站内信和公告')
        try:
            caption_content_list,count,message_url,message_item_url,notice_list = get_nexusphp_message(site_url[site_id], site.cookie, site.proxies, site_name)
            if caption_content_list or notice_list:
                image_path = f'/data/plugins/sites_message_wx/pic/{site_id}.gif'
                try:
                    # 检查 image_path 指向的文件是否存在
                    if not os.path.exists(image_path):
                        if caption_content_list:
                            image_path = f'/data/plugins/sites_message_wx/pic/msg_default.gif'
                        elif notice_list:
                            image_path = f'/data/plugins/sites_message_wx/pic/notice_default.gif'
                except Exception as e:
                    _LOGGER.error(f'检查文件是否存在时发生异常，原因：{e}')
                if push_wx:
                    thumb_media_id = get_media_id(site_name, access_token, image_path)
            if caption_content_list:
                if count > 1:
                    wecom_title = f'💌 {site_name}: {count} 条站内新信息'
                    wecom_content_m = ''.join(caption_content_list)
                    wecom_content_m = wecom_content_m.replace('<line>', '')
                    # 去掉首尾换行符
                    wecom_content_m = wecom_content_m.strip('\n')
                    wecom_content = wecom_content_m.replace('\n', '<br/>')
                    wecom_digest = re.sub(r'<.*?>', '', wecom_content_m) 
                    content_source_url = message_url
                else:
                    wecom_title = caption_content_list[0].split('<line>\n')[0]
                    wecom_content = caption_content_list[0].split('<line>\n')[1]
                    wecom_content = wecom_content.strip('\n')
                    wecom_title = wecom_title.replace('\n', '')
                    wecom_title = re.sub(r'<.*?>', '', wecom_title)
                    wecom_title = f'💌 {site_name}: {wecom_title}'
                    wecom_title = wecom_title.replace('💬 ', '')
                    wecom_title = wecom_title.replace('你的种子/帖子收到魔力值奖励', '收到魔力值奖励')
                    wecom_title = wecom_title.replace('您正在下载或做种的种子被删除', '种子被删除')
                    content_source_url = message_item_url
                    wecom_digest = re.sub(r'<.*?>', '', wecom_content)
                wecom_content = wecom_content.replace('\n', '<br/>')
                # 推送站内信
                if push_wx:
                    result = push_msg_wx(access_token, touser, agentid, wecom_title, thumb_media_id, content_source_url, wecom_digest, wecom_content, wecom_api_url)
                    _LOGGER.info(f'「{site_name}」💌 有新站内信，企业微信推送结果: {result}')
                else:
                    pic_url = 'https://raw.githubusercontent.com/Alano-i/wecom-notification/main/MR-Plugins/sites_message_wx/sites_message_wx/pic/msg_default.gif'
                    result = push_msg_mr(wecom_title, wecom_digest, pic_url, content_source_url)
                    _LOGGER.info(f'「{site_name}」💌 有新站内信，自选推送通道推送结果: {result}')
            else:
                _LOGGER.info(f'「{site_name}」无未读站内信，或通过关键词过滤后没有需要推送的新消息')
            if notice_list:
                wecom_title = f'📢 {site_name}: {notice_list[1]}'
                wecom_content_m = f'<b><big>{notice_list[0]}</b></big>\n<small>{notice_list[2]}</small>'
                wecom_content = wecom_content_m.replace('\n', '<br/>')
                wecom_digest = re.sub(r'<.*?>', '', wecom_content_m)
                content_source_url = f'{site_url}'
                # 推送公告
                if push_wx:
                    result = push_msg_wx(access_token, touser, agentid, wecom_title, thumb_media_id, content_source_url, wecom_digest, wecom_content, wecom_api_url)
                    _LOGGER.info(f'「{site_name}」📢 有新公告，企业微信推送结果: {result}')
                else:
                    pic_url = 'https://raw.githubusercontent.com/Alano-i/wecom-notification/main/MR-Plugins/sites_message_wx/sites_message_wx/pic/notice_default.gif'
                    result = push_msg_mr(wecom_title, wecom_digest, pic_url, content_source_url)
                    _LOGGER.info(f'「{site_name}」📢 有新公告，自选推送通道推送结果: {result}')
            else:
                _LOGGER.info(f'「{site_name}」无新公告')
        except Exception as e:
            _LOGGER.error(f'发生错误，原因：{e}')
            continue

# def get_qywx_user(id):
#     result = ''
#     conn = sqlite3.connect('/data/db/main.db')
#     cursor = conn.cursor()
#     cursor.execute('SELECT qywx_user FROM user WHERE id=?', (id,))
#     result = cursor.fetchone()
#     result = result[0]
#     conn.close()
#     return result

def get_qywx_info():
    try:
        yml_file = "/data/conf/base_config.yml"
        with open(yml_file, encoding='utf-8') as f:
            yml_data = yaml.load(f, Loader=yaml.FullLoader)
        for channel in yml_data['notify_channel']:
            if channel['enable']:
                agentid = channel.get('agentid')
                corpid = channel.get('corpid')
                corpsecret = channel.get('corpsecret')
                return corpid, agentid, corpsecret
    except Exception as e:
        _LOGGER.error(f'获取「企业微信配置信息」错误，可能 MR 中填写的信息有误或不全: {e}')
        pass
    return '','',''

def getToken(corpid, corpsecret, wecom_api_url):
    # 获取access_token
    url = wecom_api_url + "/cgi-bin/gettoken?corpid=" + corpid + "&corpsecret=" + corpsecret
    MAX_RETRIES = 3
    for i in range(MAX_RETRIES):
        try:
            r = requests.get(url)
            # _LOGGER.error(f'r.json: {r.json()}')
            break
        except requests.RequestException as e:
            _LOGGER.error(f'处理异常，原因：{e}')
            time.sleep(2)
    if r.json()['errcode'] == 0:
        access_token = r.json()['access_token']
        return access_token, True
    else:
        _LOGGER.error('请求企业微信「access_token」失败,请检查企业微信各个参数是否设置正确，将采用默认消息通道推送！')
        _LOGGER.error('默认消息通道推送：每个站点封面图无法一站一图，都是统一的')
        return '', False

def get_media_id(site_name, access_token, image_path):
    media_id_info_new = {}
    # 获取当前时间
    current_time = time.time()
    if server.common.get_cache('media_id_info', site_name):
         # 获取存在缓存中的时间和media_id
        stored_time = server.common.get_cache('media_id_info', site_name)['stored_time']
        stored_time_datetime = datetime.fromtimestamp(stored_time)
        stored_time_str = stored_time_datetime.strftime("%Y-%m-%d %H:%M:%S")
        media_id = server.common.get_cache('media_id_info', site_name)['media_id']
        stored_modify_time = server.common.get_cache('media_id_info', site_name)['stored_modify_time']
        # stored_modify_time = '2022-10-10 22:22:22'
        _LOGGER.info(f'「{site_name}」缓存的封面图片修改时间: {stored_modify_time}')
        _LOGGER.info(f'「{site_name}」上次传图到素材库的时间: {stored_time_str}, 3天有效, 过期自动再次上传获取新的 media_id')
        media_id_dict = {media_id}
        _LOGGER.info(f'「{site_name}」当前正在使用(缓存)的 「media_id」: {media_id_dict}')
    else:
        _LOGGER.info(f'「{site_name}」缓存的封面图片修改时间: 还未缓存')
        _LOGGER.info(f'「{site_name}」上次传图到素材库的时间: 还未上传过, 3天有效, 过期自动再次上传获取新的 media_id')
        stored_time = current_time
        stored_modify_time = '2022-02-02 22:22:22'
        media_id = ''
    # 获取文件的修改时间
    current_modify_time = os.stat(image_path).st_mtime
    # 格式化时间为"年-月-日 时分秒"
    current_modify_time = datetime.fromtimestamp(current_modify_time)
    current_modify_time = current_modify_time.strftime("%Y-%m-%d %H:%M:%S")
    # 如果 当前时间与存储的时间差大于 3 天，就调用上传图片的函数并重新获取 media_id
    if current_time - stored_time > 3 * 24 * 60 * 60 or not media_id or current_modify_time != stored_modify_time:
        media_id = upload_image_and_get_media_id(site_name, access_token, image_path)
        media_id_dict = {media_id}
        _LOGGER.info(f'「{site_name}」上传封面图片后获得的最新「media_id」: {media_id_dict}')
        media_id_info_new = {'media_id':media_id, 'stored_time':current_time, 'stored_modify_time':current_modify_time}
        server.common.set_cache('media_id_info', site_name, media_id_info_new)
    else:
        pass
    stored_media_id_info = server.common.get_cache('media_id_info', site_name)
    _LOGGER.info(f'「{site_name}」已缓存的 「media_id 信息」: {stored_media_id_info}')
    return media_id

def upload_image_and_get_media_id(site_name, access_token, image_path):
    url = "https://qyapi.weixin.qq.com/cgi-bin/media/upload"
    # /cgi-bin/material/add_material 永久素材接口，但需要授权，不知道该怎么授权 ，/cgi-bin/media/upload 临时素材接口，3天有效
    querystring = {"access_token": access_token, "type": "image"}
    files = {"media": ("image.gif", open(image_path, "rb"))}
    MAX_RETRIES = 3
    for i in range(MAX_RETRIES):
        try:
            response = requests.request("POST", url, params=querystring, files=files)
            break
        except requests.RequestException as e:
            _LOGGER.error(f'处理异常，原因：{e}')
            time.sleep(2)
    _LOGGER.info(f'上传封面返回结果：{response.text}')
    # 解析响应
    if response.status_code == 200:
        resp_data = response.json()
        media_id = resp_data.get('media_id')
        return media_id
    else:
        _LOGGER.error(f'上传图片失败，状态码：{response.status_code}')

def push_msg_wx(access_token, touser, agentid, wecom_title, thumb_media_id, content_source_url, wecom_digest, wecom_content, wecom_api_url):
    # 发送消息
    url = wecom_api_url + '/cgi-bin/message/send?access_token=' + access_token
    data = {
        "touser": touser,
        "msgtype": "mpnews",
        "agentid": agentid,
        "mpnews": {
            "articles": [
                {
                    "title" : wecom_title,
                    "thumb_media_id" : thumb_media_id,              # 卡片头部图片链接，此图片存储在企业微信中
                    "author" : "PT站内信",                           # 点击卡片进入下级页面后，时间日期的旁边的作者
                    "content_source_url" : content_source_url,      # 阅读原文链接
                    "digest" : wecom_digest,                        # 图文消息的描述
                    "content" : wecom_content,                      # 点击卡片进入下级页面后展示的消息内容
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
            r = requests.post(url, json=data)
            break
        except requests.RequestException as e:
            _LOGGER.error(f'处理异常，原因：{e}')
            time.sleep(2)
    if r is None:
        _LOGGER.error('请求「推送接口」失败')
    else:
        return r.json()

# def push_msg_mr(wecom_title, wecom_digest, pic_url, content_source_url):
def push_msg_mr(msg_title, message, pic_url, link_url):
    try:
        if message_to_uid:
            for _ in message_to_uid:
                try:
                    server.notify.send_message_by_tmpl('{{title}}', '{{a}}', {
                        'title': msg_title,
                        'a': message,
                        'pic_url': pic_url,
                        'link_url': link_url
                    }, to_uid=_)
                    return '已推送消息通知'
                except Exception as e:
                    return f'消息推送异常，原因: {e}'
                    pass
        else:
            server.notify.send_message_by_tmpl('{{title}}', '{{a}}', {
                'title': msg_title,
                'a': message,
                'pic_url': pic_url,
                'link_url': link_url
            })
            # _LOGGER.info(f'「已推送消息通知」')
            return '已推送消息通知'
    except Exception as e:
                    # _LOGGER.error(f'消息推送异常，原因: {e}')
                    return f'消息推送异常，原因: {e}'
                    pass

def get_nexusphp_message(site_url, cookie, proxies, site_name):
    caption_content_list = []
    date_and_title = []
    notice_list = []
    sms_title = ''
    element_body = ''
    message_item_url = ''
    message_url = ''
    notice_url = ''
    xxx = ''
    count = 0

    notice_title_selector = 'td.text > div > a'
    notice_content_selector = 'td.text > div > div'

    unread_selector = 'td > img[alt="Unread"]'
    body_selector = 'td[colspan*="2"]'

    if proxies:
        if proxies.startswith('http'):
            proxies = {
                'http': proxies
            }
        elif proxies.startswith('socks5'):
            proxies = {
            'socks5': proxies
            }
    else:
        proxies = None

    # 站内信
    message_url = '/messages.php?action=viewmailbox&box=1&unread=1'
    message_url = urljoin(site_url, message_url)
    headers = {
        'cookie': cookie,
    }
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    response = session.request("GET", message_url, headers=headers, proxies=proxies, timeout=30).text
    # response = requests.request("GET", message_url, headers=headers, proxies=proxies, timeout=30).text
    soup = BeautifulSoup(response, 'html.parser')
    unread_list = soup.select(unread_selector)
    for unread_item in unread_list:
        td = unread_item.parent.next_sibling.next_sibling
        sms_title = td.text
        sms_title = f'💬 {sms_title}'
        href = td.a['href']
        message_item_url = urljoin(site_url, href)
        message_res = session.request("GET", message_item_url, headers=headers, proxies=proxies, timeout=30).text
        # message_res = requests.request("GET", message_item_url, headers=headers, proxies=proxies, timeout=30).text
        message_soup = BeautifulSoup(message_res, 'html.parser')
        element_body = message_soup.select(body_selector)[0].text.strip()
        element_body = re.sub(r'[\n\r]+', '\n', element_body)
        element_body = re.sub(r'\[.*?\]', '', element_body)
        # 计数
        count = count + 1
        caption_content = f'<b><big>{sms_title}</b></big><line>\n<small>{element_body}</small>\n\n'
        caption_content_list.append(caption_content)
    
    # 获取最新公告
    # notice_url = '/index.php'
    # notice_url = urljoin(site_url, notice_url)
    notice_url = site_url
    notice_response = session.request("GET", notice_url, headers=headers, proxies=proxies, timeout=30).text    
    soup = BeautifulSoup(notice_response, 'html.parser')
    # _LOGGER.error(f'soup: {soup}')
    date_and_title = soup.select(notice_title_selector)
    if date_and_title:
        date_and_title = date_and_title[0].text.strip()
        notice_date, notice_title = date_and_title.split(' - ')
        notice_date = notice_date.replace('.', '-')
        notice_date = f'{notice_date} 公告'
    else:
        notice_date = ''
        notice_title = ''
        # _LOGGER.error(f'「{site_name}」获取公告失败')

    notice_content = soup.select(notice_content_selector)
    if notice_content:
        notice_content = notice_content[0].text.strip()
        notice_content = notice_content.strip()
        notice_content = re.sub(r'[\n\r]+', '\n', notice_content)
        notice_content = re.sub(r'\[.*?\]', '', notice_content)
    else:
        notice_content = ''
    # notice_content = '研究决定明天为庆祝站点100周年'

    if site_name == '不可说'  and notice_content:
        notice_content = notice_content.replace('\n【参与讨论】', '')
        date_and_title, notice_content = notice_content.split(' \n')
        notice_content = notice_content.strip()
        date_and_title = date_and_title.strip()
        notice_date, notice_title = date_and_title.split(' - ')
        notice_date = notice_date.replace('.', '-')
        notice_date = f'{notice_date} 新公告'
        
    # notice_list = [notice_date, notice_title, notice_content]
    # notice_list = ['2022-12-28','站点开邀通知','研究决定明天为庆祝站点100周年，开放邀请！\n 望周知，积极参加！']

    if notice_date and notice_title and notice_content:
    # if notice_list:
        new_notice = {'date':notice_date, 'title':notice_title, 'content':notice_content}
        # new_notice = {'date':notice_list[0], 'title':notice_list[1], 'content':notice_list[2]}
        old_notice = server.common.get_cache('site_notice', site_name)
        notice_list = [notice_date, notice_title, notice_content]
        if new_notice != old_notice:
            server.common.set_cache('site_notice', site_name, new_notice)
        else:
            notice_list = []
            _LOGGER.info(f'「{site_name}」获取到的「最新公告」和「缓存公告」相同，不推送')
            # _LOGGER.info(f'「{site_name}」无新公告')
    else:
        _LOGGER.error(f'「{site_name}」获取公告失败')
        notice_list = ''
    xxx = server.common.get_cache('site_notice', site_name)
    _LOGGER.info(f'「{site_name}」公告的最新缓存为{xxx}')

    if caption_content_list:
        _LOGGER.info(f'「关键字过滤前，未读站内信数量」{count}')
        # 关键字检查
        caption_content_list,count = word_ignore(site_name, caption_content_list,count)
        _LOGGER.info(f'「关键字过滤后，未读站内信数量」{count}')
    # count = 3   
    # caption_content_list = ['站点开邀通知<line>\n这是内容']
    # caption_content_list = ['<b><big>💬 等级变化</b></big><line>\n<small>你被降级为Crazy User\n\n', "<b><big>💬 种子被删除</b></big><line>\n<small>你正在下载或做种的种子 ' The Mortal Ascention'被管理员删除。原因：Dupe!</small>\n\n", "<b><big>💬 欢迎!</b></big><line>\n<small>祝贺你，'站点用户名'，\n你已成为Our的一员，\n我们真诚地欢迎你的加入！\n请务必先阅读[url=rules.php][b]规则[/b][/url]，提问前请自行参考[url=faq.php][b]常见问题[/b][/url],有空也请到[url=forums.php][b]论坛[/b][/url]看看。 \n祝你愉快。</small>\n\n"]
    # notice_list = ['2022-12-28','站点开邀通知','研究决定明天为庆祝站点100周年，开放邀请！\n 望周知，积极参加！']
    return caption_content_list,count,message_url,message_item_url,notice_list

def word_ignore(site_name, caption_content_list, count):
    word, hit = [], []
    if words:
        word = words.split(',')
        _LOGGER.info(f'「设定过滤关键词」{word}')
        for item in caption_content_list:
            for i in word:
                if i in item:
                    hit.append(item)
                    break
        for hit_item in hit:
            caption_content_list.remove(hit_item)
            count = count - 1
            _LOGGER.error(f'「{site_name}」未读站内信触发关键词过滤，将屏蔽此条消息，相关消息不会推送！')
        if not hit:
            _LOGGER.info(f'「{site_name}」未读站内信未触发关键词过滤')
    else:
        _LOGGER.info(f'未设定过滤关键词')
    return caption_content_list,count

def main():
    sites_message()
