#!/usr/bin/env python3
import datetime
import random
import typing
from typing import Dict, Any
import json
import shutil
import sqlite3
import requests
from mbot.openapi import mbot_api
from mbot.core.plugins import *
from mbot.core.plugins import *
import logging
import time
import yaml
import os
import re

server = mbot_api
api_url = "https://api.themoviedb.org/3/tv/%(tv_id)s/season/%(season_number)s"
tv_api_url = "https://api.themoviedb.org/3/tv/%(tv_id)s"
param = {}
proxies = {}
_LOGGER = logging.getLogger(__name__)
message_to_uid: typing.List[int] = []
api_key = ''


@plugin.after_setup
def after_setup(plugin_meta: PluginMeta, config: Dict[str, Any]):
    global proxies
    # global mr_url
    global param
    global set_pic_url
    global message_to_uid
    global api_key
    if (config.get('proxy') != ''):
        proxies = {
            "http": config.get('proxy'),
            "https": config.get('proxy')
        }
    set_pic_url = config.get('set_pic_url')
    api_key = config.get('apikey')       
    # api_key = config.get('mr_url')
    param = {"api_key": api_key, "language": "zh"}
    message_to_uid = config.get('uid')

    # if os.path.exists('/app/frontend/static/tv_calendar.html'):
    #     os.remove('/app/frontend/static/tv_calendar.html')
    # if os.path.exists('/app/frontend/static/episode.html'):
    #     os.remove('/app/frontend/static/episode.html')
    # if os.path.exists('/app/frontend/static/ALIBABA-Font-Bold.otf'):
    #     os.remove('/app/frontend/static/ALIBABA-Font-Bold.otf')    
    # if os.path.exists('/app/frontend/static/bg.png'):
    #     os.remove('/app/frontend/static/bg.png')    
    # if os.path.exists('/app/frontend/static/title.png'):
    #     os.remove('/app/frontend/static/title.png')    
    shutil.copy('/data/plugins/tv_calendar/frontend/tv_calendar.html', '/app/frontend/static')
    shutil.copy('/data/plugins/tv_calendar/frontend/episode.html', '/app/frontend/static')
    shutil.copy('/data/plugins/tv_calendar/frontend/ALIBABA-Font-Bold.otf', '/app/frontend/static')
    shutil.copy('/data/plugins/tv_calendar/frontend/bg.png', '/app/frontend/static')
    shutil.copy('/data/plugins/tv_calendar/frontend/title.png', '/app/frontend/static')
    _LOGGER.info(f'追剧日历插件: WEB 页素材已复制并覆盖到「/app/frontend/static」')

@plugin.config_changed
def config_changed(config: Dict[str, Any]):
    global proxies
    global param
    global set_pic_url
    global message_to_uid
    global api_key
    if (config.get('proxy') != ''):
        proxies = {
            "http": config.get('proxy'),
            "https": config.get('proxy')
        }
    set_pic_url = config.get('set_pic_url')
    api_key = config.get('apikey')       
    # mr_url = config.get('mr_url')       
    param = {"api_key": api_key, "language": "zh"}
    message_to_uid = config.get('uid')

@plugin.task('save_json', '剧集更新', cron_expression='10 0 * * *')
def task():
    save_json()
def get_tmdb_info(tv_id, season_number):
    MAX_RETRIES = 5
    for i in range(MAX_RETRIES):
        try:
            res = requests.get(api_url % {'tv_id': tv_id, 'season_number': season_number}, param, proxies=proxies, timeout=30)
            # _LOGGER.error(f'「get_tmdb_info」请求结果：{res}')
            break
        except requests.RequestException as e:
            _LOGGER.error(f'「get_tmdb_info」请求TMDB api 异常，原因：{e}')
            time.sleep(5)
            continue
    if res.status_code == 200:
        _LOGGER.info(f'「get_tmdb_info」请求TMDB api 成功，返回: {res}')
        return res
    else:
        _LOGGER.error('「get_tmdb_info」请求TMDB api 失败')
        return False
    return False
    # return requests.get(api_url % {'tv_id': tv_id, 'season_number': season_number}, param, proxies=proxies)

def get_tv_info(tv_id):
    MAX_RETRIES = 5
    for i in range(MAX_RETRIES):
        try:
            res = requests.get(tv_api_url % {'tv_id': tv_id}, param, proxies=proxies, timeout=30)
            # _LOGGER.error(f'「get_tv_info」请求结果：{res}')
            break
        except requests.RequestException as e:
            _LOGGER.error(f'「get_tv_info」请求TMDB api 异常，原因：{e}')
            time.sleep(5)
            continue
    # 如果重试了 MAX_RETRIES 次后仍然失败，则执行以下代码
    if res.status_code == 200:
        _LOGGER.info(f'「get_tv_info」请求TMDB api 成功，返回: {res}')
        return res
    else:
        _LOGGER.error('「get_tv_info」请求TMDB api 失败')
        return False
    return False

def find_season_poster(seasons, season_number):
    for season in seasons:
        if season_number == season['season_number']:
            return season['poster_path']
    return ''

