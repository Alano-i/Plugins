from mbot.core.plugins import plugin
from mbot.core.plugins import PluginContext, PluginMeta
from mbot.openapi import mbot_api
from typing import Dict, Any

from urllib.parse import urljoin
from bs4 import BeautifulSoup, SoupStrainer
import time
import random
import requests
import logging
import httpx

server = mbot_api
_LOGGER = logging.getLogger(__name__)
site_list = server.site.list()
message_skip_list = ['mteam', 'pttime', 'mikanani', 'acgrip', 'sukebei', 'exoticaz', 'filelist', 'hares', 'iptorrents',
                     'rarbg']
announcement_skip_list = ['mteam', 'U2', 'pttime', 'ttg', 'mikanani', 'acgrip', 'sukebei', 'exoticaz', 'filelist',
                          'hares',
                          'iptorrents', 'rarbg']
site_pic = {
    "audiences": "https://s2.loli.net/2023/02/07/vxzLD4O62mJKcu5.gif",
    "chdbits": "https://s2.loli.net/2023/02/07/V7mFSig19e3RO2a.gif",
    "hares": "https://s2.loli.net/2023/02/07/8RsCJmpthMlaPDS.gif",
    "hdchina": "https://s2.loli.net/2023/02/07/1e7v9crskN3hCqw.gif",
    "HDHome": "https://s2.loli.net/2023/02/07/hHbu4qyeO2x3wBG.gif",
    "hdsky": "https://s2.loli.net/2023/02/07/HXkWuKgz8ACeEGQ.gif",
    "hhan": "https://s2.loli.net/2023/02/07/oLHMi9N7QTpj2Yd.gif",
    "keepfrds": "https://s2.loli.net/2023/02/07/t9ljcArROxf41Do.gif",
    "lemonhd": "https://s2.loli.net/2023/02/07/vH3NyV6b1irDF5W.gif",
    "msg_default": "https://s2.loli.net/2023/02/07/IrlaNtgLXWh8b7Q.gif",
    "mteam": "https://s2.loli.net/2023/02/07/UnmKgS1pGjkeDP5.gif",
    "notice_default": "https://s2.loli.net/2023/02/07/9Fu6wADRKzqMOcx.gif",
    "opencd": "https://s2.loli.net/2023/02/07/8CjIHqJbhtV2cdL.gif",
    "outbits": "https://s2.loli.net/2023/02/07/7WU51fKyRBGA8En.gif",
    "pterclub": "https://s2.loli.net/2023/02/07/ECOLMon7Xm9TWGy.gif",
    "ssd": "https://s2.loli.net/2023/02/07/dB5HoA8gyk1qwQv.gif",
    "tjupt": "https://s2.loli.net/2023/02/07/pADHXnNoErxOJtY.gif",
    "ultrahd": "https://s2.loli.net/2023/02/07/sGxvjEy8g9aYDwV.gif",
}


@plugin.after_setup
def after_setup(plugin_meta: PluginMeta, config: Dict[str, Any]):
    global message_to_uid
    message_to_uid = config.get('uid')
    global words
    words = config.get('word_ignore')
    global img_api
    img_api = config.get('img_api')
    if not img_api:
        img_api = "https://api.r10086.com/img-api.php?type=P%E7%AB%99%E7%B3%BB%E5%88%974"


@plugin.config_changed
def config_changed(config: Dict[str, Any]):
    global message_to_uid
    message_to_uid = config.get('uid')
    global words
    words = config.get('word_ignore')
    global img_api
    img_api = config.get('img_api')
    if not img_api:
        img_api = "https://api.r10086.com/img-api.php?type=P%E7%AB%99%E7%B3%BB%E5%88%974"


@plugin.task('site_messages', '定时获取站点公告', cron_expression='0 0 * * *')
def site_messages_task():
    time.sleep(random.randint(1, 600))
    site_announcement()


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
    elif site_id == 'U2':
        message_notify_box = 'a[style^="color"]'
    else:
        message_notify_box = 'a[href="messages.php"] > font'
    soup_tmp = SoupStrainer("a", href="messages.php")
    soup = BeautifulSoup(html, 'html.parser', parse_only=soup_tmp).select(message_notify_box)
    if soup:
        for site in site_list:
            if site.site_name == site_name:
                site_cookie = site.cookie
                site_proxies = site.proxies
                site_user_agent = site.user_agent
                sites_message(site_domain, site_id, site_name, site_cookie, site_proxies, site_user_agent)
                break


