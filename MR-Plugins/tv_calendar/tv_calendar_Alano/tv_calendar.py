#!/usr/bin/env python3
# import datetime
from datetime import datetime
import typing
import random
import time
import requests
from typing import Dict, Any
from plexapi.server import PlexServer
from moviebotapi.common import MenuItem
from moviebotapi.core.models import MediaType
from moviebotapi.subscribe import SubStatus, Subscribe
import json
import os
import shutil
import xml.etree.ElementTree as ET
import logging
from mbot.openapi import mbot_api
from mbot.openapi import media_server_manager
from mbot.core.plugins import *
from flask import Blueprint, request
from mbot.common.flaskutils import api_result
from mbot.register.controller_register import login_required
_LOGGER = logging.getLogger(__name__)

plugins_name = '「追剧日历」'
server = mbot_api
api_url = "/3/tv/%(tv_id)s/season/%(season_number)s"
tmdb_imageBaseUrl='https://image.tmdb.org/t/p/w500'
tv_api_url = "/3/tv/%(tv_id)s"
param = {'language': 'zh-CN'}
message_to_uid: typing.List[int] = []
src_base_path = '/data/plugins/tv_calendar_Alano/frontend'
dst_base_path = '/app/frontend/static/tv_calendar'
# 设置Plex服务器连接
# plex_url = 'http://10.10.10.10:32400'
# plex_token = ''
# plexserver = PlexServer(plex_url, plex_token)
plexserver = media_server_manager.master_plex.plex


def hlink(src_base_path, dst_base_path):
    try:
        one = True
        for root, dirs, files in os.walk(src_base_path):
            for file_name in files:
                src_file_path = os.path.join(root, file_name)
                dst_file_path = os.path.join(dst_base_path, os.path.relpath(src_file_path, src_base_path))
                dst_dir_path = os.path.dirname(dst_file_path)
                if not os.path.exists(dst_dir_path):
                    os.makedirs(dst_dir_path)
                if os.path.isfile(src_file_path):
                    if os.path.exists(dst_file_path) or os.path.islink(dst_file_path):
                        os.remove(dst_file_path) # 如果目标文件已经存在，删除它
                    os.symlink(src_file_path, dst_file_path)
                    # shutil.copyfile(src_file_path, dst_file_path)
            for dir_name in dirs:
                src_dir_path = os.path.join(root, dir_name)
                dst_dir_path = os.path.join(dst_base_path, os.path.relpath(src_dir_path, src_base_path))
                if not os.path.exists(dst_dir_path):
                    os.makedirs(dst_dir_path)
                one = False
                hlink(src_dir_path, dst_dir_path)
        if one:
            _LOGGER.info(f'{plugins_name}WEB 素材已软链接到容器')
    except Exception as e:
        _LOGGER.error(f'{plugins_name}将 WEB 素材已软链接到容器出错，原因: {e}')


@plugin.after_setup
def after_setup(plugin_meta: PluginMeta, config: Dict[str, Any]):
    global set_pic_url,mbot_url,mbot_api_key
    global message_to_uid
    set_pic_url = config.get('set_pic_url','')
    message_to_uid = config.get('uid','')
    mbot_url = config.get('mbot_url','')
    mbot_api_key = config.get('mbot_api_key','')

    hlink(src_base_path, dst_base_path)

    """授权并添加菜单"""
    href = '/common/view?hidePadding=true#/static/tv_calendar/tv_calendar.html'
    # 授权管理员和普通用户可访问
    server.auth.add_permission([1, 2], href)
    # 获取菜单，把追剧日历添加到"我的"菜单分组
    menus = server.common.list_menus()
    menu_list=[]
    for menu in menus:
        if menu.title == '我的':
            for x in menu.pages:
                menu_list.append(x.title)
            if '追剧日历' not in menu_list:
                menu_item = MenuItem()
                menu_item.title = '追剧日历'
                menu_item.href = href
                menu_item.icon = 'Today'
                menu.pages.append(menu_item)
                break
    server.common.save_menus(menus)
    set_plex()

