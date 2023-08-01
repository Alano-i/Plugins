from mbot.core.plugins import plugin, PluginCommandContext, PluginCommandResponse,PluginMeta
from mbot.openapi import mbot_api
from mbot.core.params import ArgSchema, ArgType
from .audio_tools import audio_clip, move_to_dir, diy_abs, move_out, all_add_tag, add_cover
from .podcast import podcast_main,get_xml_url
import logging
import datetime
import time
import os
from .functions import *
server = mbot_api
logger = logging.getLogger(__name__)
plugins_name = '「有声书工具箱」'
exts = ['.m4a', '.mp3', '.flac','.m4b']
move_out_config = [
    {
        "name": "🔖 DIY元数据",
        "value": 'diy'
    },
    {
        "name": "🎯 运行移出文件夹操作",
        "value": 'move'
    },
    {
        "name": "📕 整理文件夹、DIY元数据",
        "value": 'add_and_move'
    }
]
clip_config = [
    {
        "name": "📕 剪辑、整理、添加元数据",
        "value": 'clip_and_move'
    },
    {
        "name": "🎯 仅剪辑",
        "value": 'clip'
    }
]
media_list = [
    {
        "name": "📕 有声书",
        "value": 'audio_book'
    },
    {
        "name": "🎹 音乐",
        "value": 'music'
    }
]

state_list = [
    {
        "name": "✅ 开启",
        "value": 'on'
    },
    {
        "name": "📴 关闭",
        "value": 'off'
    }
]
if server.common.get_cache('audio_clip', 'input_dirs'):
    last_time_input_dirs = uptime_input_dirs = server.common.get_cache('audio_clip', 'input_dirs')
else:
    last_time_input_dirs = '/Media/有声书/123456'

def cmd_config(config):
    global src_base_path_book,src_base_path_music,dst_base_path
    src_base_path_book = config.get('src_base_path_book','')
    src_base_path_music = config.get('src_base_path_music','')
    dst_base_path = config.get('dst_base_path','')

# 获取所有的播客源列表
def get_rss_url():
    global json_data
    no_data = [
        {
            "name": "没有获取到数据，可能还从未生成",
            "value": ''
        }
    ]
    file_path = f"{src_base_path_book}/podcast.json"
    # 判断文件是否存在
    if not os.path.exists(file_path):
        logger.warning(f"保存播客URL的json文件不存在，可能还从未生成！")
        json_data = {}
        return no_data
    json_data = read_json_file(file_path)
    if json_data:
        url_list = []
        for name, info in json_data.items():
            entry = {
                "name": name,
                "value": info["podcast_url"]
            }
            url_list.append(entry)
    else:
        logger.warning(f"保存播客URL的json文件为空，可能还从未生成！")
        url_list = no_data
    return url_list

# 根据选择的播客源，获取对应的xml与封面URL
def filter_json_by_podcast_url(url_list_config):
    filtered_data = {}
    for name, info in json_data.items():
        if info["podcast_url"] in url_list_config:
            filtered_data[name] = info
    return filtered_data


