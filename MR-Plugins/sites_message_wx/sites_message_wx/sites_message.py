#!/usr/bin/env python3
from mbot.core.plugins import plugin
from mbot.core.plugins import PluginContext, PluginMeta
from mbot.openapi import mbot_api
from typing import Dict, Any
from urllib.parse import urljoin
from bs4 import BeautifulSoup, SoupStrainer
import time
import random
import re
import os
import requests
import logging
import yaml
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from datetime import datetime
server = mbot_api
_LOGGER = logging.getLogger(__name__)
site_list = server.site.list()
message_skip_list = ['mteam', 'pttime' 'mikanani', 'acgrip', 'sukebei', 'exoticaz', 'filelist', 'hares', 'iptorrents','rarbg']
notice_skip_list = ['mteam', 'pttime', 'mikanani', 'acgrip', 'sukebei', 'exoticaz', 'ttg', 'filelist', 'hares','iptorrents', 'rarbg']

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
         _LOGGER.error('「PT站内信和公告推送」获取推送用户失败，可能是设置了没保存成功或者还未设置')
         user_id = ''

@plugin.config_changed
def config_changed(config: Dict[str, Any]):
    global words,user_id,wecom_proxy_url,message_to_uid,qywx_channel_extra,corpid_extra,corpsecret_extra,agentid_extra,touser_extra
    _LOGGER.info('「PT站内信和公告推送」配置发生变更，加载新设置！')
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

@plugin.task('sites_message_wx', '定时获取站内信和公告', cron_expression='0 9,19 * * *')
def task():
    time.sleep(random.randint(1, 600))
    _LOGGER.info('开始获取站内信和公告')
    # site_notice()
    main()
    _LOGGER.info('所有站点站内信和公告获取完成')

@plugin.on_event(
    bind_event=['SiteSearchComplete', 'SiteListComplete'], order=1)
def on_site_search_complete(ctx: PluginContext, event_type: str, data: Dict):
    site_id = data.get('site_id')
    site_name = data.get('site_name')
    site_domain = data.get('domain')
    html = data.get('html')
    if site_id in message_skip_list:
        return
    if site_id == 'ssd':
        message_notify_box = 'a[style^="display"]'
    else:
        message_notify_box = 'a[href="messages.php"] > font'
    soup_tmp = SoupStrainer("a", href="messages.php")
    soup = BeautifulSoup(html, 'html.parser', parse_only=soup_tmp).select(message_notify_box)
    if soup:
        push_wx, access_token, agentid, touser, wecom_api_url = is_push_to_wx()
        for site in site_list:
            if site.site_name == site_name:
                site_cookie = site.cookie
                site_proxies = site.proxies
                site_user_agent = site.user_agent
                sites_message(site_domain, site_name, site_cookie, site_proxies, site_user_agent, site_id, push_wx, access_token, agentid, touser, wecom_api_url)
                break

def sites_message_by_manual(push_wx, access_token, agentid, touser, wecom_api_url):
    # push_wx, access_token, agentid, touser, wecom_api_url = is_push_to_wx()
    for site in site_list:
        site_id = site.site_id
        if site_id in message_skip_list:
            continue
        site_name = site.site_name
        site_domain = site.domain
        site_cookie = site.cookie
        site_proxies = site.proxies
        site_user_agent = site.user_agent
        sites_message(site_domain, site_name, site_cookie, site_proxies, site_user_agent, site_id, push_wx, access_token, agentid, touser, wecom_api_url)

