#!/usr/bin/env python3
from mbot.core.plugins import plugin
from mbot.core.plugins import PluginContext, PluginMeta
from mbot.openapi import mbot_api
from typing import Dict, Any
import logging
import threading
from .audio_tools import audio_tools_config
from .event import event_config
from .podcast import podcast_config
from .command import cmd_config
from .functions import hlink
logger = logging.getLogger(__name__)
server = mbot_api

def config_setup(config):
    plugins_name = '「有声书工具箱」'
    plugins_path = '/data/plugins/audio_tools'
    exts = ['.m4a', '.mp3', '.flac','.m4b']
    dst_base_path = f"/app/frontend/static/podcast/audio"
    # dst_base_path = f"/data/plugins/podcast"
    # src_base_path = "/Media/有声书"
    config['plugins_name'] = plugins_name
    config['plugins_path'] = plugins_path
    config['exts'] = exts
    config['dst_base_path'] = dst_base_path
    src_base_path_music = config.get('src_base_path_music','')
    src_base_path_book = config.get('src_base_path_book','')
    book_watch_folder = config.get('book_watch_folder','')
    logger.info(f"{plugins_name}有声书监控文件夹：['{book_watch_folder}']")
    logger.info(f"{plugins_name}有声书父文件夹：['{src_base_path_book}']")
    logger.info(f"{plugins_name}音乐父文件夹：['{src_base_path_music}']")
    event_config(config)
    audio_tools_config(config)
    podcast_config(config)
    cmd_config(config)
    # 有声书链接线程
    if src_base_path_book:
        logger.info(f"{plugins_name}开始链接 ['有声书'] 资源到静态目录")
        thread_book = threading.Thread(target=hlink, args=(src_base_path_book, dst_base_path))
        thread_book.start()
    # 音乐链接线程
    if src_base_path_music:
        logger.info(f"{plugins_name}开始链接 ['音乐'] 资源到静态目录")
        thread_music = threading.Thread(target=hlink, args=(src_base_path_music, dst_base_path))
        thread_music.start()

@plugin.after_setup
def after_setup(plugin_meta: PluginMeta, config: Dict[str, Any]):
    config_setup(config)

@plugin.config_changed
def config_changed(config: Dict[str, Any]):
    config_setup(config)