@plugin.command(name='audio_clip_m', title='音频剪辑', desc='剪辑片头片尾，修改整理元数据', icon='LibraryMusic',run_in_background=True)
def audio_clip_m_echo(ctx: PluginCommandContext,
                input_dirs: ArgSchema(ArgType.String, last_time_input_dirs, '输入路径，支持多条，一行一条 /Media/有声书', default_value = last_time_input_dirs, required=False),
                output_dir: ArgSchema(ArgType.String, '输出路径，默认：输入路径', '', default_value='', required=False),
                series: ArgSchema(ArgType.String, '书名', '', default_value='', required=True),
                cliped_folder: ArgSchema(ArgType.String, '已剪辑存放路径，默认：书名', '', default_value='', required=False),
                audio_start: ArgSchema(ArgType.String, '剪片头开始时间，默认：0，单位：秒', '', default_value='0', required=False),
                audio_end: ArgSchema(ArgType.String, '剪片尾倒数时间，默认：0，单位：秒', '', default_value='0', required=False),
                clip_configs: ArgSchema(ArgType.Enum, '选择操作：📕 剪辑、整理、添加元数据', '若仅剪辑，下方参数不生效。', enum_values=lambda: clip_config, default_value='clip_and_move', multi_value=False, required=False),
                use_filename_config: ArgSchema(ArgType.Enum, '根据文件名优化每集标题：✅ 开启', '', enum_values=lambda: state_list, default_value='on', multi_value=False, required=False),
                authors: ArgSchema(ArgType.String, '作者：填原著作家', '', default_value='', required=False),
                narrators: ArgSchema(ArgType.String, '演播者', '', default_value='', required=False),
                year: ArgSchema(ArgType.String, '发布年份', '', default_value='', required=False),
                albums: ArgSchema(ArgType.String, '专辑：留空自动按每100集划分', '', default_value='', required=False),
                art_album: ArgSchema(ArgType.String, '专辑艺术家：推荐填书名', '', default_value='', required=False),
                subject: ArgSchema(ArgType.String, '题材，如：武侠，相声', '', default_value='', required=False),
                podcast_summary: ArgSchema(ArgType.String, '简介，用于生成播客简介', '', default_value='', required=False)):
    src_base_path = src_base_path_book
    cliped_folder = cliped_folder or series
    use_filename = get_state(use_filename_config)
    logger.info(f"{plugins_name}任务\n开始运行音频剪辑\n输入路径：[{input_dirs}]\n输出路径：[{output_dir}/{cliped_folder}]\n开始时间：[{audio_start}]\n结束倒数秒数：[{audio_end}]\n\n整理参数如下：\n系列：['{series}']\n作者：['{authors}']\n演播者：['{narrators}']\n发布年份：['{year}']\n专辑：['{albums}']\n专辑艺术家：['{art_album}']")

    server.common.set_cache('audio_clip', 'input_dirs', input_dirs)
    input_dirs_s = input_dirs.split('\n')
    if albums: albums_s = albums.split('\n')
    album = ''
    for i, input_dir in enumerate(input_dirs_s):
        if '影音视界' in input_dir: input_dir = f"/Media{input_dir.split('影音视界')[1]}"
        input_dir = process_path(input_dir)
        output_dir = f"/{output_dir.strip('/')}" if output_dir else input_dir
        if albums: album = albums_s[i]
        audio_clip(input_dir,output_dir,cliped_folder,audio_start,audio_end,clip_configs,authors,year,narrators,series,podcast_summary,album,art_album,use_filename,subject)
        time.sleep(5)
        try:
            # dst_base_path = "/app/frontend/static/podcast/audio"
            # src_base_path = '/Media/有声书'
            hlink(src_base_path, dst_base_path)
            audio_path = f"{output_dir}/{cliped_folder}"
            is_group = True
            short_filename = True
            is_book = True
            time.sleep(5)
            podcast_main(series, audio_path, podcast_summary, subject, authors, is_group,short_filename,is_book)
        except Exception as e:
            logger.error(f"「生成播客源」失败，原因：{e}")
    return PluginCommandResponse(True, f'音频剪辑任务完成')