def sites_message(site_domain, site_name, site_cookie, site_proxies, site_user_agent, site_id, push_wx, access_token, agentid, touser, wecom_api_url):
    _LOGGER.info(f'开始获取「{site_name}」站内信')
    try:
        message_list, messages_url, messages_item_url, count = get_nexusphp_message(site_name, site_domain, site_cookie, site_proxies, site_user_agent)
        if message_list:
            image_path = f'/data/plugins/sites_message_wx/pic/{site_id}.gif'
            try:
                if not os.path.exists(image_path):
                    image_path = f'/data/plugins/sites_message_wx/pic/msg_default.gif'
            except Exception as e:
                _LOGGER.error(f'检查文件是否存在时发生异常，原因：{e}')
            if count > 1:
                wecom_title = f'💌 {site_name}: {count} 条站内新信息'
                wecom_content_m = ''.join(message_list)
                wecom_content_m = wecom_content_m.replace('<line>', '')
                wecom_content_m = wecom_content_m.strip('\n')
                wecom_content = wecom_content_m.replace('\n', '<br/>')
                wecom_digest = re.sub(r'<.*?>', '', wecom_content_m) 
                content_source_url = messages_url
            else:
                wecom_title = message_list[0].split('<line>\n')[0]
                wecom_content = message_list[0].split('<line>\n')[1]
                wecom_content = wecom_content.strip('\n')
                wecom_title = wecom_title.replace('\n', '')
                wecom_title = re.sub(r'<.*?>', '', wecom_title)
                wecom_title = f'💌 {site_name}: {wecom_title}'
                wecom_title = wecom_title.replace('💬 ', '')
                wecom_title = wecom_title.replace('你的种子/帖子收到魔力值奖励', '收到魔力值奖励')
                wecom_title = wecom_title.replace('您正在下载或做种的种子被删除', '种子被删除')
                content_source_url = messages_item_url
                wecom_digest = re.sub(r'<.*?>', '', wecom_content)
            wecom_content = wecom_content.replace('\n', '<br/>')
            if push_wx:
                thumb_media_id = get_media_id(site_name, access_token, image_path)
                result = push_msg_wx(access_token, touser, agentid, wecom_title, thumb_media_id, content_source_url, wecom_digest, wecom_content, wecom_api_url)
                _LOGGER.info(f'「{site_name}」💌 有新站内信，企业微信推送结果: {result}')
            else:
                pic_url = 'https://raw.githubusercontent.com/Alano-i/wecom-notification/main/MR-Plugins/sites_message_wx/sites_message_wx/pic/msg_default.gif'
                result = push_msg_mr(wecom_title, wecom_digest, pic_url, content_source_url)
                _LOGGER.info(f'「{site_name}」💌 有新站内信，自选推送通道推送结果: {result}')
        else:
            _LOGGER.info(f'「{site_name}」无未读站内信，或通过关键词过滤后没有需要推送的新消息')
    except Exception as e:
        _LOGGER.error(f'获取「{site_name}」站内信失败，原因：{e}')
        return

def site_notice(push_wx, access_token, agentid, touser, wecom_api_url):
    # push_wx, access_token, agentid, touser, wecom_api_url = is_push_to_wx()
    for site in site_list:
        site_id = site.site_id
        site_name = site.site_name
        site_url = site.domain
        if not site_id:
            continue
        if site_id in notice_skip_list:
            continue
        _LOGGER.info(f'开始获取「{site.site_name}」站点公告')
        try:
            notice_list = get_nexusphp_notice(site.site_name, site.site_id, site.domain, site.cookie, site.proxies, site.user_agent)
            if notice_list:
                image_path = f'/data/plugins/sites_message_wx/pic/{site_id}.gif'
                try:
                    if not os.path.exists(image_path):
                        image_path = f'/data/plugins/sites_message_wx/pic/notice_default.gif'
                except Exception as e:
                    _LOGGER.error(f'检查文件是否存在时发生异常，原因：{e}')
                wecom_title = f'📢 {site_name}: {notice_list[1]}'
                wecom_content_m = f'<b><big>{notice_list[0]}</b></big>\n<small>{notice_list[2]}</small>'
                wecom_content = wecom_content_m.replace('\n', '<br/>')
                wecom_digest = re.sub(r'<.*?>', '', wecom_content_m)
                content_source_url = f'{site_url}'
                if push_wx:
                    thumb_media_id = get_media_id(site_name, access_token, image_path)
                    result = push_msg_wx(access_token, touser, agentid, wecom_title, thumb_media_id, content_source_url, wecom_digest, wecom_content, wecom_api_url)
                    _LOGGER.info(f'「{site_name}」📢 有新公告，企业微信推送结果: {result}')
                else:
                    pic_url = 'https://raw.githubusercontent.com/Alano-i/wecom-notification/main/MR-Plugins/sites_message_wx/sites_message_wx/pic/notice_default.gif'
                    result = push_msg_mr(wecom_title, wecom_digest, pic_url, content_source_url)
                    _LOGGER.info(f'「{site_name}」📢 有新公告，自选推送通道推送结果: {result}')
            else:
                _LOGGER.info(f'「{site_name}」无新公告')
        except Exception as e:
            _LOGGER.error(f'获取「{site.site_name}」站点公告失败，原因：{e}')
            continue