def save_json():
    _LOGGER.info('开始执行剧集数据更新')
    if api_key == '':
        _LOGGER.info('缺失api_key，无法执行剧集更新任务')
        return
    conn = sqlite3.connect("/data/db/main.db")
    c = conn.cursor()
    sql = "select tmdb_id,season_index from subscribe where type='TV' and status=0 " \
          "UNION " \
          "select tmdb_id,season_number as season_index from subscribe_custom where media_type='TV'"
    cursor = c.execute(sql)
    episode_arr = []
    for row in cursor:
        # try:
        tv_info = get_tv_info(row[0])
        # except Exception as e:
        #     _LOGGER.info(e)
        #     break
        if tv_info == False:
            continue
        tv = tv_info.json()
        tv_poster = tv['poster_path']
        seasons = tv['seasons']
        tv_name = tv['name']
        _LOGGER.info(f'开始处理「{tv_name}」')
        tv_original_name = tv['original_name']
        season_poster = find_season_poster(seasons, row[1])
        
        res = get_tmdb_info(row[0], row[1])
        if res == False:
            continue
        season = res.json()
        episodes = season['episodes']
        for episode in episodes:
            episode['tv_name'] = tv_name
            episode['tv_original_name'] = tv_original_name
            episode['tv_poster'] = tv_poster
            episode['season_poster'] = season_poster
            episode_arr.append(episode)
    if os.path.exists('/app/frontend/static/original.json'):
        _LOGGER.info('删除旧的「original.json」')
        try:
            os.remove('/app/frontend/static/original.json')
        except Exception as e:
            _LOGGER.error(f'删除旧「original.json」出错，原因: {e}，执行强制删除！')
            os.system('rm -f /app/frontend/static/original.json')
            pass
    try:
        with open('/app/frontend/static/original.json', 'w', encoding='utf-8') as fp:
            json.dump(episode_arr, fp, ensure_ascii=False)
        _LOGGER.info('开始写入新的「original.json」')
    except Exception as e:
            _LOGGER.error(f'写入新「original.json」文件出错，原因: {e}')
            pass
    _LOGGER.info('剧集数据更新结束')
    _LOGGER.info('开始推送今日更新')
    push_message()
    conn.close()
    _LOGGER.info('剧集数据更新进程全部完成')


def get_after_day(day, n):
    # 今天的时间计算偏移量
    offset = datetime.timedelta(days=n)
    # 获取想要的日期的时间
    after_day = day + offset
    return after_day

def push_message():
    mr_url = ''
    link_url = ''
    msg_title = ''
    pic_url = ''
    mr_url = get_server_url()
    if mr_url:
        link_url = f'{mr_url}/static/tv_calendar.html'
        # _LOGGER.error(f'mr_url: {mr_url}，all:{link_url}')
    try:
        with open('/app/frontend/static/original.json', encoding='utf-8') as f:
            episode_arr = json.load(f)
        episode_filter = list(
            filter(lambda x: x['air_date'] == datetime.date.today().strftime('%Y-%m-%d'), episode_arr))
        name_dict = {}
        for item in episode_filter:
            if item['tv_name'] not in name_dict:
                name_dict[item['tv_name']] = [item]
            else:
                name_dict[item['tv_name']].append(item)
        img_api = 'https://api.r10086.com/img-api.php?type=%E5%8A%A8%E6%BC%AB%E7%BB%BC%E5%90%88' + str(
            random.randint(1, 18))
        
        _LOGGER.info(f'设置的消息封面图片地址: {set_pic_url}')
        if set_pic_url:
            pic_url = set_pic_url
        else:
            pic_url = img_api

        if len(episode_arr) == 0:
            message = "今日没有剧集更新"
        else:
            message_arr = []
            tv_count = len(name_dict)
            if tv_count:
                msg_title = f'今天将更新 {int(tv_count):02d} 部剧集'
            else:
                msg_title = "今日剧集更新"
            for tv_name in name_dict:
                episodes = name_dict[tv_name]
                episode_number_arr = []
                for episode in episodes:
                    episode_number_arr.append(str(episode['episode_number']))
                # episode_numbers = ','.join(episode_number_arr)
                episode_numbers = ','.join([f"{int(episode):02d}" for episode in episode_number_arr])
                # _LOGGER.error(f'转换后: {episode_numbers}')
                message_arr.append(f"{tv_name}  第 {episodes[0]['season_number']:02d} 季·第 {episode_numbers} 集")
            message = "\n".join(message_arr)
    except Exception as e:
        _LOGGER.error(f'处理异常，原因: {e}')
        pass
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
                    _LOGGER.info(f'「今日剧集更新列表」已推送通知')
                except Exception as e:
                    _LOGGER.error(f'消息推送异常，原因: {e}')
                    pass
        else:
            server.notify.send_message_by_tmpl('{{title}}', '{{a}}', {
                'title': msg_title,
                'a': message,
                'pic_url': pic_url,
                'link_url': link_url
            })
            _LOGGER.info(f'「今日剧集更新列表」已推送通知')
    except Exception as e:
                    _LOGGER.error(f'消息推送异常，原因: {e}')
                    pass
def get_server_url():
    try:
        yml_file = "/data/conf/base_config.yml"
        with open(yml_file, encoding='utf-8') as f:
            yml_data = yaml.load(f, Loader=yaml.FullLoader)
        mr_url = yml_data['web']['server_url']
        # if(re.match('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',mr_url)!=None):
        if(re.match('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', mr_url) != None):
            _LOGGER.info(f'从配置文件中获取到的「mr_url」{mr_url}')
            return mr_url
    except Exception as e:
                _LOGGER.error(f'获取「mr_url」异常，原因: {e}')
                pass
    return ''       