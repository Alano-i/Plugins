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
        # xx=server.common.get_cache('notify', 'alerts')
        # _LOGGER.info(f'{xx}')
        # xx=[{
        #     'alert_time': '2023-03-17 11:47:08',
        #     'alert_level': 'CRITICAL',
        #     'alert_type': 'UPSCommbad',
        #     'alert_text': "Communication with UPS ups lost.<br><br>UPS Statistics: 'ups'<br><br>Statistics could not be recovered<br>"
        # }, {
        #     'alert_time': '2023-03-15 18:56:24',
        #     'alert_level': 'WARNING',
        #     'alert_type': 'NTPHealthCheck',
        #     'alert_text': "NTP health check failed - No Active NTP peers: [{'203.107.6.88': 'REJECT'}, {'120.25.115.20': 'REJECT'}, {'202.118.1.81': 'REJECT'}]"
        # }, {
        #     'alert_time': '2023-03-13 03:49:08',
        #     'alert_level': 'INFO',
        #     'alert_type': 'ScrubFinished',
        #     'alert_text': "Scrub of pool 'boot-pool' finished."
        # }, {
        #     'alert_time': '2023-03-08 15:18:10',
        #     'alert_level': 'NOTICE',
        #     'alert_type': 'ZpoolCapacityNotice',
        #     'alert_text': 'Space usage for pool "Pool" is 73%. Optimal pool performance requires used space remain below 80%.'
        # }, {
        #     'alert_time': '2023-02-19 09:37:10',
        #     'alert_level': 'CRITICAL',
        #     'alert_type': 'SMART',
        #     'alert_text': 'Device: /dev/sdh [SAT], ATA error count increased from 0 to 1.'
        # }, {
        #     'alert_time': '2022-08-23 00:02:53',
        #     'alert_level': 'CRITICAL',
        #     'alert_type': 'SMART',
        #     'alert_text': 'Device: /dev/sdg [SAT], 2 Currently unreadable (pending) sectors.'
        # }]
        # server.common.set_cache('notify', 'alerts', xx)
        _LOGGER.info('「TrueNas Scale 系统通知」手动运行，开始获取TrueNas Scale 系统通知')
        if not get_truenas_alert():
            _LOGGER.info('「TrueNas Scale 系统通知」手动运行没有获取到新通知')
        else:
            _LOGGER.info('「TrueNas Scale 系统通知」手动运行获取到新通知，并已推送')
        return PluginCommandResponse(True, f'「TrueNas Scale 系统通知」手动运行，执行完成')
    except Exception as e:
        _LOGGER.error(f'出错了,{e}')
        return PluginCommandResponse(False, f'「TrueNas Scale 系统通知」手动运行，执行失败，原因：{e}')