@plugin.config_changed
def config_changed(config: Dict[str, Any]):
    global set_pic_url,mbot_url,mbot_api_key
    global message_to_uid
    set_pic_url = config.get('set_pic_url','')
    message_to_uid = config.get('uid','')
    mbot_url = config.get('mbot_url','')
    mbot_api_key = config.get('mbot_api_key','')
    # shutil.copy('/data/plugins/tv_calendar_Alano/frontend/tv_calendar.html', '/app/frontend/static')
    hlink(src_base_path, dst_base_path)
    _LOGGER.info('「追剧日历」已重新加载配置并重新链接资源到容器内')
    set_plex()

# 新增剧集订阅，重新生成日历数据
@plugin.on_event(
    bind_event=['SubMedia'], order=1)
def on_subscribe_new_media(ctx: PluginContext, event_type: str, data: Dict):
    time.sleep(30)
    media_type = data.get('type','')
    if media_type == 'TV':
        sub_info = get_sub_info(data)
        _LOGGER.info(f'{plugins_name}新订阅剧集{sub_info}，更新追剧日历数据')
        time.sleep(30)
        save_json()
    else:
        cn_name = data.get('cn_name','')
        _LOGGER.info(f'{plugins_name}新订阅媒体{cn_name}，不是剧集，不更新追剧日历数据')
    
# 删除剧集订阅，重新生成日历数据
@plugin.on_event(
    bind_event=['DeleteSubMedia'], order=2)
def on_subscribe_delete_media(ctx: PluginContext, event_type: str, data: Dict):
    time.sleep(30)
    media_type = data.get('type','')
    if media_type == 'TV':
        sub_info = get_sub_info(data)
        _LOGGER.info(f'{plugins_name}退订剧集{sub_info}，更新追剧日历数据')
        time.sleep(30)
        save_json()
    else:
        cn_name = data.get('cn_name','')
        _LOGGER.info(f'{plugins_name}退订媒体{cn_name}，不是剧集，不更新追剧日历数据')

# 每天重新生成日历数据
@plugin.task('save_json', '更新追剧日历数据', cron_expression='45 0,1,6 * * *')
def task():
    save_json()

# 每小时自动同步本地媒体库数据至追剧日历
@plugin.task('update_json', '同步本地媒体库数据至追剧日历', cron_expression='0 * * * *')
def update():
    update_json()


def set_plex():
    try:
        # settings = plexserver.settings
        if mbot_url and mbot_api_key:
            webhook_url = f'{mbot_url}/api/plugins/update_json?access_key={mbot_api_key}'
            # 自动设置 webhooks
            account = plexserver.myPlexAccount()
            webhooks = account.webhooks()
            if webhook_url not in webhooks:
                webhooks.append(webhook_url)
                account.setWebhooks(webhooks)
                _LOGGER.info(f"{plugins_name} 已向 PLEX 服务器添加 Webhook")
            else:
                _LOGGER.info(f"{plugins_name} PLEX 服务器 Webhook 列表中已添加此 Webhook 链接：{webhook_url}")
    except Exception as e:
        _LOGGER.error(f'{plugins_name}为 PLEX 服务器添加 Webhook 出错，原因: {e}')

def get_sub_info(data):
    try:
        cn_name = data.get('cn_name',None)
        release_year = data.get('release_year',None)
        season_index = data.get('season_index',None)
        sub_info = f"「{cn_name} ({release_year}) 第 {season_index} 季」"
        return sub_info
    except Exception as e:
        _LOGGER.error(f'{plugins_name}获取新订阅剧集信息异常，原因：{e}')
        return ''

def get_tmdb_info(tv_id, season_number):
    time.sleep(1)
    result = ''
    for i in range(3):
        try:
            result = server.tmdb.request_api(api_url % {'tv_id': tv_id, 'season_number': season_number}, param)
            break
        except Exception as e:
            _LOGGER.error(f'「get_tmdb_info」{i+1}/3 次请求异常，原因：{e}')
            time.sleep(5)
            continue
    if result:
        # _LOGGER.info(f'「get_tmdb_info」请求成功')
        return result
    else:
        _LOGGER.error('「get_tmdb_info」请求获取失败，可能还没有这个剧集的信息')
    return False

def create_hard_link(file_name):
    # 排除以.开头的文件
    if file_name.startswith('.'):
        return
    src_path = os.path.join(src_base_path, file_name)
    dst_path = os.path.join(dst_base_path, file_name)

    if os.path.exists(dst_path) or os.path.islink(dst_path):
        os.remove(dst_path) # 如果目标文件已经存在，删除它
    # os.link(src_path, dst_path) # 创建硬链接
    os.symlink(src_path, dst_path) # 创建软链接
    # shutil.copyfile(src_path, dst_path) # 复制文件
    # _LOGGER.info(f'「{src_path}」已软链接到「{src_path}」')