@plugin.command(name='poscast_m', title='生成播客源', desc='生成 Apple 播客源 URL', icon='Podcasts',run_in_background=True)
def poscast_m_echo(ctx: PluginCommandContext,
                is_book_config: ArgSchema(ArgType.Enum, '类型：📕 有声书', '', enum_values=lambda: media_list, default_value='audio_book', multi_value=False, required=False),
                book_title: ArgSchema(ArgType.String, '书名', '', default_value = '', required=False),
                audio_paths: ArgSchema(ArgType.String, '输入文件夹名称或完整路径', '支持多条，一行一条 /Media/有声书/', default_value='', required=False),
                podcast_summary: ArgSchema(ArgType.String, '简介', '', default_value='', required=False),
                podcast_category: ArgSchema(ArgType.String, '分类', '', default_value='', required=False),
                podcast_author: ArgSchema(ArgType.String, '作者', '', default_value='', required=False),
                is_group_config: ArgSchema(ArgType.Enum, '第1季强制200集：✅ 开启', '', enum_values=lambda: state_list, default_value='on', multi_value=False, required=False),
                short_filename_config: ArgSchema(ArgType.Enum, '根据文件名优化每集标题：✅ 开启', '', enum_values=lambda: state_list, default_value='on', multi_value=False, required=False)):
    # audio_paths = /Media/有声书/三国
    # src_base_path = /Media/有声书
    src_base_path = src_base_path_book if is_book_config == 'audio_book' else src_base_path_music
    is_book = False if is_book_config == 'music' else True
    state = False
    if not book_title and not audio_paths:
        logger.info(f"{plugins_name}未设置书名和路径，请设置后重试")
        return
    is_group = get_state(is_group_config)
    short_filename = get_state(short_filename_config)
    book_title_new = book_title
    try:
        logger.info(f"{plugins_name}任务 - 生成播客源 URL\n书名：['{book_title}']\n输入路径：['{audio_paths}']\n有声书简介：['{podcast_summary}']\n有声书分类：['{podcast_category}']\n作者：['{podcast_author}']\n第1季强制200集：{is_group}")
        audio_path_list = audio_paths.split('\n')
        for i, audio_path in enumerate(audio_path_list):
            audio_path = process_path(audio_path)
            if '影音视界' in audio_path: audio_path = f"/Media{audio_path.split('影音视界')[1]}"
            if src_base_path not in audio_path and audio_path:
                audio_path = f"/{src_base_path.strip('/')}{audio_path}"
            if not book_title:
                book_title_new = os.path.basename(audio_path).strip('/')
            else:
                if not audio_path:
                    audio_path = f"/{src_base_path.strip('/')}/{book_title}"
            state = podcast_main(book_title_new, audio_path, podcast_summary, podcast_category, podcast_author,is_group,short_filename,is_book)
    except Exception as e:
        logger.error(f"「生成播客源」失败，原因：{e}")
        return PluginCommandResponse(False, f'生成博客源 RSS XML 任务失败')
    if state:
        return PluginCommandResponse(True, f'生成博客源 RSS XML 任务完成')
    else:
        return PluginCommandResponse(False, f'生成博客源 RSS XML 任务失败')

