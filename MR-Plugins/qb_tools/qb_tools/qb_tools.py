#!/usr/bin/env python3
import requests
import time
import json
import os
import random
import qbittorrentapi
from mbot.core.plugins import plugin
from mbot.core.plugins import PluginContext, PluginMeta
from mbot.openapi import mbot_api
from typing import Dict, Any
import logging
import threading
import sched
from flask import Blueprint, request
from mbot.common.flaskutils import api_result
from mbot.register.controller_register import login_required
from mbot.openapi import media_server_manager

plexserver = media_server_manager.master_plex.plex
_LOGGER = logging.getLogger(__name__)
server = mbot_api
plugins_name = '「QB 工具箱」'
plugins_path = '/data/plugins/qb_tools'
ignore_torrents = []

@plugin.after_setup
def after_setup(plugin_meta: PluginMeta, config: Dict[str, Any]):
    global qb_urls, qb_ports, usernames, passwords, add_tag, check_interval, update_plex_library_on, random_set
    qb_urls = config.get('qb_urls', '')
    qb_ports = config.get('qb_ports', '')
    usernames = config.get('usernames', '')
    passwords = config.get('passwords', '')
    random_set = config.get('random_set', '')
    add_tag = config.get('add_tag', False)
    update_plex_library_on = config.get('update_plex_library_on', False)
    check_interval = config.get('check_interval', False)
    
@plugin.config_changed
def config_changed(config: Dict[str, Any]):
    global qb_urls, qb_ports, usernames, passwords, add_tag, check_interval, update_plex_library_on, random_set
    qb_urls = config.get('qb_urls', '')
    qb_ports = config.get('qb_ports', '')
    usernames = config.get('usernames', '')
    passwords = config.get('passwords', '')
    random_set = config.get('random_set', '')
    add_tag = config.get('add_tag', False)
    update_plex_library_on = config.get('update_plex_library_on', False)
    check_interval = config.get('check_interval', False)
    _LOGGER.warning(f"{plugins_name}已重新加载设置，将自动重启 Mbot，请等待重启完成")
    server.common.restart_app()

plex_update_lib_post = Blueprint('plex_update_lib', __name__)
"""
把flask blueprint注册到容器
这个URL访问完整的前缀是 /api/plugins/你设置的前缀
api 请求 url = 'http://localhost:1329/api/plugins/plex_update_lib'
"""
plugin.register_blueprint('plex_update_lib', plex_update_lib_post)

@plex_update_lib_post.route('', methods=['POST', 'GET'])
@login_required()
def plex_update_lib():
    plex_update_data = request.json
    try:
        lib_name = request.args.get('lib_name', plex_update_data.get('lib_name', request.form.get('lib_name', '空')))
        filepath = request.args.get('filepath', plex_update_data.get('filepath', request.form.get('filepath', '空')))
        if random_set:
            try:
                min_delay, max_delay = random_set.split(',')
            except Exception as e:
                min_delay = 400
                max_delay = 600
            delay_time = random.randint(int(min_delay), int(max_delay))
        else:
            delay_time = random.randint(400, 600)
        _LOGGER.info(f"「接收 PLEX 刷新路径」接收到更新数据 ['lib_name': '{lib_name}', 'filepath': '{filepath}']，等待 {delay_time} 秒后通知刷新")
        code = 0
        result = {'state':'接收更新数据成功'}
        thread = threading.Thread(target=plex_update, args=(lib_name, filepath, delay_time))
        thread.start()
    except Exception as e:
        _LOGGER.error(f'「接收 PLEX 刷新路径」未接收到更新数据，传参错误，{e}')
        code = 1
        result = {'state':'失败', 'reason':e}
        return api_result(code=code, message=result, data=plex_update_data)
    return api_result(code=code, message=result, data=plex_update_data)

def plex_update(lib_name, filepath, delay_time):
    time.sleep(delay_time)
    for i in range(10):
        try:
            lib = plexserver.library.section(lib_name)
            if lib:
                lib.update(path=filepath)
            else:
                _LOGGER.error(f"没有找到媒体库：{lib_name}")
            _LOGGER.info(f"「通知 PLEX 刷新媒体库」已通知 PLEX 刷新媒体库 ['{lib_name}'] 下的路径：['{filepath}']")
            break
        except Exception as e:
            _LOGGER.error(f"「通知 PLEX 刷新媒体库」第 {i+1}/10 次通知 PLEX 刷新媒体库 ['{lib_name}'] 下的路径：['{filepath}'] 失败，原因：{e}")
            time.sleep(5)
            continue