def get_nexusphp_message(site_name, site_url, cookie, proxies, user_agent):
    message_list = []
    sms_title = ''
    element_body = ''
    messages_item_url = ''
    message_url = ''
    count = 0
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
    message_url = 'messages.php?action=viewmailbox&box=1&unread=1'
    messages_url = urljoin(site_url, message_url)
    headers = {
        'cookie': cookie,
        'user-agent': user_agent,
    }
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    response = session.request("GET", messages_url, headers=headers, proxies=proxies, timeout=30).text
    soup_tmp = SoupStrainer("form", {"action": "messages.php"})
    soup = BeautifulSoup(response, 'html.parser', parse_only=soup_tmp)
    unread_list = soup.select(unread_selector)
    messages_item_url = ''
    for unread_item in unread_list:
        td = unread_item.parent.next_sibling.next_sibling
        sms_title = td.text
        sms_title = f'💬 {sms_title}'
        href = td.a['href']
        messages_item_url = urljoin(site_url, href)
        message_res = requests.request("GET", messages_item_url, headers=headers, proxies=proxies, timeout=30).text
        message_soup_tmp = SoupStrainer("td", {"colspan": "2"})
        message_soup = BeautifulSoup(message_res, 'html.parser', parse_only=message_soup_tmp)
        element_body = message_soup.select(body_selector)[0].text.strip()
        element_body = re.sub(r'[\n\r]+', '\n', element_body)
        element_body = re.sub(r'\[.*?\]', '', element_body)
        count = count + 1
        caption_content = f'<b><big>{sms_title.strip()}</b></big><line>\n<small>{element_body}</small>\n\n'
        message_list.append(caption_content)
    if message_list:
        _LOGGER.info(f'「关键字过滤前，未读站内信数量」{count}')
        message_list,count = word_ignore(site_name, message_list,count)
        _LOGGER.info(f'「关键字过滤后，未读站内信数量」{count}')
    return message_list, messages_url, messages_item_url, count

