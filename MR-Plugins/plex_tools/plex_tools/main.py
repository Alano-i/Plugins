import logging
from typing import Dict
from flask import Blueprint, request
from mbot.common.flaskutils import api_result
from mbot.register.controller_register import login_required
import json
import time
import threading
from plexapi.server import PlexServer
from mbot.core.event.models import EventType
from mbot.core.plugins import PluginContext,PluginMeta,plugin
from mbot.openapi import mbot_api
from . import plex_sortout
from .get_top250 import get_top250_config
from .sub_to_mbot import import_config
from .add_info import add_config,add_info_to_posters_main
logger = logging.getLogger(__name__)
plugins_name = '「PLEX 工具箱」'
plex_webhook = Blueprint('get_plex_event', __name__)
"""
把flask blueprint注册到容器
这个URL访问完整的前缀是 /api/plugins/你设置的前缀
"""
plugin.register_blueprint('get_plex_event', plex_webhook)
server = mbot_api
max_retry = 3

@plugin.after_setup
def after_setup(plugin: PluginMeta, plugin_conf: dict):
    """
    插件加载后执行的操作
    """
    logger.info(f'{plugins_name}插件开始加载')
    # global added, libtable , plex_url, plex_token
    global added,collection_on,libtable,libstr,add_media_info,add_info_toggle
    global plex_url, plex_token,custom_url,mbot_url,mbot_api_key,check,update_add_info
    plex_url = plugin_conf.get('plex_url','')
    plex_token = plugin_conf.get('plex_token','')
    custom_url = plugin_conf.get('custom_url','')
    mbot_url = plugin_conf.get('mbot_url','')
    mbot_api_key = plugin_conf.get('mbot_api_key','')
    add_info_toggle = plugin_conf.get('add_info_toggle',True)
    
    # mbot_api_key = server.auth.get_default_ak()


    update_add_info = plugin_conf.get('update_add_info',True)
    check = plugin_conf.get('check',True)
    added = plugin_conf.get('Added') if plugin_conf.get('Added') else None
    add_media_info = plugin_conf.get('add_media_info') if plugin_conf.get('add_media_info') else None
    collection_on = plugin_conf.get('Collection') if plugin_conf.get('Collection') else None
    if added:
        logger.info(f'{plugins_name}启用「PLEX 入库事件」触发整理实时入库的媒体')
    else:
        logger.info(f'{plugins_name}未启用「PLEX 入库事件」触发整理实时入库的媒体')
    libstr = plugin_conf.get('LIBRARY')
    if libstr:
        if str(libstr).lower() != 'all':
            libtable=libstr.split(',')
            logger.info(f'{plugins_name}需要整理的库：{libtable}')
            # plugin_conf['library']=libtable
    else:
        logger.info(f'{plugins_name}未设置需要整理的媒体库名称，将默认整理所有库')
        # plugin_conf['library'] = 'ALL'   
    # 传递设置参数
    get_top250_config(plugin_conf)
    import_config(plugin_conf)
    add_config(plugin_conf)
    plex_sortout.setconfig(plugin_conf)
    logger.info(f'{plugins_name}自定义参数加载完成')
    # printAllMembers(plex_sortout)

@plugin.config_changed
def config_changed(plugin_conf: dict):
    """
    插件变更配置后执行的操作
    """
    logger.info(f'{plugins_name}配置发生变更，加载新配置')
    global added,collection_on,libtable,libstr,add_media_info,add_info_toggle
    global plex_url, plex_token,custom_url,mbot_url,mbot_api_key,check,update_add_info
    plex_url = plugin_conf.get('plex_url','')
    plex_token = plugin_conf.get('plex_token','')
    custom_url = plugin_conf.get('custom_url','')
    mbot_url = plugin_conf.get('mbot_url','')
    mbot_api_key = plugin_conf.get('mbot_api_key','')
    update_add_info = plugin_conf.get('update_add_info',True)
    add_info_toggle = plugin_conf.get('add_info_toggle',True)
    check = plugin_conf.get('check',True)
    added = plugin_conf.get('Added') if plugin_conf.get('Added') else None
    add_media_info = plugin_conf.get('add_media_info') if plugin_conf.get('add_media_info') else None
    collection_on = plugin_conf.get('Collection') if plugin_conf.get('Collection') else None
    if added:
        logger.info(f'{plugins_name}启用「PLEX 入库事件」触发整理实时入库的媒体')
    else:
        logger.info(f'{plugins_name}未启用「PLEX 入库事件」触发整理实时入库的媒体')
    libstr = plugin_conf.get('LIBRARY')
    if libstr:
        if str(libstr).lower() != 'all':
            libtable=libstr.split(',')
            logger.info(f'{plugins_name}需要整理的库：{libtable}')
            # plugin_conf['library']=libtable
    else:
        logger.info(f'{plugins_name}未设置需要整理的媒体库名称，将默认整理所有库')
        # plugin_conf['library'] = 'ALL'
    
    # 传递设置参数
    get_top250_config(plugin_conf)
    import_config(plugin_conf)
    add_config(plugin_conf)
    plex_sortout.setconfig(plugin_conf)
    logger.info(f'{plugins_name}自定义参数加载完成')
    # printAllMembers(plex_sortout)