def get_display_title(key):
    plex_url = plexserver.url('')
    plex_token = plexserver._token
    url = plex_url + key + '?X-Plex-Token=' + plex_token
    response = requests.get(url)
    if response.status_code == 200:
        # 解析XML
        root = ET.fromstring(response.text)
        """
        streamType="1": 视频流 (Video Stream)
        streamType="2": 音频流 (Audio Stream)
        streamType="3": 字幕流 (Subtitle Stream)
        streamType="4": 章节流 (Chapter Stream)
        """
        # 使用XPath定位第一个streamType="1"的Stream元素
        stream_element = root.find('.//Video/Media/Part/Stream[@streamType="1"]')
        # 使用XPath定位所有的streamType="1"的Stream元素
        # stream_elements = root.findall('.//Video/Media/Part/Stream[@streamType="1"]')
        if stream_element is not None:
            display_title = stream_element.get('displayTitle')
            if display_title:
                return display_title
    return ''

def get_tv_info(tv_id):
    time.sleep(1)
    result = ''
    for i in range(3):
        try:
            result = server.tmdb.request_api(tv_api_url % {'tv_id': tv_id}, param)
            break
        except Exception as e:
            _LOGGER.error(f'「get_tv_info」{i+1}/3 次请求异常，原因：{e}')
            time.sleep(3)
            continue
    if result:
        # _LOGGER.info(f'「get_tv_info」请求成功')
        return result
    else:
        _LOGGER.error('「get_tv_info」请求获取失败，可能还没有这个剧集的信息')
        return False

def find_season_poster(seasons, season_number):
    for season in seasons:
        if season_number == season['season_number']:
            return season['poster_path']
    return ''

# 大小单位转换，输入Bytes
def convert_bytes_to_gbm(bytes_value):
    gb = bytes_value / (1024 ** 3)  # 转换为GB
    if gb >= 1:
        return f"{gb:.2f}GB"
    else:
        mb = bytes_value / (1024 ** 2)  # 转换为MB
        return f"{mb:.2f}MB"

def convert_milliseconds(milliseconds):
    milliseconds = int(milliseconds)
    minutes = milliseconds // 60000  # 毫秒转分钟
    if minutes >= 60:
        hours = minutes // 60
        minutes %= 60
        return f"{hours}小时{minutes}分钟"
    else:
        return f"{minutes}分钟"