def tag_torrent(qb_url, qb_port, username, password, add_tag, add_tag_m, progress_path, add_tag_m_name):
    if all([not qb_url, not qb_port, not username, not password]):
        return
    # 创建 qBittorrent 客户端
    qb = qbittorrentapi.Client(host=qb_url, port=qb_port, username=username, password=password)
    try:
        qb.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        _LOGGER.error(f"{plugins_name}Qbittorrent: {qb_url}  登入失败!，原因：{e}")
        return
    if add_tag:
        # 正在下载的种子
        progress_torrent = qb.torrents.info(status_filter='downloading')
        for torrent in progress_torrent:
            if not torrent.tags:
                torrent_name = torrent.name
                # _LOGGER.info(f"ignore_torrents: {ignore_torrents}")
                if torrent_name not in ignore_torrents:
                    label = get_tmdbid(torrent_name)
                    if label:
                        torrent.add_tags(label)
                    else:
                        _LOGGER.error(f"{plugins_name}['{torrent_name}'] 没有获取到该种子的 tmdbid，添加标签 tmdb=none")
                        torrent.add_tags('[tmdb=none]')
                        ignore_torrents.append(torrent_name)
    if add_tag_m:
        if progress_path and add_tag_m and add_tag_m_name:
            # 所有种子
            all_torrent = qb.torrents.info()
            for torrent in all_torrent:
                if os.path.abspath(progress_path) == os.path.abspath(torrent.save_path):
                    if not torrent.tags:
                        # torrent.add_tags('PT刷流')
                        torrent.add_tags(add_tag_m_name)
                    else:
                        _LOGGER.warning(f"{plugins_name}为种子 ['{torrent.name}'] 添加标签失败，因为已有标签：['{torrent.tags}']")
        else:
            _LOGGER.error(f"{plugins_name}手动添加标签 ['{add_tag_m_name}'] 失败，参数设置错误")

def get_tmdbid(torrent_name):
    label = ''
    media_tmdb_id = ''
    media = server.amr.analysis_string(torrent_name)
    # media = server.amr.analysis_string('三体.ThreeBody.S01.2023.2160p.V2.WEB-DL.H265.AAC-HHEB')
    # json_string = json.dumps(vars(media), ensure_ascii=False)
    # _LOGGER.info(f'解析到的媒体信息：{json_string}')
    if media:
        media_tmdb_id = getattr(media, 'tmdb_id', None)
        # label = f"[tmdb={media_tmdb_id}]" if media_tmdb_id else ''
        media_type = getattr(media.media_type, 'value', None)
        if media_type == 'Movie':
            label = f'tmdb=m-{media_tmdb_id}' if media_tmdb_id else ''
        elif media_type == 'TV':
            label = f'tmdb=tv-{media_tmdb_id}' if media_tmdb_id else ''
    return label

def monitor_clients(qb_urls, qb_ports, usernames, passwords, add_tag, add_tag_m, progress_path, add_tag_m_name):
    qb_urls = qb_urls.split('\n') if '\n' in qb_urls else [qb_urls]
    qb_ports = qb_ports.split('\n') if '\n' in qb_ports else [qb_ports]
    usernames = usernames.split('\n') if '\n' in usernames else [usernames]
    passwords = passwords.split('\n') if '\n' in passwords else [passwords]
    clients = [
        {'host': qb_urls[i], 'port': qb_ports[i], 'username': usernames[i], 'password': passwords[i]}
        for i in range(len(qb_urls))
    ]
    for client in clients:
        tag_torrent(client['host'], client['port'], client['username'], client['password'], add_tag, add_tag_m, progress_path, add_tag_m_name)

scheduler = sched.scheduler(time.time, time.sleep)

def update_library():
    for library in plexserver.library.sections():
        _LOGGER.info(f"{plugins_name}定时开始刷新媒体库：{library}")
        library.update()

def add_tag_m(add_tag_m, progress_path, add_tag_m_name):
    monitor_clients(qb_urls, qb_ports, usernames, passwords, add_tag, add_tag_m, progress_path, add_tag_m_name)

def send_heartbeat():
    monitor_clients(qb_urls, qb_ports, usernames, passwords, add_tag, False, '', '')
    scheduler.enter(int(check_interval), 1, send_heartbeat)

@plugin.task('qb_tools', 'QB 添加标签', cron_expression='*/5 * * * *')
def task():
    if add_tag:
        scheduler.enter(0, 1, send_heartbeat)
        scheduler.run()

@plugin.task('update_plex_library', '刷新 PLEX 全库', cron_expression='30 1 * * *')
def update_plex_library_task():
    if update_plex_library_on:
        update_library()