def get_nexusphp_notice(site_name, site_id, site_url, cookie, proxies, user_agent):
    sites_notice_selector = {
        'putao': {
            'notice_box_selector': 'td',
            'notice_box_attributes': {'class': 'text'},
            'notice_title_selector': 'td.text > ul > a',
            'notice_content_selector': 'td.text > ul > div',
        },
        'ssd': {
            'notice_box_selector': 'td',
            'notice_box_attributes': {'class': 'text'},
            'notice_title_selector': 'td.text > div > div:nth-child(1) > a',
            'notice_content_selector': 'td.text > div > div:nth-child(1) > div',
        },
        'hdchina': {
            'notice_box_selector': 'div',
            'notice_box_attributes': {'class': 'announcebox'},
            'notice_title_selector': 'div.announcebox > div.announce > h4',
            'notice_content_selector': 'div.announcebox > div.announce > h3',
        },
        'nexusphp': {
            'notice_box_selector': 'td',
            'notice_box_attributes': {'class': 'text'},
            'notice_title_selector': 'td.text > div > a',
            'notice_content_selector': 'td.text > div > div',
        }
    }
    if site_id not in sites_notice_selector.keys():
        site_id = 'nexusphp'
    notice_box_selector = sites_notice_selector[site_id].get('notice_box_selector')
    notice_box_attributes = sites_notice_selector[site_id].get('notice_box_attributes')
    notice_title_selector = sites_notice_selector[site_id].get('notice_title_selector')
    notice_content_selector = sites_notice_selector[site_id].get('notice_content_selector')
    notice_list = []
    xxx = ''
    notice_date_title = ''
    notice_content = ''
    notice_title = ''
    notice_date = ''
    notice_url = 'index.php'
    notice_url = urljoin(site_url, notice_url)
    headers = {
        'cookie': cookie,
        'user-agent': user_agent,
    }
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
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    response = session.request("GET", notice_url, headers=headers, proxies=proxies, timeout=30).text  
    soup_tmp = SoupStrainer(notice_box_selector, notice_box_attributes)
    soup = BeautifulSoup(response, 'html.parser', parse_only=soup_tmp)
    notice_date_title = soup.select(notice_title_selector)
    if notice_date_title:
        notice_date_title = notice_date_title[0].text.strip()
        try:
            notice_date, notice_title = notice_date_title.split(' - ')
        except Exception as e:
            notice_date, notice_title = notice_date_title.split(' -')
        notice_date = notice_date.replace('.', '-')
        notice_date = f'{notice_date} 公告'
    notice_content = soup.select(notice_content_selector)
    if notice_content:
        notice_content = notice_content[0].text.strip()
        notice_content = notice_content.strip()
        notice_content = re.sub(r'[\n\r]+', '\n', notice_content)
        notice_content = re.sub(r'\[.*?\]', '', notice_content)
    
    if notice_date and not notice_content:
        notice_content = '无文字内容，可能是图片公告！'

    if notice_date or notice_title or notice_content:
        notice_list = [notice_date, notice_title, notice_content]
        new_notice = {'date':notice_date, 'title':notice_title, 'content':notice_content}
        # new_notice = {'date':'notice_date', 'title':'notice_title', 'content':'notice_content'}
        if new_notice != server.common.get_cache('site_notice', site_name):
            server.common.set_cache('site_notice', site_name, new_notice)
        else:
            _LOGGER.info(f'「{site_name}」获取到的「最新公告」和「缓存公告」相同，不推送')
            notice_list = ''
    else:
        notice_list = ''
    xxx = server.common.get_cache('site_notice', site_name)
    _LOGGER.info(f'「{site_name}」公告的最新缓存为{xxx}')
    return notice_list

def word_ignore(site_name, message_list, count):
    word, hit = [], []
    if words:
        word = words.split(',')
        _LOGGER.info(f'「设定过滤关键词」{word}')
        for item in message_list:
            for i in word:
                if i in item:
                    hit.append(item)
                    break
        for hit_item in hit:
            message_list.remove(hit_item)
            count = count - 1
            _LOGGER.error(f'「{site_name}」未读站内信触发关键词过滤，将屏蔽此条消息，相关消息不会推送！')
        if not hit:
            _LOGGER.info(f'「{site_name}」未读站内信未触发关键词过滤')
    else:
        _LOGGER.info(f'未设定过滤关键词')
    return message_list,count

def is_push_to_wx():
    push_wx = True
    extra_flag = True
    wecom_api_url = 'https://qyapi.weixin.qq.com'
    access_token = ''
    agentid = ''
    touser = ''
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
        touser = server.user.get(user_id).qywx_user
        _LOGGER.info(f'获取到 MR 系统主干设置的的企业微信信息:「agentid: {agentid} corpid: {corpid} corpsecret: {corpsecret} touser: {touser}」')
        if not agentid or not corpid or not corpsecret or not touser:
            _LOGGER.error('企业微信信息获取失败或填写不完整')
            _LOGGER.error('在设置-设置企业微信页设置：「agentid」，「corpid」，「corpsecret」')
            _LOGGER.error('在用户管理页设置微信账号，获取方法参考: https://alanoo.notion.site/thumb_media_id-64f170f7dcd14202ac5abd6d0e5031fb')
            _LOGGER.error('本插件选用微信通道推送消息效果最佳，但现在没获取到，将采用默认消息通道推送')
            _LOGGER.error('默认消息通道推送：每个站点封面图无法一站一图，都是统一的')
            push_wx = False
    elif not user_id and not qywx_channel_extra:
        _LOGGER.error('未设置推送人，也没有设置独立微信应用参数，将采用默认消息通道推送')
        _LOGGER.error('默认消息通道推送：每个站点封面图无法一站一图，都是统一的')
        push_wx = False
    if (push_wx or qywx_channel_extra) and extra_flag:
        if wecom_proxy_url:
            _LOGGER.info(f'设置了微信白名单代理，地址是：{wecom_proxy_url}')
            wecom_api_url = wecom_proxy_url
        else:
            _LOGGER.info('未设置微信白名单代理，使用官方 api 地址: https://qyapi.weixin.qq.com')
        push_wx, access_token = getToken(corpid, corpsecret, wecom_api_url)
    return push_wx, access_token, agentid, touser, wecom_api_url

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
    url = wecom_api_url + "/cgi-bin/gettoken?corpid=" + corpid + "&corpsecret=" + corpsecret
    MAX_RETRIES = 3
    for i in range(MAX_RETRIES):
        try:
            r = requests.get(url)
            break
        except requests.RequestException as e:
            _LOGGER.error(f'处理异常，原因：{e}')
            time.sleep(2)
    if r.json()['errcode'] == 0:
        access_token = r.json()['access_token']
        return True, access_token
    else:
        _LOGGER.error('请求企业微信「access_token」失败,请检查企业微信各个参数是否设置正确，将采用默认消息通道推送！')
        _LOGGER.error('默认消息通道推送：每个站点封面图无法一站一图，都是统一的')
        return False, ''

