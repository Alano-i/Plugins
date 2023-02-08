from mbot.core.plugins import plugin, PluginCommandContext, PluginCommandResponse
from mbot.openapi import mbot_api
from mbot.core.params import ArgSchema, ArgType
import logging
from .daily_news import main
_LOGGER = logging.getLogger(__name__)

@plugin.command(name='daily_news', title='每天60秒读懂世界', desc='获取每日新闻和天气并微信通知', icon='LocalPostOffice', run_in_background=True)
def daily_news_echo(ctx: PluginCommandContext):
    try:
        _LOGGER.info('「每天60秒读懂世界」开始获取每日新闻和天气')
        main()
        _LOGGER.info('「每天60秒读懂世界」获取每日新闻和天气完成,并已推送消息')
        return PluginCommandResponse(True, f'「每天60秒读懂世界」获取每日新闻和天气完成,并已推送消息')
    except Exception as e:
        _LOGGER.error(f'出错了,{e}')
        return PluginCommandResponse(False, f'「每天60秒读懂世界」获取每日新闻和天气失败，原因：{e}')