def get_local_info(tmdb_id, season_number, tv_name):
    episode_local_max = 0
    local_info = {}
    local_info_list = {}
    for i in range(3):
        try:
            # 获取媒体库中集的数据
            episode_list = server.media_server.list_episodes_from_tmdb(tmdb_id, season_number)
            # 已有集数列表[1,2,3,4]
            episode_local_arr = [int(x.index) for x in episode_list]
            # 有多少集 4
            episode_local_num = len(episode_local_arr)
            if episode_local_arr:
                episode_local_max = max(episode_local_arr)
                episode_local_arr_f = format_episode_local_arr(episode_local_arr)
                episode_local_arr_f = f"有 {episode_local_num} 集 {episode_local_arr_f}"
            else:
                episode_local_arr_f = f"媒体库中还没有该剧集"

            if episode_list:
                # 获取剧集在plex服务器的本地数据
                try:
                    episode_local_child_rating_key = episode_list[0].id
                    episode = plexserver.fetchItem(int(episode_local_child_rating_key))
                    RATING_KEY = episode.grandparentRatingKey
                    show = plexserver.fetchItem(int(RATING_KEY))
                    season = show.season(season_number)
                    episodes = season.episodes()
                    for episode_item in episodes:
                        # 文件名
                        try:
                            file_name = os.path.basename(episode_item.locations[0])
                            # file_name = os.path.basename(episode_item.media[0].parts[0].file)  # 此行也可获取文件名
                        except Exception as e:
                            file_name = ''
                        # 时长
                        try:
                            duration = convert_milliseconds(episode_item.duration)
                        except Exception as e:
                            duration = ''
                        # 大小
                        try:
                            size = convert_bytes_to_gbm(episode_item.media[0].parts[0].size)
                        except Exception as e:
                            size = ''
                        # bitrate
                        try:
                            bitrate = f"{round(episode_item.media[0].bitrate / 1000, 1)}Mbps"
                        except Exception as e:
                            bitrate = ''
                        # 分辨率
                        try:
                            videoResolution = episode_item.media[0].videoResolution.lower() #480 720 1080 4k
                            videoResolution = videoResolution if videoResolution == '4k' else f"{videoResolution}P"
                            videoResolution = videoResolution.upper()
                        except Exception as e:
                            videoResolution = ''
                        # 动态范围
                        try:
                            key = episode_item.key # /library/metadata/33653
                            display_title = get_display_title(key).lower()
                            # display_title = episode_item.media[0].parts[0].streams[0].displayTitle.lower(), #'4K DoVi (HEVC Main 10) 4K HDR10 (HEVC Main 10) 1080p (H.264)
                            if 'dovi' in display_title or 'dov' in display_title or 'dv' in display_title:
                                display_title = 'DV'
                            elif 'hdr' in display_title:
                                display_title = 'HDR'
                            else:
                                display_title = 'SDR'
                        except Exception as e:
                            display_title = ''
                        try:
                            isPlayed = episode_item.isPlayed
                        except Exception as e:
                            isPlayed = False
                        local_info={
                            episode_item.episodeNumber: {
                                'file_name': file_name, 
                                'display_title': display_title,
                                'size': size,
                                'videoResolution': videoResolution,
                                'duration': duration,
                                'bitrate': bitrate,
                                'isPlayed': isPlayed
                        }}
                        local_info_list.update(local_info)

                except Exception as e:
                    _LOGGER.error(f'{plugins_name}读取「{tv_name}」{tmdb_id}-{season_number} 本地剧集信息出错，原因: {e}')
                    pass
                return episode_local_arr, episode_local_num, episode_local_arr_f, episode_local_max, local_info_list
        except Exception as e:
            _LOGGER.error(f'「get_local_info」{i+1}/3 次请求异常，原因：{e}')
            time.sleep(3)
            continue
    return [],0,'',0,{}

