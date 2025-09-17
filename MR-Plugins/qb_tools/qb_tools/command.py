from mbot.core.plugins import plugin, PluginCommandContext, PluginCommandResponse,PluginMeta
from mbot.openapi import mbot_api
from mbot.core.params import ArgSchema, ArgType
from .qb_tools import add_tag_m,edit_tracker_m, delete_task_m
import logging

server = mbot_api
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
plugins_name = '「QB 工具箱」'

add_tag_config_list = [
    {
        "name": "✅ 开启",
        "value": 'on'
    },
    {
        "name": "📴 关闭",
        "value": 'off'
    }
]

@plugin.command(name='add_tag_ma', title='QB种子添加标签', desc='为指定文件夹添加标签', icon='Style',run_in_background=True)
def add_tag_m_echo(ctx: PluginCommandContext,
                progress_path: ArgSchema(ArgType.String, '为以下保存路径的种子添加标签', '', default_value='', required=True),
                add_tag_m_name: ArgSchema(ArgType.String, '添加的标签名称', '', default_value='', required=True),
                add_tag_config: ArgSchema(ArgType.Enum, '是否启用，默认开启', '', enum_values=lambda: add_tag_config_list, default_value='on', multi_value=False, required=False)):
    add_tag_config = bool(add_tag_config and add_tag_config.lower() != 'off')
    
    logger.info(f'{plugins_name}开始手动添加标签')
    logger.info(f"{plugins_name}将为保存路径为 ['{progress_path}'] 的种子添加 ['{add_tag_m_name}'] 标签")
    add_tag_m(add_tag_config, progress_path, add_tag_m_name)
    logger.info(f'{plugins_name}手动添加标签任务完成')
    return PluginCommandResponse(True, f'手动添加标签任务完成')

@plugin.command(name='edit_tracker', title='修改tracker', desc='QB种子修改tracker', icon='PublishedWithChanges',run_in_background=True)
def edit_tracker_echo(ctx: PluginCommandContext,
                old_tracker: ArgSchema(ArgType.String, '将原 tracker 中的关键字', '', default_value='', required=True),
                new_tracker: ArgSchema(ArgType.String, '替换为', '', default_value='', required=True),
                edit_tracker_config: ArgSchema(ArgType.Enum, '启用修改tracker，默认开启', '', enum_values=lambda: add_tag_config_list, default_value='on', multi_value=False, required=False)):
    edit_tracker = bool(edit_tracker_config and edit_tracker_config.lower() != 'off')
    if edit_tracker:
        logger.info(f"{plugins_name}将 tracker 中的关键字['{old_tracker}'] 替换为 ['{new_tracker}'] ")
        edit_tracker_m(old_tracker, new_tracker, edit_tracker)
        logger.info(f'{plugins_name}手动修改tracker任务完成')
    else:
        logger.info(f'{plugins_name}未启用修改tracker，任务停止')
    return PluginCommandResponse(True, f'手动修改tracker任务完成')

@plugin.command(name='del_ta', title='手动删种', desc='删种，本地文件，硬链接文件', icon='PublishedWithChanges',run_in_background=True)
def del_ta_echo(ctx: PluginCommandContext,
                save_path: ArgSchema(ArgType.String, '删除指定下载文件夹的种子，一行一个，末尾带/', '/Media/downloads/', default_value='', required=True),
                delete_local_config: ArgSchema(ArgType.Enum, '🗂️ 删除本地文件，默认关闭', '', enum_values=lambda: add_tag_config_list, default_value='off', multi_value=False, required=False),
                delete_hard_config: ArgSchema(ArgType.Enum, '🔗 删除硬链接，默认关闭', '', enum_values=lambda: add_tag_config_list, default_value='off', multi_value=False, required=False),
                hardlink_paths: ArgSchema(ArgType.String, '下载文件夹对应的硬链接目录，末尾不带/，一行一个', '/Media/短剧', default_value='', required=True),
                del_day: ArgSchema(ArgType.String, '删除多少天之前的种子，默认7天', '', default_value='7', required=True)):
    delete_hard = bool(delete_hard_config and delete_hard_config.lower() != 'off')
    delete_local = bool(delete_local_config and delete_local_config.lower() != 'off')
    save_path=save_path.splitlines()
    hardlink_paths=hardlink_paths.splitlines()
    try:
        del_day = int(del_day)
    except ValueError:
        del_day = 7

    delete_task_m(save_path,delete_local,delete_hard,hardlink_paths,del_day)

    return PluginCommandResponse(True, f'手动运行删种任务完成')