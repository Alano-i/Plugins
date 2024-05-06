from mbot.core.plugins import plugin, PluginCommandContext, PluginCommandResponse,PluginMeta
from mbot.openapi import mbot_api
from mbot.core.params import ArgSchema, ArgType
import logging
from .get_115_cookie import get_cookie
server = mbot_api
loger = logging.getLogger(__name__)
plugins_name = '「115工具箱」'

app_config = [
    {
        "name": "115 网页版",
        "value": 'web'
    },
    {
        "name": "115生活（安卓端)",
        "value": 'android'
    },
    {
        "name": "115生活（iOS 端)",
        "value": 'ios'
    },
    {
        "name": "115生活（Linux 端)",
        "value": 'linux'
    },
    {
        "name": "115生活（Mac 端）",
        "value": 'mac'
    },
    {
        "name": "115 Windows 端",
        "value": 'windows'
    },
    {
        "name": "115网盘（安卓电视端）",
        "value": 'tv'
    },
    {
        "name": "115生活（支付宝小程序）",
        "value": 'alipaymini'
    },
    {
        "name": "115生活（微信小程序）",
        "value": 'wechatmini'
    },
    {
        "name": "115管理（安卓端）",
        "value": 'qandroid'
    }
]

@plugin.command(name='get_115_ck', title='获取 115 cookie', desc='获取不同设备的 cookie', icon='Cookie',run_in_background=True)
def audio_clip_m_echo(ctx: PluginCommandContext,
                app: ArgSchema(ArgType.Enum, '选择获取 cookie 的设备', '', enum_values=lambda: app_config, default_value='web', multi_value=False, required=True),
                ):
    # 从 app_config 中找到匹配 app 值的配置
    app_name = next((config['name'] for config in app_config if config['value'] == app), None)
    loger.info(f"{plugins_name}开始获取['{app_name}']的 cookie")            
    get_cookie(app,False,app_name)
    loger.info(f"{plugins_name}获取['{app_name}']的 cookie 完成")
    return PluginCommandResponse(True, f'获取cookie完成')
    

