#!/usr/bin/env python3
from mbot.core.plugins import plugin
from mbot.core.plugins import PluginContext, PluginMeta
from mbot.openapi import mbot_api
from typing import Dict, Any
import logging
from .audio_tools import audio_tools_config
from .podcast import podcast_config
from .command import cmd_config
from .functions import hlink

logger = logging.getLogger(__name__)
server = mbot_api
plugins_name = '「有声书工具箱」'
plugins_path = '/data/plugins/audio_clip'
exts = ['.m4a', '.mp3', '.flac']
dst_base_path = f"/app/frontend/static/podcast/audio"
# src_base_path = "/Media/有声书"

@plugin.after_setup
def after_setup(plugin_meta: PluginMeta, config: Dict[str, Any]):
    config['plugins_name'] = plugins_name
    config['plugins_path'] = plugins_path
    config['exts'] = exts
    config['dst_base_path'] = dst_base_path

    src_base_path = config.get('src_base_path','')
    audio_tools_config(config)
    podcast_config(config)
    cmd_config(config)
    hlink(src_base_path, dst_base_path)
    logger.info(f'{plugins_name}已加载配置并链接有声书资源到静态目录')

@plugin.config_changed
def config_changed(config: Dict[str, Any]):
    config['plugins_name'] = plugins_name
    config['plugins_path'] = plugins_path
    config['exts'] = exts
    config['dst_base_path'] = dst_base_path

    src_base_path = config.get('src_base_path','')
    audio_tools_config(config)
    podcast_config(config)
    cmd_config(config)
    hlink(src_base_path, dst_base_path)
    logger.info(f'{plugins_name}已加载配置并链接有声书资源到静态目录')
