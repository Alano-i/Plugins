from mbot.core.plugins import plugin, PluginCommandContext, PluginCommandResponse,PluginMeta
from mbot.openapi import mbot_api
from mbot.core.params import ArgSchema, ArgType
from .audio_tools import audio_clip, move_to_dir, diy_abs, move_out,all_add_tag
import logging
server = mbot_api
_LOGGER = logging.getLogger(__name__)
plugins_name = '「有声书工具箱」'
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

use_filename_config_list = [
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
    last_time_input_dirs = '/Media/音乐/有声书/xx2587456'

@plugin.command(name='audio_clip_m', title='音频剪辑', desc='剪辑片头片尾，修改整理元数据', icon='LibraryMusic',run_in_background=True)
def audio_clip_m_echo(ctx: PluginCommandContext,
                input_dirs: ArgSchema(ArgType.String, last_time_input_dirs, '输入路径,末尾不带/，支持多条，一行一条/Media/音乐/有声书/', default_value = last_time_input_dirs, required=False),
                output_dir: ArgSchema(ArgType.String, '输出路径', '', default_value=None, required=False),
                cliped_folder: ArgSchema(ArgType.String, '已剪辑存放路径，默认：已剪辑', '', default_value='已剪辑', required=False),
                audio_start: ArgSchema(ArgType.String, '剪辑开始时间', '默认：00:00:00', default_value='00:00:00', required=False),
                audio_end: ArgSchema(ArgType.String, '剪辑结束倒数秒数', '默认：0，单位：秒', default_value='0', required=False),
                clip_configs: ArgSchema(ArgType.Enum, '选择运行的操作，默认：剪辑、整理、添加元数据', '若仅剪辑，下方参数不生效。', enum_values=lambda: clip_config, default_value='clip_and_move', multi_value=False, required=False),
                use_filename_config: ArgSchema(ArgType.Enum, '文件名作为标题，默认开启', '', enum_values=lambda: use_filename_config_list, default_value='on', multi_value=False, required=False),
                authors: ArgSchema(ArgType.String, '作者：推荐填写原著作家', '', default_value=None, required=False),
                narrators: ArgSchema(ArgType.String, '演播者，多个示例：演播A,,演播B,,', '', default_value=None, required=False),
                series: ArgSchema(ArgType.String, '系列：推荐填写书名', '', default_value=None, required=False),
                year: ArgSchema(ArgType.String, '发布年份', '', default_value=None, required=False),
                albums: ArgSchema(ArgType.String, '专辑：留空则自动按每100集划分', '', default_value=None, required=False),
                art_album: ArgSchema(ArgType.String, '专辑艺术家：推荐填写书名', '', default_value=None, required=False),
                subject: ArgSchema(ArgType.String, '题材，例如：武侠，相声', '', default_value=None, required=False)):
    output_dir = output_dir or input_dirs
    use_filename = bool(use_filename_config and use_filename_config.lower() != 'off')
    _LOGGER.info(f"{plugins_name}任务\n开始运行音频剪辑\n输入路径：[{input_dirs}]\n输出路径：[{output_dir}/{cliped_folder}]\n开始时间：[{audio_start}]\n结束倒数秒数：[{audio_end}]\n\n整理参数如下：\n系列：['{series}']\n作者：['{authors}']\n演播者：['{narrators}']\n发布年份：['{year}']\n专辑：['{albums}']\n专辑艺术家：['{art_album}']")
    
    server.common.set_cache('audio_clip', 'input_dirs', input_dirs)
    
    
    input_dirs_s = input_dirs.split('\n')
    if albums:
        albums_s = albums.split('\n')
    album = None
    for i, input_dir in enumerate(input_dirs_s):
        if albums:
            album = albums_s[i]
        output_dir = output_dir or input_dir
        audio_clip(input_dir,output_dir,cliped_folder,audio_start,audio_end,clip_configs,authors,year,narrators,series,album,art_album,use_filename,subject)
    return PluginCommandResponse(True, f'音频剪辑任务完成')

@plugin.command(name='diy_abs', title='修改metadata.abs', desc='修改 Audiobookshelf 元数据', icon='SwitchAccessShortcutAdd',run_in_background=True)
def diy_abs_echo(ctx: PluginCommandContext,
                folder_path: ArgSchema(ArgType.String, '输入路径', '/Media/音乐/有声书/', default_value='/Media/音乐/有声书/', required=True),
                series: ArgSchema(ArgType.String, '系列：推荐填写书名', '', default_value=None, required=False),
                authors: ArgSchema(ArgType.String, '作者：推荐填写原著作家', '', default_value=None, required=False),
                narrators: ArgSchema(ArgType.String, '演播者，多个示例：演播A,,演播B,,', '', default_value=None, required=False),
                year: ArgSchema(ArgType.String, '发布年份', '', default_value=None, required=False)):

    _LOGGER.info(f"{plugins_name}任务\n开始运行 DIY 音频元数据\n输入路径：[{folder_path}]\n系列：['{series}']\n作者：['{authors}']\n演播者：['{narrators}']\n发布年份：['{year}']")
    diy_abs(folder_path, series, authors, narrators, year)
    return PluginCommandResponse(True, f'DIY 音频元数据任务完成')

@plugin.command(name='move_to_dir', title='整理有声书', desc='分配到子文件夹 1-100 101-200 201-300, 并添加元数据', icon='RuleFolder',run_in_background=True)
def move_to_dir_echo(ctx: PluginCommandContext,
                move_out_configs: ArgSchema(ArgType.Enum, '选择运行的操作，默认：运行整理并添加元数据', '', enum_values=lambda: move_out_config, default_value='add_and_move', multi_value=False, required=False),
                output_dir: ArgSchema(ArgType.String, '输入路径', '/Media/音乐/有声书/', default_value=None, required=True),
                authors: ArgSchema(ArgType.String, '作者：推荐填写原著作家', '', default_value=None, required=False),
                use_filename_config: ArgSchema(ArgType.Enum, '文件名作为标题，默认开启', '', enum_values=lambda: use_filename_config_list, default_value='on', multi_value=False, required=False),
                narrators: ArgSchema(ArgType.String, '演播者，多个示例：演播A,,演播B,,', '', default_value=None, required=False),
                series: ArgSchema(ArgType.String, '系列：推荐填写书名', '', default_value=None, required=False),
                year: ArgSchema(ArgType.String, '发布年份', '', default_value=None, required=False),
                album: ArgSchema(ArgType.String, '专辑：留空则自动按每100集划分', '', default_value=None, required=False),
                art_album: ArgSchema(ArgType.String, '专辑艺术家：推荐填写书名', '', default_value=None, required=False),
                subject: ArgSchema(ArgType.String, '题材，例如：武侠，相声', '', default_value=None, required=False)):
    use_filename = bool(use_filename_config and use_filename_config.lower() != 'off')
    _LOGGER.info(f"{plugins_name}任务\n开始整理系列文件夹\n输入路径：[{output_dir}]\n系列：['{series}']\n作者：['{authors}']\n演播者：['{narrators}']\n发布年份：['{year}']")
    if move_out_configs == 'move':
        move_out(output_dir)
    elif move_out_configs == 'add_and_move':
        move_to_dir(output_dir,authors,year,narrators,series,album,art_album,move_out_configs,use_filename,subject)
        diy_abs(output_dir, series, authors, narrators, year)
    else:
        all_add_tag(output_dir,authors,year,narrators,series,album,art_album,use_filename,subject)
    return PluginCommandResponse(True, f'整理系列文件夹任务完成')