def update_json():
    try:
        # today_date = datetime.date.today().strftime('%Y-%m-%d')
        today_date = datetime.today().strftime("%Y-%m-%d")
        
        original_path = f'{src_base_path}/original.json'
        if not os.path.exists(original_path):
            return
        # 打开原始 JSON 文件
        with open(original_path, 'r', encoding='utf-8') as f:
            episode_list = json.load(f)
        tmdb_id_list = []
        episode_data_list = {}
        episode_data= {}
        # 将今天更新的集数提取出来放到 today_air_episode
        for episode in episode_list:
            if episode["air_date"] == today_date:
                today_episodes = [ep["episode_number"] for ep in episode_list if ep["show_id"] == episode["show_id"] and ep["air_date"] == today_date]
                for ep in episode_list:
                    if ep["show_id"] == episode["show_id"]:
                        ep["today_air_episode"] = today_episodes
            else:
                episode["today_air_episode"] = []
        # 添加本地媒体库数据
        for episode in episode_list:
            tmdb_id = episode.get('show_id','')
            episode_number = episode.get('episode_number','')
            season_number = episode.get('season_number','')
            tv_name = episode.get('tv_name','')
            if tmdb_id not in tmdb_id_list:
                today_air_episode = episode['today_air_episode']
                episode_local_arr, episode_local_num, episode_local_arr_f, episode_local_max, local_info_list = get_local_info(tmdb_id, season_number,tv_name)
                if today_air_episode:
                    episode_local_updated = set(today_air_episode).issubset(set(episode_local_arr))
                else:
                    episode_local_updated = False
                episode['episode_local_num'] = episode_local_num
                episode['episode_local_max'] = episode_local_max
                episode['episode_local_arr_f'] = episode_local_arr_f
                episode['episode_local_updated'] = episode_local_updated
                episode['episode_local_filename'] = local_info_list.get(episode_number, {}).get('file_name', '')
                episode['episode_local_size'] = local_info_list.get(episode_number, {}).get('size', '')
                episode['episode_local_videoResolution'] = local_info_list.get(episode_number, {}).get('videoResolution', '')
                episode['episode_local_display_title'] = local_info_list.get(episode_number, {}).get('display_title', '')
                episode['episode_local_bitrate'] = local_info_list.get(episode_number, {}).get('bitrate', '')
                episode['episode_local_duration'] = local_info_list.get(episode_number, {}).get('duration', '')
                episode['episode_local_isPlayed'] = local_info_list.get(episode_number, {}).get('isPlayed', '')
                episode_data = {
                    tmdb_id: {
                        "episode_local_num": episode_local_num,
                        "episode_local_max": episode_local_max,
                        "episode_local_updated": episode_local_updated,
                        "episode_local_arr_f": episode_local_arr_f,
                        "local_info_list": local_info_list
                    }
                }
                episode_data_list.update(episode_data)
                tmdb_id_list.append(tmdb_id)
            else:
                episode['episode_local_num'] = episode_data_list[tmdb_id]["episode_local_num"]
                episode['episode_local_max'] = episode_data_list[tmdb_id]["episode_local_max"]
                episode['episode_local_arr_f'] = episode_data_list[tmdb_id]["episode_local_arr_f"]
                episode['episode_local_updated'] = episode_data_list[tmdb_id]["episode_local_updated"]
                episode['episode_local_filename'] = episode_data_list[tmdb_id]["local_info_list"].get(episode_number,{}).get('file_name', '')
                episode['episode_local_size'] = episode_data_list[tmdb_id]["local_info_list"].get(episode_number,{}).get('size', '')
                episode['episode_local_videoResolution'] = episode_data_list[tmdb_id]["local_info_list"].get(episode_number,{}).get('videoResolution', '')
                episode['episode_local_display_title'] = episode_data_list[tmdb_id]["local_info_list"].get(episode_number,{}).get('display_title', '')
                episode['episode_local_bitrate'] = episode_data_list[tmdb_id]["local_info_list"].get(episode_number,{}).get('bitrate', '')
                episode['episode_local_duration'] = episode_data_list[tmdb_id]["local_info_list"].get(episode_number,{}).get('duration', '')
                episode['episode_local_isPlayed'] = episode_data_list[tmdb_id]["local_info_list"].get(episode_number,{}).get('isPlayed', '')
    except Exception as e:
        _LOGGER.error(f'{plugins_name}同步本地媒体库数据到「original.json」出错，原因: {e}')
    # 将更新后的数据写回到文件中
    write_json_file(original_path,episode_list)
    create_hard_link('original.json')
    _LOGGER.info(f'{plugins_name}已同步本地媒体库数据到「original.json」并已链接到容器')

def format_episode_local_arr(episode_local_arr):
    episode_local_arr = sorted(episode_local_arr) # 对列表进行排序
    new_ranges = [] # 用于存储连续范围的列表
    # 检查第一个连续范围
    i = 0
    while i < len(episode_local_arr):
        start_num = episode_local_arr[i]
        end_num = start_num
        while i < len(episode_local_arr) - 1 and episode_local_arr[i+1] == end_num+1:
            end_num = episode_local_arr[i+1]
            i += 1
        i += 1
        if start_num == end_num:
            new_ranges.append(str(start_num))
        else:
            new_ranges.append(f"{start_num}-{end_num}")
    # 将连续范围格式化为字符串
    new = ",".join(new_ranges)
    return new


