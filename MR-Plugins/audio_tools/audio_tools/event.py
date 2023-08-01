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
    global plugins_name,src_base_path,book_watch_folder,check_book
    plugins_name = config.get('plugins_name','')
    src_base_path = config.get('src_base_path_book','')
    book_watch_folder = config.get('book_watch_folder','')
    check_book = config.get('check_book',False)
    if book_watch_folder:
        book_watch_folder = process_path(book_watch_folder)
    if src_base_path:
        src_base_path = process_path(src_base_path)

def get_bookname_and_author(save_path_name):
    # 定义匹配书名和播客作者的正则表达式
    # pattern = r'^(.+?)[\.-](.+?)[\.-]'
    pattern = r'^(.+?)[\.\-\s*]+(.+?)[\.\-\s*]+'
    # pattern = r'^(.+?)[\.\-\s*]+(.+?)[\.\-\s*]+(.+?)[\.\-\s*]'
    # 使用正则表达式匹配书名和播客作者
    match = re.search(pattern, save_path_name)
    # 如果匹配成功，则提取书名和播客作者
    if match:
        book_title = match.group(1).strip()
        podcast_author = match.group(2).strip()
        # narrators = match.group(3).strip().replace("演播","").strip()
        return book_title, podcast_author
    else:
        return '', '', ''
    
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
        save_path_name = os.path.basename(save_path)
    """
    first_path：/Media/downloads/有声书
    save_path：/Media/downloads/有声书/九阳神王.寂小贼.演播红薯中文网.2022.AAC.32kbps-RL4B
    save_path_name：九阳神王.寂小贼.演播红薯中文网.2022.AAC.32kbps-RL4B
    """
    # 检查是否匹配监控目录配置
    if first_path == book_watch_folder:
        logger.info(f"{plugins_name}['{save_path}'] 目录是有声书监控目录，运行生成播客源")
        book_title, podcast_author = get_bookname_and_author(save_path_name)
        if book_title:
            audio_path = os.path.join(src_base_path, book_title)
            podcast_summary = ''
            podcast_category = ''
            is_group = True
            short_filename = True
            is_book = True
            if not os.path.samefile(first_path, src_base_path):
                hlink_h(save_path, audio_path)
            logger.info(f"{plugins_name}解析后的数据 audio_path：['{audio_path}'] book_title：['{book_title}'] podcast_author：['{podcast_author}']")
            state = podcast_main(book_title, audio_path, podcast_summary, podcast_category, podcast_author,is_group,short_filename,is_book)
    else:
        logger.info(f"{plugins_name} ['{save_path}'] 目录不是有声书监控目录，不运行生成播客源")
        return
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
