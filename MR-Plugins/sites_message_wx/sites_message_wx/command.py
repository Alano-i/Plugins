from mbot.core.plugins import plugin, PluginCommandContext, PluginCommandResponse
from mbot.openapi import mbot_api
from mbot.core.params import ArgSchema, ArgType
import logging
from .sites_message import main
_LOGGER = logging.getLogger(__name__)

@plugin.command(name='sites_message_wx', title='获取PT站内信和公告-微信通知', desc='点击执行站内信和公告获取并微信通知', icon='LocalPostOffice', run_in_background=True)
def sites_message_echo(ctx: PluginCommandContext):
    try:
        _LOGGER.info('开始获取站内信和公告')
        main()
        _LOGGER.info('站内信和公告获取完成')
        return PluginCommandResponse(True, f'站内信和公告获取成功')
    except Exception as e:
        _LOGGER.error(f'出错了,{e}')
        return PluginCommandResponse(False, f'站内信和公告获取失败，原因：{e}')