@plugin.command(name='add_cover_m', title='修改音频封面', desc='修改音频封面', icon='Image',run_in_background=True)
def add_cover_m_echo(ctx: PluginCommandContext,
                audio_path: ArgSchema(ArgType.String, '输入路径', '/Media/有声书/', default_value='', required=True)):
    audio_path = process_path(audio_path)
    cover_art_path = os.path.join(audio_path, 'cover.jpg')
    logger.info(f"cover_art_path: {cover_art_path}")
    i=0
    try:
        for dirpath, _, filenames in os.walk(audio_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if datetime.datetime.now().second % 10 == 0 or i==0:
                    logger.info(f"{plugins_name}开始处理: {file_path}")
                add_cover(file_path,cover_art_path)
                i = i+1
        logger.info(f"{plugins_name}封面修改完成")
    except Exception as e:
        logger.error(f"「添加封面」失败，原因：{e}")
        return PluginCommandResponse(False, f'添加封面任务失败')
    return PluginCommandResponse(True, f'添加封面任务完成')

@plugin.command(name='get_xml_url', title='获取已生成播客源', desc='查看Apple播客源URL，并推送通知，点通知快速添加到播客App', icon='RssFeedSharp',run_in_background=True)
def get_xml_url_echo(ctx: PluginCommandContext, 
                url_list_config: ArgSchema(ArgType.Enum, '📕 选择书名，留空选择全部', '', enum_values=get_rss_url, default_value='all', multi_value=True, required=False),
                send_sms_config: ArgSchema(ArgType.Enum, '推送消息：✅ 开启', '开启后，选了多少个播客源就将收到多少条消息', enum_values=lambda: state_list, default_value='on', multi_value=False, required=False)):

    if not url_list_config or not json_data:
        return PluginCommandResponse(True, f'播客源 RSS URL 获取失败，可能还从未生成')
    send_sms = get_state(send_sms_config)
    if url_list_config == 'all':
        new_json_data = json_data
    else:
        new_json_data = filter_json_by_podcast_url(url_list_config)
    get_xml_url(new_json_data, send_sms)
    return PluginCommandResponse(True, f'已生成播客源 RSS URL 获取完成')

@plugin.command(name='diy_abs', title='修改metadata.abs', desc='修改 Audiobookshelf 元数据', icon='SwitchAccessShortcutAdd',run_in_background=True)
def diy_abs_echo(ctx: PluginCommandContext,
                folder_path: ArgSchema(ArgType.String, '输入路径', '/Media/有声书/', default_value='/Media/有声书/', required=True),
                series: ArgSchema(ArgType.String, '系列：推荐填写书名', '', default_value='', required=False),
                podcast_summary: ArgSchema(ArgType.String, '简介，用于生成播客简介', '', default_value='', required=False),
                authors: ArgSchema(ArgType.String, '作者：推荐填写原著作家', '', default_value='', required=False),
                narrators: ArgSchema(ArgType.String, '演播者，多个示例：演播A,,演播B,,', '', default_value='', required=False),
                year: ArgSchema(ArgType.String, '发布年份', '', default_value='', required=False)):
    folder_path = process_path(folder_path)
    logger.info(f"{plugins_name}任务\n开始运行 DIY 音频元数据\n输入路径：[{folder_path}]\n系列：['{series}']\n作者：['{authors}']\n演播者：['{narrators}']\n发布年份：['{year}']")
    diy_abs(folder_path, series, podcast_summary, authors, narrators, year)
    return PluginCommandResponse(True, f'DIY 音频元数据任务完成')

@plugin.command(name='move_to_dir', title='整理有声书', desc='分配到子文件夹 1-100 101-200 201-300, 并添加元数据', icon='RuleFolder',run_in_background=True)
def move_to_dir_echo(ctx: PluginCommandContext,
                move_out_configs: ArgSchema(ArgType.Enum, '选择运行的操作：🔖 DIY元数据', '', enum_values=lambda: move_out_config, default_value='diy', multi_value=False, required=False),
                output_dir: ArgSchema(ArgType.String, '输入路径', '/Media/有声书/', default_value='', required=True),
                series: ArgSchema(ArgType.String, '书名', '', default_value='', required=True),
                authors: ArgSchema(ArgType.String, '作者：填写原著作家', '', default_value='', required=False),
                use_filename_config: ArgSchema(ArgType.Enum, '根据文件名优化每集标题：✅ 开启', '', enum_values=lambda: state_list, default_value='on', multi_value=False, required=False),
                narrators: ArgSchema(ArgType.String, '演播者', '', default_value='', required=False),
                podcast_summary: ArgSchema(ArgType.String, '简介，用于生成播客简介', '', default_value='', required=False),
                year: ArgSchema(ArgType.String, '发布年份', '', default_value='', required=False),
                album: ArgSchema(ArgType.String, '专辑：留空自动按每100集划分', '', default_value='', required=False),
                art_album: ArgSchema(ArgType.String, '专辑艺术家：推荐填写书名', '', default_value='', required=False),
                subject: ArgSchema(ArgType.String, '题材，如：武侠，相声', '', default_value='', required=False),
                diy_cover_config: ArgSchema(ArgType.Enum, '修改封面：📴 关闭', '需要输入文件夹下有cover.jpg', enum_values=lambda: state_list, default_value='off', multi_value=False, required=False)):
    output_dir = process_path(output_dir)
    if '影音视界' in output_dir: output_dir = f"/Media{output_dir.split('影音视界')[1]}"
    use_filename = get_state(use_filename_config)
    diy_cover = get_state(diy_cover_config)
    logger.info(f"{plugins_name}任务\n开始整理系列文件夹\n输入路径：[{output_dir}]\n系列：['{series}']\n作者：['{authors}']\n演播者：['{narrators}']\n发布年份：['{year}']")
    if move_out_configs == 'move':
        move_out(output_dir)
    elif move_out_configs == 'add_and_move':
        move_to_dir(output_dir,authors,year,narrators,series,podcast_summary,album,art_album,move_out_configs,use_filename,subject)
        diy_abs(output_dir, series, authors, narrators, year)
    else:
        all_add_tag(output_dir,authors,year,narrators,series, podcast_summary, album,art_album,use_filename,subject,diy_cover)
    return PluginCommandResponse(True, f'整理系列文件夹任务完成')