def save_json():
    _LOGGER.info(f'{plugins_name}开始更新剧集数据')
    subscribe_list_all = []
    # 获取订阅列表
    subscribe_list_all = server.subscribe.list(MediaType.TV, SubStatus.Subscribing)
    # 获取自定义订阅列表
    custom_list = server.subscribe.list_custom_sub()
    custom_list_filter = list(filter(lambda x: x.media_type == MediaType.TV and x.tmdb_id and x.enable, custom_list))
    # 所有订阅存在 subscribe_list_all 这个列表中
    for item in custom_list_filter:
        subscribe_list_all.append(Subscribe({'tmdb_id': item.tmdb_id, 'season_index': item.season_number}, mbot_api.subscribe))
    img_list = []
    episode_list = []
    for row in subscribe_list_all:
        tmdb_id = row.tmdb_id
        season_number = row.season_number
        # release_year = row.release_year
        tv = get_tv_info(tmdb_id)
        if not tv:
            continue
        tv_poster = tv['poster_path']
        seasons = tv['seasons']
        tv_name = tv['name']
        _LOGGER.info(f'开始处理「{tv_name}」')
        tv_original_name = tv['original_name']
        backdrop_path = tv['backdrop_path']
        season_poster = find_season_poster(seasons, season_number)
        season = get_tmdb_info(tmdb_id, season_number)
        if not season:
            continue
        episodes = season['episodes']
        # 一共多少集 数据来源于tmdb
        episodes_all_num = len(episodes)
        for episode in episodes:
        # for i, episode in enumerate(episodes):
            if tv_poster:
                tv_poster_name = os.path.basename(tv_poster)
                img_list.append(tv_poster_name)

            if season_poster:
                season_poster_name = os.path.basename(season_poster)
                img_list.append(season_poster_name)

            if backdrop_path:
                backdrop_name = os.path.basename(backdrop_path)
                img_list.append(backdrop_name)
            # 将海报存在本地
            post_img_path = ''
            post_img_path = season_poster or tv_poster
            if post_img_path:
                save_img(post_img_path,tv_name)
            # 将单集封面存到本地
            still_path = episode.get('still_path','')
            if still_path:
                save_img(still_path,tv_name)
                still_name = os.path.basename(still_path)
                img_list.append(still_name)
            # 将单集默认封面存到本地
            if backdrop_path:
                save_img(backdrop_path,tv_name)
            episode['tv_name'] = tv_name
            episode['tv_original_name'] = tv_original_name
            episode['tv_poster'] = tv_poster
            episode['season_poster'] = season_poster
            episode['backdrop_path'] = backdrop_path
            # 总集数存入单集数据中
            episode['episodes_all_num'] = episodes_all_num
            episode_list.append(episode)
    original_path = f'{src_base_path}/original.json'
    _LOGGER.info(f'{plugins_name}开始写入新的追剧日历数据到「original.json」文件')
    write_json_file(original_path,episode_list)
    update_json()
    # 遍历删除不需要的图片
    del_img(img_list)
    hlink(src_base_path, dst_base_path)
    _LOGGER.info(f'{plugins_name}剧集数据更新结束')
    if datetime.now().time().hour == 6:
        push_message()
    _LOGGER.info(f'{plugins_name}数据更新进程全部完成')

def write_json_file(original_path,list):
    for i in range(3):
        try:
            with open(original_path, 'w', encoding='utf-8') as fp:
                json.dump(list, fp, ensure_ascii=False)
        except Exception as e:
            _LOGGER.error(f'{plugins_name}写入新数据到「original.json」文件出错，原因: {e}')
            time.sleep(3)
            continue

def del_img(img_list):
    del_img_list = []
    _LOGGER.info(f'{plugins_name}开始检查是否有完结剧集相关图片，如有将其删除！')
    all_img = os.listdir(os.path.join(src_base_path, 'img'))
    for img_file in all_img:
        if img_file not in img_list:
            try:
                os.remove(os.path.join(src_base_path, 'img', img_file))
                del_img_list.append(img_file)
            except Exception as e:
                    _LOGGER.error(f'{plugins_name}删除 {img_file} 出错，原因: {e}')
                    continue
    if del_img_list:
        _LOGGER.info(f'{plugins_name}已删除完结剧集相关图片: {del_img_list}')


def get_after_day(day, n):
    offset = datetime.timedelta(days=n)
    # 获取想要的日期的时间
    after_day = day + offset
    return after_day

# def get_server_url():
#     try:
#         yml_file = "/data/conf/base_config.yml"
#         with open(yml_file, encoding='utf-8') as f:
#             yml_data = yaml.load(f, Loader=yaml.FullLoader)
#         mr_url = yml_data['web']['server_url']
#         if mr_url is None or mr_url == '':
#           return ''
#         if (re.match('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', mr_url) is not None):
#             _LOGGER.info(f'从配置文件中获取到的「mr_url」{mr_url}')
#             return mr_url
#     except Exception as e:
#         _LOGGER.error(f'获取「mr_url」异常，原因: {e}')
#         pass
#     return '' 

