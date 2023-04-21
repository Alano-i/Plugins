from mbot.core.plugins import plugin, PluginCommandContext, PluginCommandResponse
from mbot.openapi import mbot_api
from mbot.core.params import ArgSchema, ArgType
import logging

from .sites_message import sites_message_by_manual, site_announcement

_LOGGER = logging.getLogger(__name__)


@plugin.command(name='sites_message', title='站内信获取', desc='点击执行站内信获取并通知', icon='LocalPostOffice', run_in_background=True)
def sites_message_echo(ctx: PluginCommandContext):
    try:
        _LOGGER.info('开始获取站内信')
        sites_message_by_manual()
        _LOGGER.info('站内信获取完成')
        return PluginCommandResponse(True, f'站内信获取成功')
    except Exception as e:
        _LOGGER.error(f'出错了,{e}')
        return PluginCommandResponse(False, f'站内信获取失败，原因：{e}')


@plugin.command(name='site_announcement', title='站点公告获取', desc='点击执行站点公告获取并通知', icon='LocalPostOffice', run_in_background=True)
def site_announcement_echo(ctx: PluginCommandContext):
    try:
        _LOGGER.info('开始获取站点公告')
        site_announcement()
        _LOGGER.info('站点公告获取完成')
        return PluginCommandResponse(True, f'站点公告获取成功')
    except Exception as e:
        _LOGGER.error(f'出错了,{e}')
        return PluginCommandResponse(False, f'站点公告获取失败,{e}')
