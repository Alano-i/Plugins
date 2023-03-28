from mbot.core.plugins import plugin, PluginCommandContext, PluginCommandResponse,PluginMeta
from mbot.openapi import mbot_api
from mbot.core.params import ArgSchema, ArgType
from .qb_tools import add_tag_m
import logging

server = mbot_api
_LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
plugins_name = '「QB 工具箱」'

add_tag_config_list = [
    {
        "name": "开启",
        "value": True
    },
    {
        "name": "关闭",
        "value": False
    }
]

@plugin.command(name='add_tag_ma', title='QB种子添加标签', desc='为指定文件夹添加标签', icon='HourglassFull',run_in_background=True)
def add_tag_m_echo(ctx: PluginCommandContext,
                progress_path: ArgSchema(ArgType.String, '指定种子保存路径', '', default_value='', required=True),
                add_tag_m_name: ArgSchema(ArgType.String, '添加的标签名称', '', default_value='', required=True),
                add_tag_config: ArgSchema(ArgType.Enum, '是否启用，默认开启', '', enum_values=lambda: add_tag_config_list, default_value=True, multi_value=False, required=False)):
    
    _LOGGER.info(f'{plugins_name}开始手动添加标签')
    _LOGGER.info(f"{plugins_name}将为保存路径为 ['{progress_path}'] 的种子添加 ['{add_tag_m_name}'] 标签")
    add_tag_m(add_tag_config, progress_path, add_tag_m_name)
    _LOGGER.info(f'{plugins_name}手动添加标签任务完成')
