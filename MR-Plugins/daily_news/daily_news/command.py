from mbot.core.plugins import plugin, PluginCommandContext, PluginCommandResponse
from mbot.openapi import mbot_api
from mbot.core.params import ArgSchema, ArgType
import logging
from .daily_news import main
server = mbot_api
_LOGGER = logging.getLogger(__name__)

@plugin.command(name='daily_news', title='每天60秒读懂世界', desc='获取每日新闻和天气并微信通知', icon='LocalPostOffice', run_in_background=True)
def daily_news_echo(ctx: PluginCommandContext):
    try:
        _LOGGER.info('「每天60秒读懂世界」手动运行，开始获取每日新闻和天气')
        server.common.set_cache('is_get_news', 'daily_news', False)
        server.common.set_cache('is_get_news', 'entertainment', False)
        server.common.set_cache('is_get_news', 'hour', 8)
        # server.common.set_cache('is_get_news', 'entertainment', True)
        # server.common.set_cache('is_get_news', 'hour', '')
        if main():
            _LOGGER.info('「每天60秒读懂世界」手动运行，获取每日新闻和天气完成！')
        return PluginCommandResponse(True, f'「每天60秒读懂世界」手动运行，执行完成')
    except Exception as e:
        _LOGGER.error(f'出错了,{e}')
        return PluginCommandResponse(False, f'「每天60秒读懂世界」手动运行，执行失败，原因：{e}')
