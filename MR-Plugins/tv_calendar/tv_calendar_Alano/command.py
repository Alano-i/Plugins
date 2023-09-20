from mbot.core.plugins import plugin, PluginCommandContext, PluginCommandResponse
from mbot.openapi import mbot_api
import logging

from .tv_calendar import save_json, update_json
server = mbot_api
loger = logging.getLogger(__name__)
@plugin.command(name='echo', title='更新追剧日历数据', desc='订阅剧集越多，执行时间越长，请耐心等待', icon='MovieFilter', run_in_background=True)
def echo(ctx: PluginCommandContext):
    """
    异步执行,更新追剧日历数据
    """
    try:
        save_json()
    except Exception as e:
        loger.error(e)
        return PluginCommandResponse(False, f'创建追剧日历数据源失败')
    return PluginCommandResponse(True, f'创建追剧日历数据源成功')

@plugin.command(name='update_json', title='更新本地媒体库到追剧日历', desc='同步本地媒体库剧集详情到追剧日历', icon='MovieFilter', run_in_background=True)
def update_json_echo(ctx: PluginCommandContext):
    """
    异步执行,更新追剧日历数据
    """
    # loger.info(f'「追剧日历」开始同步本地媒体库数据到追剧日历')
    try:
        update_json()
    except Exception as e:
        loger.error(f'「追剧日历」同步本地媒体库数据到追剧日历失败，原因：{e}')
        return PluginCommandResponse(False, f'同步本地媒体库数据到追剧日历失败')
    return PluginCommandResponse(True, f'同步本地媒体库数据到追剧日历成功')
