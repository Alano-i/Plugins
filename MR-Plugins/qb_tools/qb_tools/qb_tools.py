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
import shutil
import subprocess

import threading
import sched
from flask import Blueprint, request
from mbot.common.flaskutils import api_result
from mbot.register.controller_register import login_required
from mbot.openapi import media_server_manager

plexserver = media_server_manager.master_plex.plex
logger = logging.getLogger(__name__)
server = mbot_api
plugins_name = '「QB 工具箱」'
plugins_path = '/data/plugins/qb_tools'
ignore_torrents = []
old_tracker = ''
new_tracker = ''

def config_setup(config):
    global cfg,qb_urls, qb_ports, usernames, passwords, add_tag, check_interval, update_plex_library_on, random_set, library_set,auto_edit_tracker,delete_task,save_path,delete_local,delete_hard,hardlink_paths,del_day
    qb_urls = config.get('qb_urls', '')
    qb_ports = config.get('qb_ports', '')
    usernames = config.get('usernames', '')
    passwords = config.get('passwords', '')
    random_set = config.get('random_set', '')
    library_set = config.get('library_set', '')
    add_tag = config.get('add_tag', False)
    auto_edit_tracker = config.get('auto_edit_tracker', False)
    update_plex_library_on = config.get('update_plex_library_on', False)
    check_interval = config.get('check_interval', '30')

    delete_task = config.get('delete_task', False)
    save_path = config.get('save_path', '').splitlines()
    delete_local = config.get('delete_local', False)
    delete_hard = config.get('delete_hard', False)
    delete_hard = delete_local and delete_hard
    hardlink_paths = config.get('hardlink_paths', '').splitlines()
    del_day = config.get('del_day', '')
    try:
        del_day = int(del_day)
    except ValueError:
        del_day = 7
    cfg=config
 

@plugin.after_setup
def after_setup(plugin_meta: PluginMeta, config: Dict[str, Any]):
    config_setup(config)

    
@plugin.config_changed
def config_changed(config: Dict[str, Any]):
    config_setup(config)
    logger.warning(f"{plugins_name}已重新加载设置，将自动重启 Mbot，请等待重启完成")
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
        logger.info(f"「接收 PLEX 刷新路径」接收到更新数据 ['lib_name': '{lib_name}', 'filepath': '{filepath}']，等待 {delay_time} 秒后通知刷新")
        code = 0
        result = {'state':'接收更新数据成功'}
        thread = threading.Thread(target=plex_update, args=(lib_name, filepath, delay_time))
        thread.start()
    except Exception as e:
        logger.error(f'「接收 PLEX 刷新路径」未接收到更新数据，传参错误，{e}')
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
                logger.error(f"没有找到媒体库：{lib_name}")
            logger.info(f"「通知 PLEX 刷新媒体库」已通知 PLEX 刷新媒体库 ['{lib_name}'] 下的路径：['{filepath}']")
            break
        except Exception as e:
            logger.error(f"「通知 PLEX 刷新媒体库」第 {i+1}/10 次通知 PLEX 刷新媒体库 ['{lib_name}'] 下的路径：['{filepath}'] 失败，原因：{e}")
            time.sleep(5)
            continue

def replace_tracker(tracker,old_tracker,new_tracker,auto_edit_tracker):
    new_urls = tracker
    if old_tracker and old_tracker in tracker and "hd4fans.org" not in old_tracker:
        new_urls = tracker.replace(old_tracker, new_tracker)
    if (auto_edit_tracker or "hd4fans.org" in old_tracker) and "hd4fans.org" in tracker:
        base_url = ".hd4fans.org" + tracker.split('hd4fans.org')[1]
        new_urls = '\n'.join([
            f"https://tracker{base_url}",
            f"http://tracker{base_url}",
            f"https://pt{base_url}",
            f"http://pt{base_url}"
        ])
    return new_urls