def save_img(img_path,tv_name):
    img_url = f"{tmdb_imageBaseUrl}{img_path}"
    img_dir = os.path.join(src_base_path, 'img')
    os.makedirs(img_dir, exist_ok=True)
    img_path = os.path.join(img_dir, os.path.basename(img_url))
    if not os.path.exists(img_path):
        for i in range(3):
            try:
                response = requests.get(img_url)
                with open(img_path, "wb") as f:
                    f.write(response.content)
                # _LOGGER.info(f"{tv_name}的海报/背景已存入{img_path}")
                break
            except Exception as e:
                _LOGGER.error(f'「{tv_name}」保存 {img_url} 到本地 {i+1}/3 次请求异常，原因：{e}')
                time.sleep(3)
                continue
    # else:
    #     img_name = os.path.basename(img_path)
        # _LOGGER.info(f'「{tv_name}」图片「{img_name}」本地有了，不重新保存了')

def push_message():
    _LOGGER.info(f'{plugins_name}开始推送今日将要更新的剧集信息')
    msg_title = ''
    pic_url = ''
    message = ''
    # mr_url = get_server_url()
    # if mr_url:
    #     link_url = f'{mr_url}/static/tv_calendar.html'
    try:
        with open('/app/frontend/static/tv_calendar/original.json', encoding='utf-8') as f:
            episode_list = json.load(f)
        episode_filter = list(
            filter(lambda x: x['air_date'] == datetime.today().strftime("%Y-%m-%d"), episode_list))
        name_dict = {}
        for item in episode_filter:
            if item['tv_name'] not in name_dict:
                name_dict[item['tv_name']] = [item]
            else:
                name_dict[item['tv_name']].append(item)
        img_api = 'https://api.r10086.com/img-api.php?type=%E5%8A%A8%E6%BC%AB%E7%BB%BC%E5%90%88' + str(
            random.randint(1, 18))
        
        if set_pic_url:
            pic_url = set_pic_url
            _LOGGER.info(f'已设置消息封面图片地址: {pic_url}')
        else:
            pic_url = img_api
            _LOGGER.info(f'未设置消息封面图片地址，封面图片将展示为随机二次元图片')
        if len(episode_list) == 0:
            message = "今日没有剧集更新"
        else:
            message_arr = []
            tv_count = len(name_dict)
            if tv_count:
                msg_title = f'今天将更新 {int(tv_count):02d} 部剧集'
            else:
                msg_title = "今日没有剧集更新"
            for tv_name in name_dict:
                episodes = name_dict[tv_name]
                episode_number_arr = []
                for episode in episodes:
                    episode_number_arr.append(str(episode['episode_number']))
                episode_numbers = ','.join([f"{int(episode):02d}" for episode in episode_number_arr])
                message_arr.append(f"{tv_name} - 第 {episodes[0]['season_number']:02d} 季·第 {episode_numbers} 集")
            message = "\n".join(message_arr)
    except Exception as e:
        _LOGGER.error(f'{plugins_name}处理消息数据异常，原因: {e}')
        pass
    server_url = mbot_api.config.web.server_url
    if server_url:
        link_url = f"{server_url.rstrip('/')}/static/tv_calendar/tv_calendar.html"
    else:
        link_url = None
    try:
        if message_to_uid:
            for _ in message_to_uid:
                server.notify.send_message_by_tmpl('{{title}}', '{{a}}', {
                    'title': msg_title,
                    'a': message,
                    'pic_url': pic_url,
                    'link_url': link_url
                }, to_uid=_)
                _LOGGER.info(f'「今日剧集更新列表」已推送通知')
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

plex_webhook = Blueprint('update_json', __name__)
"""
把flask blueprint注册到容器
这个URL访问完整的前缀是 /api/plugins/你设置的前缀
"""
plugin.register_blueprint('update_json', plex_webhook)

# 接收 plex 服务器主动发送的事件
@plex_webhook.route('', methods=['POST'])
@login_required() # 接口access_key鉴权
def update_json_wb():
    payload = request.form['payload']
    data = json.loads(payload)
    plex_event = data.get('event', '')
    if plex_event in ['library.on.deck', 'library.new']:
        metadata = data.get('Metadata', '')
        org_type = metadata.get('type', '')
        if org_type in ['episode','season','show']:
            _LOGGER.info(f'{plugins_name}接收到 PLEX 通过 Webhook 传过来的「入库事件」，开始分析事件并同步媒体库数据到追剧日历')
            update_json()
    return api_result(code=0, message='ok', data=plex_event)