def get_media_id(site_name, access_token, image_path):
    media_id_info_new = {}
    current_time = time.time()
    if server.common.get_cache('media_id_info', site_name):
        stored_time = server.common.get_cache('media_id_info', site_name)['stored_time']
        stored_time_datetime = datetime.fromtimestamp(stored_time)
        stored_time_str = stored_time_datetime.strftime("%Y-%m-%d %H:%M:%S")
        media_id = server.common.get_cache('media_id_info', site_name)['media_id']
        stored_modify_time = server.common.get_cache('media_id_info', site_name)['stored_modify_time']
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
    current_modify_time = os.stat(image_path).st_mtime
    current_modify_time = datetime.fromtimestamp(current_modify_time)
    current_modify_time = current_modify_time.strftime("%Y-%m-%d %H:%M:%S")
    if current_time - stored_time > 3 * 24 * 60 * 60 or not media_id or current_modify_time != stored_modify_time:
        _LOGGER.info(f'「{site_name}」上传的封面图片过期或有了新封面，将重新上传并获取新的「media_id」')
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
    querystring = {"access_token": access_token, "type": "image"}
    files = {"media": ("image.gif", open(image_path, "rb"))}
    MAX_RETRIES = 3
    for i in range(MAX_RETRIES):
        try:
            response = requests.request("POST", url, params=querystring, files=files)
            break
        except requests.RequestException as e:
            _LOGGER.error(f'「{site_name}」上传封面处理异常，原因：{e}')
            time.sleep(2)
    _LOGGER.info(f'「{site_name}」上传封面返回结果：{response.text}')
    if response.status_code == 200:
        resp_data = response.json()
        media_id = resp_data.get('media_id')
        return media_id
    else:
        _LOGGER.error(f'「{site_name}」上传封面失败，状态码：{response.status_code}')

def push_msg_wx(access_token, touser, agentid, wecom_title, thumb_media_id, content_source_url, wecom_digest, wecom_content, wecom_api_url):
    url = wecom_api_url + '/cgi-bin/message/send?access_token=' + access_token
    data = {
        "touser": touser,
        "msgtype": "mpnews",
        "agentid": agentid,
        "mpnews": {
            "articles": [
                {
                    "title" : wecom_title,
                    "thumb_media_id" : thumb_media_id,
                    "author" : "PT站内信",
                    "content_source_url" : content_source_url,
                    "digest" : wecom_digest,
                    "content" : wecom_content,
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
            return '已推送消息通知'
    except Exception as e:
        return f'消息推送异常，原因: {e}'
        pass

def main():
    push_wx, access_token, agentid, touser, wecom_api_url = is_push_to_wx()
    sites_message_by_manual(push_wx, access_token, agentid, touser, wecom_api_url)
    site_notice(push_wx, access_token, agentid, touser, wecom_api_url)
    
