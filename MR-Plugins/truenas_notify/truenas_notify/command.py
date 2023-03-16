from mbot.core.plugins import plugin, PluginCommandContext, PluginCommandResponse
from mbot.openapi import mbot_api
from mbot.core.params import ArgSchema, ArgType
import logging
from .truenas_notify import get_truenas_alert
server = mbot_api
_LOGGER = logging.getLogger(__name__)

@plugin.command(name='truenas_notify', title='TrueNas 系统通知', desc='获取TrueNas Scale 系统通知', icon='LocalPostOffice', run_in_background=True)
def daily_news_echo(ctx: PluginCommandContext):
    try:
        _LOGGER.info('「TrueNas Scale 系统通知」手动运行，开始获取TrueNas Scale 系统通知')
        if not get_truenas_alert():
            _LOGGER.info('「TrueNas Scale 系统通知」手动运行没有获取到新通知')
        else:
            _LOGGER.info('「TrueNas Scale 系统通知」手动运行获取到新通知，并已推送')
        return PluginCommandResponse(True, f'「TrueNas Scale 系统通知」手动运行，执行完成')
    except Exception as e:
        _LOGGER.error(f'出错了,{e}')
        return PluginCommandResponse(False, f'「TrueNas Scale 系统通知」手动运行，执行失败，原因：{e}')
