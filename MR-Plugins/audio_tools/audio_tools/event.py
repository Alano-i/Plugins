import os
import logging
from mbot.core.event.models import EventType
from mbot.core.plugins import plugin
from mbot.core.plugins import PluginContext
from typing import Dict
from .functions import *
from .podcast import podcast_main
logger = logging.getLogger(__name__)

def event_config(config):
    global plugins_name,src_base_path_book, src_base_path_music,book_watch_folder,check_book,dst_base_path
    plugins_name = config.get('plugins_name','')
    # src_base_path = config.get('src_base_path_book','')
    src_base_path_book = config.get('src_base_path_book','')
    src_base_path_music = config.get('src_base_path_music','')

    dst_base_path = config.get('dst_base_path','')
    book_watch_folder = config.get('book_watch_folder','')
    check_book = config.get('check_book',False)
    if book_watch_folder:
        book_watch_folder = process_path(book_watch_folder)
    if src_base_path_book:
        src_base_path_book = process_path(src_base_path_book)
    if src_base_path_music:
        src_base_path_music = process_path(src_base_path_music)
    
@plugin.on_event(bind_event=[EventType.DownloadCompleted], order=20)
def on_event(ctx: PluginContext, event_type: str, data: Dict):
    if not check_book or not book_watch_folder: return
    """
    触发绑定的事件后调用此函数
    函数接收参数固定。第一个为插件上下文信息，第二个事件类型，第三个事件携带的数据
    """
    save_path = data.get("source_path")
    if not save_path:
        return
    else:
        first_path,save_path = extract_file_or_folder_path(save_path)
        first_path = process_path(first_path)
        save_path = process_path(save_path)
        
    """
    first_path：/Media/downloads/有声书
    save_path：/Media/downloads/有声书/九阳神王.寂小贼.演播红薯中文网.2022.AAC.32kbps-RL4B
    save_path_name：九阳神王.寂小贼.演播红薯中文网.2022.AAC.32kbps-RL4B
    """
    # 检查是否匹配监控目录配置
    if first_path == book_watch_folder:
        logger.info(f"{plugins_name}['{save_path}'] 目录是有声书监控目录，运行生成播客源")
        is_group = True
        short_filename = True
        is_book = True
        book_title,podcast_author,reader,pub_year,podcast_category,podcast_summary = '','','','','',''
        book_title,podcast_author,reader,pub_year,podcast_category,podcast_summary = get_audio_info_all(save_path,book_title,podcast_author,reader,pub_year,podcast_category,podcast_summary)
        auto_podcast(save_path,first_path,book_title,podcast_summary,podcast_category,podcast_author,reader,pub_year,is_group,short_filename,is_book)
    else:
        logger.info(f"{plugins_name} ['{save_path}'] 目录不是有声书监控目录，不生成播客源")
        return
    
def auto_podcast(save_path,first_path,book_title,podcast_summary,podcast_category,podcast_author,reader,pub_year,is_group,short_filename,is_book):
    src_base_path = src_base_path_book if is_book else src_base_path_music
    # logger.info(f"src_base_path:{src_base_path}")
    if not first_path:
        first_path,save_path = extract_file_or_folder_path(save_path)
    save_path_name = os.path.basename(save_path)
    # book_title,podcast_author,reader,pub_year,podcast_category,podcast_summary = get_audio_info_all(audio_path,book_title,podcast_author,reader,pub_year,podcast_category,podcast_summary)
    if book_title:
        audio_path = os.path.join(src_base_path, book_title)
        if not os.path.samefile(first_path, src_base_path):
            if not hard_link(save_path, audio_path):
                return
            hlink(audio_path, os.path.join(dst_base_path, book_title))
        else:
            audio_path = save_path
            hlink(audio_path, os.path.join(dst_base_path, save_path_name))
        logger.info(f"{plugins_name}解析后的数据 audio_path：['{audio_path}'] book_title：['{book_title}'] 作者：['{podcast_author}'] 演播：['{reader}'] 发布年份：['{pub_year}'] 简介：['{podcast_summary}'] 题材：['{podcast_category}']")
        result = podcast_main(book_title, audio_path, podcast_summary, podcast_category, podcast_author,reader,pub_year,is_group,short_filename,is_book)
        return result
    else:
        logger.error(f"{plugins_name}解析 ['{save_path}'] 的书名和作者失败，可能是文件夹命名不规范，结束任务")
        return False

# data={
#     'sub_id': None, 
#     'uid': '', 
#     'media_type': 'Other', 
#     'file_size': '568.09 MB', 
#     'media_stream': {'resolution': '2K', 'media_source': None, 'media_codec': None, 'media_audio': ['AAC'], 'release_team': None}, 
#     'source_path': '/Media/downloads/有声书/X档案研究所.夷梦.演播七十.2018.AAC.32kbps-RL4B/X档案研究所.夷梦.演播七十.2018.AAC.32kbps.disk01-RL4B.m4b',  # 文件夹中只有一个文件
#     'source_path': '/Media/downloads/有声书/X档案研究所.夷梦.演播七十.2018.AAC.32kbps-RL4B',  # 文件夹中有多个文件
#     'torrent_name': 'X档案研究所.夷梦.演播七十.2018.AAC.32kbps-RL4B', 
#     'torrent_subject': '', 
#     'torrent_id': 0, 
#     'torrent_hash': '9b86e4e2913ed78733fc678bf08fd2e770dd50bf', 
#     'torrent_url': '', 
#     'site_id': 'unknown', 
#     'site_name': None
# }