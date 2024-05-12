#!/usr/bin/env python3
# encoding: utf-8
from enum import Enum
from json import loads
from os import link
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from io import StringIO
import logging
# import httpx
logger = logging.getLogger(__name__)
plugins_name = '「115工具箱」'


from mbot.core.plugins import plugin
from mbot.core.plugins import PluginMeta
from mbot.openapi import mbot_api
from typing import Dict, Any

from .cookie_to_json import cookie2json
server = mbot_api

def config_setup(config):
    global message_to_uid,channel,pic_url,push_msg,cookie2cookie
    message_to_uid = config.get('uid','')
    channel = config.get('channel','qywx')
    pic_url = config.get('pic_url','')
    push_msg = config.get('push_msg',True)
    cookie2cookie = config.get('cookie2cookie','')
    logger.info(f'{plugins_name}已切换通知通道至「{channel}」')
    if not message_to_uid:
        logger.error(f'{plugins_name}获取推送用户失败, 可能是设置了没保存成功或者还未设置')

@plugin.after_setup
def after_setup(plugin_meta: PluginMeta, config: Dict[str, Any]):
    config_setup(config)

@plugin.config_changed
def config_changed(config: Dict[str, Any]):
    config_setup(config)


def push_msg_to_mbot(msg_title, msg_digest,link_url=''):
    msg_data = {
        'title': msg_title,
        'a': msg_digest,
        'pic_url': pic_url,
        'link_url': link_url,
    }
    try:
        if message_to_uid:
            for _ in message_to_uid:
                server.notify.send_message_by_tmpl('{{title}}', '{{a}}', msg_data, to_uid=_, to_channel_name = channel)
        else:
            server.notify.send_message_by_tmpl('{{title}}', '{{a}}', msg_data)
        logger.info(f'{plugins_name}已推送消息')
        return
    except Exception as e:
        logger.error(f'{plugins_name}推送消息异常, 原因: {e}')

AppEnum = Enum("AppEnum", "web, android, ios, linux, mac, windows, tv, alipaymini, wechatmini, qandroid")

def get_enum_name(val, cls):
    if isinstance(val, cls):
        return val.name
    try:
        if isinstance(val, str):
            return cls[val].name
    except KeyError:
        pass
    return cls(val).name


def get_qrcode_token():
    """获取登录二维码，扫码可用
    GET https://qrcodeapi.115.com/api/1.0/web/1.0/token/
    :return: dict
    """
    api = "https://qrcodeapi.115.com/api/1.0/web/1.0/token/"
    """
    try:
        # 使用 httpx 发起 GET 请求
        # verify=False 参数用于禁用 SSL 证书验证
        with httpx.Client(verify=True) as client:
            response = client.get(api)
        
        # 检查 HTTP 响应状态
        response.raise_for_status()
        
        # 返回 JSON 响应数据
        return response.json()
    except httpx.HTTPError as e:  # 捕获可能的 HTTP 异常
        print("Error fetching QR code token:", e)
        return None
    """
    return loads(urlopen(api).read())


def get_qrcode_status(payload):
    """获取二维码的状态（未扫描、已扫描、已登录、已取消、已过期等）
    GET https://qrcodeapi.115.com/get/status/
    :param payload: 请求的查询参数，取自 `login_qrcode_token` 接口响应，有 3 个
        - uid:  str
        - time: int
        - sign: str
    :return: dict
    """
    api = "https://qrcodeapi.115.com/get/status/?" + urlencode(payload)
    return loads(urlopen(api).read())


def post_qrcode_result(uid, app="web"):
    """获取扫码登录的结果，并且绑定设备，包含 cookie
    POST https://passportapi.115.com/app/1.0/{app}/1.0/login/qrcode/
    :param uid: 二维码的 uid，取自 `login_qrcode_token` 接口响应
    :param app: 扫码绑定的设备，可以是 int、str 或者 AppEnum
        app 目前发现的可用值：
            - 1,  "web",        AppEnum.web
            - 2,  "android",    AppEnum.android
            - 3,  "ios",        AppEnum.ios
            - 4,  "linux",      AppEnum.linux
            - 5,  "mac",        AppEnum.mac
            - 6,  "windows",    AppEnum.windows
            - 7,  "tv",         AppEnum.tv
            - 8,  "alipaymini", AppEnum.alipaymini
            - 9,  "wechatmini", AppEnum.wechatmini
            - 10, "qandroid",   AppEnum.qandroid
    :return: dict，包含 cookie
    """
    app = get_enum_name(app, AppEnum)
    payload = {"app": app, "account": uid}
    api = "https://passportapi.115.com/app/1.0/%s/1.0/login/qrcode/" % app
    return loads(urlopen(Request(api, data=urlencode(payload).encode("utf-8"), method="POST")).read())