def sites_message_by_manual():
    for site in site_list:
        site_id = site.site_id
        if site_id in message_skip_list:
            continue
        site_name = site.site_name
        site_domain = site.domain
        site_cookie = site.cookie
        site_proxies = site.proxies
        site_user_agent = site.user_agent
        sites_message(site_domain, site_id, site_name, site_cookie, site_proxies, site_user_agent)


def sites_message(site_domain, site_id, site_name, site_cookie, site_proxies, site_user_agent):
    _LOGGER.info(f'开始获取「{site_name}」站内信')
    try:
        message_list, message_item_url = get_nexusphp_message(
            site_domain, site_cookie, site_proxies, site_user_agent)
        if message_list:
            message_after = word_ignore(site_name, message_list)
            count = len(message_after)
            result_message = ''.join(message_after)
            if result_message:
                if count == 1:
                    title = f'💌{site_name}:{result_message.splitlines()[0].replace("💬 ", "")}'
                    content = result_message.split('\n', 1)[1]
                    link_url = message_item_url
                else:
                    title = f'💌{site_name}:{count}条站内新消息'
                    content = result_message
                    link_url = urljoin(site_domain, '/messages.php?action=viewmailbox&box=1')
                pic = site_pic[site_id] if site_id in site_pic else site_pic["msg_default"]
                sent_notify(title, content, link_url, pic)
            _LOGGER.info(f'「{site_name}」站点共{count}条新消息已发送通知')
        else:
            _LOGGER.info(f'「{site_name}」无未读站内信')
    except Exception as e:
        _LOGGER.error(f'获取「{site_name}」站内信失败，原因：{e}')
        return


def site_announcement():
    for site in site_list:
        site_id = site.site_id
        if not site_id:
            continue
        if site_id in announcement_skip_list:
            continue
        _LOGGER.info(f'开始获取「{site.site_name}」站点公告')
        try:
            gonggao_date, anouncement_title, anouncement_content, flag = get_nexusphp_announcement(
                site.site_name, site.site_id, site.domain, site.cookie, site.proxies, site.user_agent)
            if flag:
                title = f'📢{site.site_name}: {anouncement_title}'
                content = f'日期：{gonggao_date}\n内容：{anouncement_content}' if anouncement_content else ''
                link_url = urljoin(site.domain, '/index.php')
                pic = site_pic[site_id] if site_id in site_pic else site_pic["notice_default"]
                sent_notify(title, content, link_url, pic)
                _LOGGER.info(f'「{site.site_name}」站点公告已发送通知')
            else:
                _LOGGER.info(f'{site.site_name}没有新公告')
        except Exception as e:
            _LOGGER.error(f'获取「{site.site_name}」站点公告失败，原因：{e}')
            continue


def get_nexusphp_message(site_url, cookie, proxies, user_agent):
    unread_selector = 'td > img[alt="Unread"]'
    body_selector = 'td[colspan*="2"]'
    caption_list = []
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
    message_url = 'messages.php?action=viewmailbox&box=1'
    messages_url = urljoin(site_url, message_url)
    headers = {
        'cookie': cookie,
        'user-agent': user_agent,
    }
    if 'totheglory' in site_url:
        response = httpx.get(messages_url, headers=headers, proxies=proxies, timeout=30).text
    else:
        response = requests.request("GET", messages_url, headers=headers, proxies=proxies, timeout=30).text
    soup_tmp = SoupStrainer("form", {"action": "messages.php"})
    soup = BeautifulSoup(response, 'html.parser', parse_only=soup_tmp)
    unread_list = soup.select(unread_selector)
    messages_item_url = ''
    for unread_item in unread_list:
        td = unread_item.parent.next_sibling.next_sibling
        title = td.text
        href = td.a['href']
        messages_item_url = urljoin(site_url, href)
        if 'totheglory' in site_url:
            message_res = httpx.get(messages_item_url, headers=headers, proxies=proxies, timeout=30).text
        else:
            message_res = requests.request("GET", messages_item_url, headers=headers, proxies=proxies, timeout=30).text
        message_soup_tmp = SoupStrainer("td", {"colspan": "2"})
        message_soup = BeautifulSoup(message_res, 'html.parser', parse_only=message_soup_tmp)
        element_body = message_soup.select(body_selector)[0].text.strip()
        caption = f'💬 {title.strip()}\n{element_body.strip()}\n\n'
        caption_list.append(caption)
    return caption_list, messages_item_url