def is_sub_path(torrent_path, target_path):
    torrent_path = os.path.abspath(torrent_path)
    target_path = os.path.abspath(target_path)
    return torrent_path == target_path or torrent_path.startswith(os.path.join(target_path, ''))

def format_time_delta(seconds):
    """把秒数格式化成 天时分秒"""
    days = int(seconds // (24 * 3600))
    hours = int((seconds % (24 * 3600)) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    formated_time=f"{days}天{hours}小时{minutes}分{secs}秒"
    return formated_time.replace('0天','').replace('0小时','').replace('0分','').replace('0秒','')

def delete_with_hardlinks(file_path, search_paths):
    """删除文件及其在指定目录下的硬链接"""
    try:
        inode = os.stat(file_path).st_ino
        for sp in search_paths:
            if not os.path.exists(sp):
                continue
            try:
                # 查找硬链接文件
                result = subprocess.check_output(['find', sp, '-xdev', '-inum', str(inode)], text=True)
                paths = result.strip().split('\n')
                for p in paths:
                    if os.path.exists(p):
                        # 删除 sp 下一级目录
                        relative_path = os.path.relpath(p, sp)  # 计算相对路径
                        first_level_dir = relative_path.split(os.sep)[0]  # 第一级目录
                        dir_to_delete = os.path.join(sp, first_level_dir)
                        if os.path.exists(dir_to_delete):
                            try:
                                shutil.rmtree(dir_to_delete)
                                logger.info(f"{plugins_name}已删除硬链接目录: {dir_to_delete}")
                                return True # 找到一个就够
                            except Exception as e:
                                logger.info(f"{plugins_name}删除硬链接目录 {dir_to_delete} 出错: {e}")
                            
                return False
            except subprocess.CalledProcessError:
                # find 没找到结果时会报错，忽略即可
                pass
    except Exception as e:
        logger.info(f"{plugins_name}删除硬链接失败: {file_path}, 错误: {e}")
        return False


def delete_main(qb):
    # ============ 删除 7 天前完成的任务 ============
    # save_path = ['/Media/downloads/短剧/', '']     # qb下载目录
    # hardlink_paths = ['/Volumes/影音视界-1/短剧']      # 需要查找硬链接的目录
    logger.info(f"{plugins_name}开始删除完成时间超过「{del_day}」天的种子，下载路径: {save_path}，硬链接路径：{hardlink_paths}，删除本地文件：{delete_local}，删除硬链接：{delete_hard}")
    now = time.time()
    del_deadline = del_day * 24 * 60 * 60
    completed_torrents = qb.torrents.info(status_filter='completed')
    for torrent in completed_torrents:
        try:
            # 判断保存路径是否在目标列表
            if any(is_sub_path(torrent.save_path, path) for path in save_path if path):
                if torrent.completion_on:
                    delta = now - torrent.completion_on
                    if delta > del_deadline:
                        time_str = format_time_delta(delta)
                        logger.info(f"{plugins_name}即将删除种子: {torrent.name}, 保存路径: {torrent.save_path}, 完成时间超过{del_day}天 ({time_str})")
                        
                        # 先删除种子相关文件及硬链接
                        files = qb.torrents_files(torrent.hash)
                        for f in files:
                            file_path = os.path.join(torrent.save_path, f.name)
                            if os.path.exists(file_path) and delete_hard and delete_local:
                                if delete_with_hardlinks(file_path, hardlink_paths):
                                    break

                        # 最后删除 qbittorrent 任务
                        qb.torrents_delete(delete_files=delete_local, torrent_hashes=torrent.hash)
                        if delete_local:
                            logger.info(f"{plugins_name}已删除下载任务且已删除本地文件: {torrent.name}, 保存路径: {torrent.save_path}\n")
                        else:
                            logger.info(f"{plugins_name}已删除下载任务，未删除本地文件: {torrent.name}, 保存路径: {torrent.save_path}\n")
        except Exception as e:
            logger.info(f"{plugins_name}处理种子 {torrent.name} 出错: {e}")


def qb_tools(qb_url, qb_port, username, password, add_tag, add_tag_m, progress_path, add_tag_m_name,edit_tracker,auto_edit_tracker,del_task_falg):
    if all([not qb_url, not qb_port, not username, not password]):
        return
    # 创建 qBittorrent 客户端
    qb = qbittorrentapi.Client(host=qb_url, port=qb_port, username=username, password=password)
    try:
        qb.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        logger.error(f"{plugins_name}Qbittorrent: {qb_url}  登入失败!，原因：{e}")
        return
    if delete_task and del_task_falg:
        delete_main(qb)
    if add_tag:
        # 正在下载的种子
        progress_torrent = qb.torrents.info(status_filter='downloading')
        for torrent in progress_torrent:
            if not torrent.tags:
                torrent_name = torrent.name
                # logger.info(f"ignore_torrents: {ignore_torrents}")
                if torrent_name not in ignore_torrents:
                    label = get_tmdbid(torrent_name)
                    if label:
                        torrent.add_tags(label)
                    else:
                        logger.error(f"{plugins_name}['{torrent_name}'] 没有获取到该种子的 tmdbid，添加标签 tmdb=none")
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
                        logger.warning(f"{plugins_name}为种子 ['{torrent.name}'] 添加标签失败，因为已有标签：['{torrent.tags}']")
        else:
            logger.error(f"{plugins_name}手动添加标签 ['{add_tag_m_name}'] 失败，参数设置错误")
    torrents = ''
    if edit_tracker:
        # 所有种子
        torrents = qb.torrents.info()
    if auto_edit_tracker:
        torrents = qb.torrents.info(status_filter='downloading')
    edit_count = 0
    if (edit_tracker or auto_edit_tracker) and torrents:
        org_trackers_str = ''
        for torrent in torrents:
            org_trackers = []
            trackers = torrent.trackers
            for tracker in trackers:
                if tracker['url'].startswith('http'):
                    if "hd4fans.org" in tracker['url']:
                        org_trackers.append(tracker['url'])
            if org_trackers: org_trackers_str = '\n'.join(org_trackers)
            if all(keyword in org_trackers_str for keyword in ["https://tracker", "http://tracker", "https://pt", "http://pt"]):
                continue
            for tracker in trackers:
                if tracker['url'].startswith('http'):
                    updated_trackers = replace_tracker(tracker['url'],old_tracker,new_tracker,auto_edit_tracker)
                    if updated_trackers and updated_trackers != tracker['url']:
                        if '\n' in updated_trackers:
                            qb.torrents_add_trackers(torrent_hash=torrent['hash'], urls=updated_trackers)
                            edit_count = edit_count+1
                        else:
                            qb.torrents_edit_tracker(torrent_hash=torrent['hash'], original_url=tracker['url'], new_url=updated_trackers)
                            edit_count = edit_count+1
        if edit_count > 0:
            if edit_tracker:
                logger.info(f"{plugins_name}已将 {edit_count} 个tracker 由 ['{old_tracker}'] 修改为 ['{new_tracker}']")
            if auto_edit_tracker:
                logger.info(f'{plugins_name}已自动完成 {edit_count} 个兽站tracker修改')

 
def get_tmdbid(torrent_name):
    label = ''
    media_tmdb_id = ''
    media = server.amr.analysis_string(torrent_name)
    # media = server.amr.analysis_string('三体.ThreeBody.S01.2023.2160p.V2.WEB-DL.H265.AAC-HHEB')
    # json_string = json.dumps(vars(media), ensure_ascii=False)
    # logger.info(f'解析到的媒体信息：{json_string}')
    if media:
        media_tmdb_id = getattr(media, 'tmdb_id', None)
        # label = f"[tmdb={media_tmdb_id}]" if media_tmdb_id else ''
        media_type = getattr(media.media_type, 'value', None)
        if media_type == 'Movie':
            label = f'tmdb=m-{media_tmdb_id}' if media_tmdb_id else ''
        elif media_type == 'TV':
            label = f'tmdb=tv-{media_tmdb_id}' if media_tmdb_id else ''
    return label

def monitor_clients(qb_urls, qb_ports, usernames, passwords, add_tag, add_tag_m, progress_path, add_tag_m_name,edit_tracker,auto_edit_tracker,del_task_falg):
    qb_urls = qb_urls.split('\n') if '\n' in qb_urls else [qb_urls]
    qb_ports = qb_ports.split('\n') if '\n' in qb_ports else [qb_ports]
    usernames = usernames.split('\n') if '\n' in usernames else [usernames]
    passwords = passwords.split('\n') if '\n' in passwords else [passwords]
    clients = [
        {'host': qb_urls[i], 'port': qb_ports[i], 'username': usernames[i], 'password': passwords[i]}
        for i in range(len(qb_urls))
    ]
    for client in clients:
        qb_tools(client['host'], client['port'], client['username'], client['password'], add_tag, add_tag_m, progress_path, add_tag_m_name,edit_tracker,auto_edit_tracker,del_task_falg)

scheduler = sched.scheduler(time.time, time.sleep)

def update_library(library_names):
    if library_names:
        libraries = [plexserver.library.section(name) for name in library_names]
    else:
        libraries = plexserver.library.sections()
    for library in libraries:
        logger.info(f"{plugins_name}定时开始刷新媒体库：{library}")
        library.update()
        time.sleep(10)

def add_tag_m(add_tag_m, progress_path, add_tag_m_name):
    monitor_clients(qb_urls, qb_ports, usernames, passwords, add_tag, add_tag_m, progress_path, add_tag_m_name, False, False,False)


def edit_tracker_m(old, new, edit_tracker):
    global old_tracker, new_tracker
    if old and new:
        old_tracker = old
        new_tracker = new
    monitor_clients(qb_urls, qb_ports, usernames, passwords, False, False, '', '',edit_tracker,False,False)

def send_heartbeat():
    monitor_clients(qb_urls, qb_ports, usernames, passwords, add_tag, False, '', '',False,auto_edit_tracker,False)
    scheduler.enter(int(check_interval), 1, send_heartbeat)

@plugin.task('qb_tools', 'QB 自动添加标签', cron_expression='*/5 * * * *')
def task():
    if add_tag:
        scheduler.enter(0, 1, send_heartbeat)
        scheduler.run()

@plugin.task('auto_edit_tracker', 'QB 自动修改tracker', cron_expression='*/4 * * * *')
def task():
    if auto_edit_tracker:
        scheduler.enter(0, 1, send_heartbeat)
        scheduler.run()

@plugin.task('update_plex_library', '刷新 PLEX 媒体库', cron_expression='30 1 * * *')
def update_plex_library_task():
    if update_plex_library_on:
        if library_set.lower() != 'all' or library_set:
            library_names =  library_set.split(',')
        else:
            library_names = ''
        update_library(library_names)
        logger.info(f"{plugins_name}定时刷新媒体库完成")


def delete_task_m(save_path0,delete_local0,delete_hard0,hardlink_paths0,del_day0):
    global save_path, delete_hard, hardlink_paths, delete_task,del_day,delete_local
    save_path = save_path0
    delete_local = delete_local0
    delete_hard = delete_hard0
    hardlink_paths = hardlink_paths0
    delete_task = True
    del_day = del_day0
    monitor_clients(qb_urls, qb_ports, usernames, passwords, False, False, '', '','','',True)
    config_setup(cfg)

# @plugin.task('delete_t', '自动删种', cron_expression='0 1 * * *')
@plugin.task('delete_t', '自动删种', cron_expression='45 7/15 * * *')
def delete_t_task():
    if delete_task:
        monitor_clients(qb_urls, qb_ports, usernames, passwords, False, False, '', '','','',True)
        logger.info(f"{plugins_name}定时自动删种完成")