def get_qrcode(uid):
    """获取二维码图片（注意不是链接）
    :return: 一个文件对象，可以读取
    """
    # 二维码图片链接
    url = "https://qrcodeapi.115.com/api/1.0/mac/1.0/qrcode?uid=%s" % uid
    return url
    # return urlopen(url)


def login_with_qrcode(app="web", scan_in_console=True,app_name='web'):
    """用二维码登录
    :param app: 扫码绑定的设备，可以是 int、str 或者 AppEnum
        app 目前发现的可用值：
            - 1,  "web",        AppEnum.web
            - 2,  "android",    AppEnum.android
            - 3,  "ios",        AppEnum.ios
            - 4,  "linux",      AppEnum.linux
            - 5,  "mac",        AppEnum.mac
            - 6,  "windows",    AppEnum.windows
            - 7,  "tv",         AppEnum.tv
            - 8,  "alipaymini", AppEnum.alipaymini
            - 9,  "wechatmini", AppEnum.wechatmini
            - 10, "qandroid",   AppEnum.qandroid
    :return: dict，扫码登录结果
    """
    qrcode_token = get_qrcode_token()["data"]
    qrcode = qrcode_token.pop("qrcode")
    if scan_in_console:
        try:
            from qrcode import QRCode
        except ModuleNotFoundError:
            from sys import executable
            from subprocess import run
            run([executable, "-m", "pip", "install", "qrcode"], check=True)
            from qrcode import QRCode # type: ignore
        # qr = QRCode(border=1)
        # qr.add_data(qrcode)
        # qr.print_ascii(tty=True)

        qr = QRCode(border=1)
        qr.add_data(qrcode)
        
        # 创建一个 StringIO 对象来捕获 QRCode 的输出
        qr_string_io = StringIO()
        # 将 tty 参数设置为 False，然后将输出重定向到 StringIO 对象
        qr.print_ascii(out=qr_string_io, tty=False)
        # 获取 QRCode 的字符串表示
        qr_string = qr_string_io.getvalue()
        # 关闭 StringIO 对象
        qr_string_io.close()
        # 使用 logging.info 打印 QRCode 字符串到日志
        logger.info("请使用115客户端扫描下方二维码:\n" + qr_string)
        logger.info("需要F12在控制台输入下面的代码才能正常扫描\n['document.querySelectorAll(\'code\').forEach(function(element) {element.style.setProperty(\'line-height\', \'1\', \'important\');});']")

    else:
        qrcode_image_url = get_qrcode(qrcode_token["uid"])
        # print(f"请打开下方的链接，使用115客户端扫描二维码：{qrcode_image_url}")
        logger.info(f"{plugins_name}请打开下方的链接，使用115客户端扫描二维码：{qrcode_image_url}")
        if push_msg:
            if qrcode_image_url:
                msg_title=f'{app_name}请求登录'
                msg_digest=f'点击查看二维码'
                push_msg_to_mbot(msg_title, msg_digest,qrcode_image_url)
    while True:
        try:
            resp = get_qrcode_status(qrcode_token)
        except TimeoutError:
            continue
        status = resp["data"].get("status")
        if status == 0:
            logger.info(f"{plugins_name}扫描二维码：等待中...")
        elif status == 1:
            logger.info(f"{plugins_name}扫描二维码：已扫描")
        elif status == 2:
            logger.info(f"{plugins_name}扫描二维码：已登录")
            break
        elif status == -1:
            raise OSError(f"{plugins_name}扫描二维码：已过期")
        elif status == -2:
            raise OSError(f"{plugins_name}扫描二维码：已取消")
        else:
            raise OSError(f"{plugins_name}扫描二维码出错：{resp}")

    return post_qrcode_result(qrcode_token["uid"], app)

def get_cookie(app,scan_in_console=False,app_name='web',EditThisCookie=False):
    resp = login_with_qrcode(app, scan_in_console,app_name)
    cookie=("; ".join(f"{key}={value}" for key, value in resp['data']['cookie'].items()))
    # logger.info(f"{plugins_name}获取到的cookie如下：\nUID={resp['data']['cookie']['UID']}; CID={resp['data']['cookie']['CID']}; SEID={resp['data']['cookie']['SEID']}")
    if EditThisCookie:
        logger.info(f"{plugins_name}获取到的cookie如下,已转换为 EditThisCookie 格式：\n{cookie2json(cookie)}")
    else:
        logger.info(f"{plugins_name}获取到的cookie如下：\n{cookie}")
    if push_msg:
        msg_title=f'{app_name}的cookie'
        msg_digest=f'{cookie}'
        push_msg_to_mbot(msg_title, msg_digest)