sites_announcement_selector = {
    'putao': {
        'gonggao_box_selector': 'td',
        'gonggao_box_attributes': {'class': 'text'},
        'gonggao_title_selector': 'td.text > ul > a',
        'gonggao_content_selector': 'td.text > ul > div',
    },
    'ssd': {
        'gonggao_box_selector': 'td',
        'gonggao_box_attributes': {'class': 'text'},
        'gonggao_title_selector': 'td.text > div > div:nth-child(1) > a',
        'gonggao_content_selector': 'td.text > div > div:nth-child(1) > div',
    },
    'hdchina': {
        'gonggao_box_selector': 'div',
        'gonggao_box_attributes': {'class': 'announcebox'},
        'gonggao_title_selector': 'div.announcebox > div.announce > h4',
        'gonggao_content_selector': 'div.announcebox > div.announce > h3',
    },
    'nexusphp': {
        'gonggao_box_selector': 'td',
        'gonggao_box_attributes': {'class': 'text'},
        'gonggao_title_selector': 'td.text > div > a',
        'gonggao_content_selector': 'td.text > div > div',
    }
}


def get_nexusphp_announcement(site_name, site_id, site_url, cookie, proxies, user_agent):
    if site_id not in sites_announcement_selector.keys():
        site_id = 'nexusphp'
    gonggao_box_selector = sites_announcement_selector[site_id].get('gonggao_box_selector')
    gonggao_box_attributes = sites_announcement_selector[site_id].get('gonggao_box_attributes')
    gonggao_title_selector = sites_announcement_selector[site_id].get('gonggao_title_selector')
    gonggao_content_selector = sites_announcement_selector[site_id].get('gonggao_content_selector')
    gonggao_url = 'index.php'
    gonggao_url = urljoin(site_url, gonggao_url)
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
    response = requests.request("GET", gonggao_url, headers=headers, proxies=proxies, timeout=30).text
    soup_tmp = SoupStrainer(gonggao_box_selector, gonggao_box_attributes)
    soup = BeautifulSoup(response, 'html.parser', parse_only=soup_tmp)
    announcement_title = soup.select(gonggao_title_selector)
    announcement_content = soup.select(gonggao_content_selector)[0].text.strip()
    gonggao_date = announcement_title[0].text.strip().split(' -', 1)[0].replace('.', '-')
    announcement_title = announcement_title[0].text.strip().split(' -', 1)[1]
    gonggao_cache = get_cache(site_name, gonggao_date)
    flag = False
    if not gonggao_cache:
        server.common.set_cache(site_name, gonggao_date, announcement_content)
        flag = True
    if gonggao_cache != announcement_content:
        server.common.set_cache(site_name, gonggao_date, announcement_content)
        flag = True
    return gonggao_date, announcement_title, announcement_content, flag


def word_ignore(site_name, message_list: list):
    word, hit = [], []
    if words:
        word = words.split(',')
        for item in message_list:
            for i in word:
                if i in item:
                    hit.append(item)
                    break
        for hit_item in hit:
            message_list.remove(hit_item)
            _LOGGER.info(f'「{site_name}」站内信「{hit_item.strip()}」触发关键词，已屏蔽！')
    else:
        pass
    return message_list


def get_cache(site_name, gonggao_date):
    comm = server.common.get_cache(site_name, gonggao_date)
    return comm


def sent_notify(title, content, link_url, pic):
    if message_to_uid:
        for _ in message_to_uid:
            server.notify.send_message_by_tmpl('{{title}}', '{{a}}', {
                'title': title,
                'a': content,
                'link_url': link_url,
                'pic_url': pic
            }, to_uid=_)
    else:
        server.notify.send_message_by_tmpl('{{title}}', '{{a}}', {
            'title': title,
            'a': content,
            'link_url': link_url,
            'pic_url': pic
        })


def main():
    sites_message_by_manual()
    site_announcement()
