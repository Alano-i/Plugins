from mbot.core.plugins import plugin, PluginCommandContext, PluginCommandResponse
from mbot.openapi import mbot_api
from mbot.core.params import ArgSchema, ArgType
import logging

from .sites_message import main
_LOGGER = logging.getLogger(__name__)


@plugin.command(name='echo', title='PT站内信获取', desc='点击执行站内信获取并通知', icon='LocalPostOffice', run_in_background=True)
def echo(ctx: PluginCommandContext):
    _LOGGER.info('开始获取站内信')
    main()
    _LOGGER.info('站内信获取完成')
    return PluginCommandResponse(True, f'站内信获取成功')

