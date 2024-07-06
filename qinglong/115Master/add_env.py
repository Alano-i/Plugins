import os
from qinglong_api import QinglongApi

new_envs = [
    {
        'name': 'app_115',
        'value': '输入变量值',
        'remarks': '获取115 cookie的设备',
    },
    {
        'name': 'cookie_fire',
        'value': '输入变量值',
        'remarks': '115作为火种的cookie，用于自动获取新的cookie',
    },
    {
        'name': 'cookie_115',
        'value': '输入变量值',
        'remarks': '115 cookie',
    },
    {
        'name': 'touser',
        'value': '输入变量值',
        'remarks': '企业微信通知接收者',
    },
    {
        'name': 'corpid',
        'value': '输入变量值',
        'remarks': '企业 ID',
    },
    {
        'name': 'corpsecret',
        'value': '输入变量值',
        'remarks': '企业微信 corp secret',
    },
    {
        'name': 'agentid',
        'value': '输入变量值',
        'remarks': '企业微信应用 ID',
    },
    {
        'name': 'pic_url_115',
        'value': '输入变量值',
        'remarks': '115通知封面',
    },
    {
        'name': 'del_root_id',
        'value': '输入变量值',
        'remarks': '115文件夹id',
    },
    {
        'name': 'push_notify_115',
        'value': '输入变量值',
        'remarks': '115通知开关，on/off',
    },
    {
        'name': 'normal_notify_115',
        'value': '输入变量值',
        'remarks': '115无风控通知开关，on/off',
    },
    {
        'name': 'media_id_115',
        'value': '输入变量值',
        'remarks': '企业微信封面图 Media id',
    },
]

if __name__ == "__main__":
    QinglongApi().add_env(new_envs)