def printAllMembers(cls):
    print('\n'.join(dir(cls)))

def set_plex():
    if  plex_url and plex_token:
        plexserver = PlexServer(plex_url, plex_token)
        # settings = plexserver.settings
        # 开启GDM网络发现
        plexserver.settings.get('gdmEnabled').set(True)
        if custom_url:
            if plexserver.settings.get('customConnections').value != custom_url:
                # 设置自定义域名
                plexserver.settings.get('customConnections').set(custom_url)
        # 开启webhooks开关
        plexserver.settings.get('webHooksEnabled').set(True)
        # 开启通知推送开关
        plexserver.settings.get('pushNotificationsEnabled').set(True)
        plexserver.settings.save()

        if mbot_url and mbot_api_key:
            webhook_url = f'{mbot_url}/api/plugins/get_plex_event/webhook?access_key={mbot_api_key}'
            # 自动设置 webhooks
            account = plexserver.myPlexAccount()
            webhooks = account.webhooks()
            if webhook_url not in webhooks:
                webhooks.append(webhook_url)
                account.setWebhooks(webhooks)
                logger.info(f"{plugins_name} 已向 PLEX 服务器添加 Webhook")
    else:
        logger.error(f'{plugins_name}PLEX URL 或 TOKEN 未设置，无法检查设置')

last_event_time = 0
last_event_count = 1
# 接收 plex 服务器主动发送的事件
@plex_webhook.route('/webhook', methods=['POST'])
@login_required() # 接口access_key鉴权
def webhook():
    global last_event_time, last_event_count
    payload = request.form['payload']
    data = json.loads(payload)
    # plex_event = data['event']
    plex_event = data.get('event', '')
    # if plex_event in ['library.on.deck', 'library.new', 'media.play', 'media.pause', 'media.resume'] and added:
    if plex_event in ['library.on.deck', 'library.new'] and added:
        metadata = data.get('Metadata', '')
        library_section_title = metadata.get('librarySectionTitle', '')
        # 媒体库类型：show artist movie photo
        library_section_type = metadata.get('librarySectionType', '')
        rating_key = metadata.get('ratingKey', '')
        parent_rating_key = metadata.get('parentRatingKey', '')
        grandparent_rating_key = metadata.get('grandparentRatingKey', '')
        grandparent_title = metadata.get('grandparentTitle', '')
        parent_title = metadata.get('parentTitle', '')
        org_title = metadata.get('title', '')
        org_type = metadata.get('type', '')

        # 如果是照片库直接跳过
        if library_section_type == 'photo':
            return api_result(code=0, message=plex_event, data=data)
        ########################## 始终处理 ##########################
        logger.info(f'{plugins_name}接收到 PLEX 通过 Webhook 传过来的「入库事件」，开始分析事件')
        # 执行自动整理
        thread = threading.Thread(target=plex_sortout.process_new, args=(library_section_title,rating_key,parent_rating_key,grandparent_rating_key,grandparent_title,parent_title,org_title,org_type,add_media_info,add_info_toggle))
        thread.start()
        # 等待线程结束
        # thread.join()

        ########################## 15秒内处理一次 ##########################
        # if time.time() - last_event_time < 15:
        #     last_event_count = last_event_count + 1
        #     logger.info(f'{plugins_name}15 秒内接收到 {last_event_count} 条入库事件，只处理一次')
        # else:
        #     last_event_time = time.time()
        #     last_event_count = 1
        #     # time.sleep(60)
        #     logger.info(f'{plugins_name}接收到 PLEX 通过 Webhook 传过来的「入库事件」，开始分析事件')
        #     # 执行自动整理
        #     thread = threading.Thread(target=plex_sortout.process_new, args=(library_section_title,rating_key,parent_rating_key,grandparent_rating_key,grandparent_title,parent_title,org_title,org_type))
        #     thread.start()

    return api_result(code=0, message=plex_event, data=data)

    # plex_event_all = {
    #     'media.pause': '暂停',
    #     'media.play': '开始播放',
    #     'media.resume': '恢复播放',
    #     'media.stop': '停止播放',
    #     'library.on.deck': '新片入库',
    #     'library.new': '新片入库'
    # }

@plugin.task('process_collection', '「整理 PLEX 合集」', cron_expression='50 4 * * *')
def task():
    if collection_on:
        logger.info(f'{plugins_name}定时任务启动，开始处理 PLEX 合集')
        plex_sortout.process_collection()
    else:
        logger.info(f'{plugins_name}定时任务启动，未开启合集整理，跳过处理')

@plugin.task('process_recent', '「整理最近10项和添加海报信息」', cron_expression='18 3 * * *')
def process_recent():
    if str(libstr).lower() == 'all' or not libstr:
        try:
            libtables = plex_sortout.get_library()
            libtable = [value['value'] for value in libtables]
        except Exception as e:
            logger.error(f"{plugins_name}获取所有媒体库出错，原因：{e}")
    else:
        libtable=libstr.split(',')
    logger.info(f"{plugins_name}开始整理媒体库中最近10项")
    plex_sortout.process_all(libtable,'10','run_all',0,False,True)
    logger.info(f"{plugins_name}媒体库中最近10项整理完成")
    if not add_info_toggle:
        logger.info(f'{plugins_name}未开启添加海报信息开关，跳过。')
        return
    show_log = False
    force_add = False
    restore = False
    only_show = False
    logger.info(f"{plugins_name}开始为海报添加媒体信息，已添加信息的海报将自动跳过")
    for i in range(len(libtable)):
        add_info_to_posters_main(libtable[i],force_add,restore,show_log,only_show)
    logger.info(f"{plugins_name}为海报添加媒体信息完成，已自动跳过处理过的海报")

@plugin.task('re_add_all', '「更新海报信息」', cron_expression='10 1 * * tue,fri')
def re_add_all():
    if update_add_info:
        logger.info(f"{plugins_name}开始为所有库中的所有海报重新添加媒体信息，已添加信息的海报将重新添加，主要为了更新评分，每周2 和 周5 凌晨 1:10 执行一次")
        if not add_info_toggle:
            logger.info(f'{plugins_name}未开启添加海报信息开关，跳过。')
            return
        if str(libstr).lower() == 'all' or not libstr:
            try:
                libtables = plex_sortout.get_library()
                libtable = [value['value'] for value in libtables]
            except Exception as e:
                logger.error(f"{plugins_name}获取所有媒体库出错，原因：{e}")
        else:
            libtable=libstr.split(',')
        show_log = False
        force_add = True
        restore = False
        only_show = False
        for i in range(len(libtable)):
            add_info_to_posters_main(libtable[i],force_add,restore,show_log,only_show)
        logger.info(f"{plugins_name}为重新为海报添加媒体信息完成，评分信息已是更新到最新")
    else:
        logger.info(f'{plugins_name}未开启每周更新海报评分开关，跳过。')


@plugin.task('set_plex', '「检查 PLEX 设置」', cron_expression='15 */2 * * *')
def set_plex_ckeck():
    if check:
        for retry_count in range(max_retry):
            try:
                set_plex()
                break
            except Exception as e:
                logger.error(f"{plugins_name} 第 {retry_count+1}/{max_retry} 次检查 PLEX 服务器设置出错，原因: {e}")
                time.sleep(5)
                continue

# @plugin.on_event(
#     bind_event=[EventType.DownloadCompleted], order=1)
# def on_event(ctx: PluginContext, event_type: str, data: Dict):
#     """
#     触发绑定的事件后调用此函数
#     函数接收参数固定。第一个为插件上下文信息，第二个事件类型，第三个事件携带的数据
#     """
#     # logger.info(f'{plugins_name}接收到「DownloadCompleted」事件，现在开始整理')
#     if not added:
#         logger.info(f'{plugins_name}接收到「下载完成事件」且未开启入库事件触发，现在开始整理')
#         plex_sortout.process()
#     else:
#         logger.info(f'{plugins_name}接收到「下载完成事件」但已开启入库事件触发，将等待 PLEX 入库后再整理')
    