#!/usr/bin/env python3
from notifyhub.controller.schedule import register_cron_job
from notifyhub.plugins.common import after_setup
from notifyhub.controller.server import server
from notifyhub.plugins.utils import (
    get_plugin_data,
    get_plugin_config,
)

from bs4 import BeautifulSoup, SoupStrainer
from PIL import Image, ImageDraw, ImageFont
import time
import json
from fastapi.responses import FileResponse
from fastapi import APIRouter
import re
import jwt
import os
import requests
import logging
from zhdate import ZhDate
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from datetime import datetime, timezone
logger = logging.getLogger(__name__)

plugin_name = '「每天60秒读懂世界」'
plugin_id = "daily_news"
plugin_path = '/data/plugins/daily_news'
session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('https://', adapter)


# 获取原始存储数据（含名称等元信息）
data = get_plugin_data(plugin_id)  # 存在时返回字典，不存在返回 None
# 获取配置字典
config = get_plugin_config(plugin_id)  # 返回 dict，不存在时返回空字典 {}
# logger.info(f"{plugin_name}原始存储数据（含名称等元信息）: {data}")
# logger.info(f"{plugin_name}配置字典: {config}")
city = f"{config.get('city', '北京')}"
news_type = config.get('news_type')
private_key = config.get('private_key', '')
kid = config.get('kid', '')
sub = config.get('sub', '')
api_host = config.get('api_host', '')
notify_switch = config.get('notify_switch', True)
bind_channel = config.get('bind_channel')
PUSH_LINK_URL = config.get('push_link_url', '')
PUSH_IMG_URL = config.get('push_img_url', '')


# 热点新闻
def get_daily_news():
    exit_falg = False
    wecom_title = '🌏 每天60秒读懂世界'
    url="https://api.03c3.cn/api/zb"
    response = requests.get(url)
    logger.info(f'{plugin_name}请求每日新闻源：{url}')
    if response.status_code == 200:
        back_day_str = response.headers['Date']
        # 解析为 datetime（UTC）
        back_day = datetime.strptime(back_day_str, "%a, %d %b %Y %H:%M:%S %Z")
        # 获取今天的 UTC 日期（只保留年月日）
        today = datetime.now(timezone.utc).date()
        image_url = url
        # 格式化日期，只保留年月日
        updated_date = back_day.date()
        # logger.error(f"运行前获取标识：{server.get_cache('is_get_news', 'daily_news')}")

        if updated_date < today:
            logger.error(f'{plugin_name}今天的每日新闻还未更新，一小时后会再次重试！')
            server.set_cache('is_get_news', 'daily_news', False)
            exit_falg = True
            return '', '', '', '', exit_falg
        elif server.get_cache('is_get_news', 'daily_news'):
            logger.info(f'{plugin_name}今天的每日新闻源已经更新，但今天已经获取过了，将在明天 8:00 再次获取！')
            exit_falg = True
            return '', '', '', '', exit_falg
        else:
            news_url = image_url

            news_content = f'<img src="{news_url}" style="border-radius: 12px;" alt="每天60秒读懂世界" width="100%">'
            server.set_cache('is_get_news', 'daily_news', True)
            # news_content = f'<div style="border-radius: 12px; overflow: hidden;"><img src="{img_url}" alt="封面"></div>{news_content}'
    else:
        news_content = '获取热点新闻内容失败，请检查网络！'
        news_digest = '获取热点新闻内容失败，请检查网络！'
        news_url = url
        logger.error('热点新闻获取失败，请检查网络！')
    news_digest = '点击了解世界'
    # logger.error(f"运行后获取标识：{server.get_cache('is_get_news', 'daily_news')}")
    return wecom_title, news_digest, news_content, news_url, exit_falg
# 热点新闻
def get_daily_news_old():
    exit_falg = False
    wecom_title = '🌏 每天60秒读懂世界'
    url = "https://api.jun.la/60s.php?format=imgapi"
    headers = {
        "Content-Type": "text/html;charset=utf-8",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Headers": "x-requested-with, content-type"
    }
    res = session.request("GET", url, headers=headers, timeout=30)
    if res.status_code == 200:
        logger.info(f'{plugin_name}请求每日新闻源：{res.text}')
        image_url = json.loads(res.text)["imageBaidu"]
        image_time = json.loads(res.text)["imageTime"]
        # 格式化日期，只保留年月日
        updated_date = image_time
        # 获取今天的日期
        today = datetime.today().strftime("%Y-%m-%d")
        # logger.error(f"运行前获取标识：{server.get_cache('is_get_news', 'daily_news')}")

        if updated_date < today:
            logger.error(f'{plugin_name}今天的每日新闻还未更新，一小时后会再次重试！')
            server.set_cache('is_get_news', 'daily_news', False)
            exit_falg = True
            return '', '', '', '', exit_falg
        elif server.get_cache('is_get_news', 'daily_news'):
            logger.info(f'{plugin_name}今天的每日新闻源已经更新，但今天已经获取过了，将在明天 8:00 再次获取！')
            exit_falg = True
            return '', '', '', '', exit_falg
        else:
            news_url = image_url

            news_content = f'<img src="{news_url}" style="border-radius: 12px;" alt="每天60秒读懂世界" width="100%">'
            server.set_cache('is_get_news', 'daily_news', True)
            # news_content = f'<div style="border-radius: 12px; overflow: hidden;"><img src="{img_url}" alt="封面"></div>{news_content}'
    else:
        news_content = '获取热点新闻内容失败，请检查网络！'
        news_digest = '获取热点新闻内容失败，请检查网络！'
        news_url = 'https://api.jun.la/60s.php?format=imgapi'
        logger.error('热点新闻获取失败，请检查网络！')
    news_digest = '点击了解世界'
    # logger.error(f"运行后获取标识：{server.get_cache('is_get_news', 'daily_news')}")
    return wecom_title, news_digest, news_content, news_url, exit_falg

# 影视快讯
def get_entertainment_news(pic_url):
    wecom_title = '🔥 热点影视快讯'
    news_urls = [
        "https://ent.sina.cn/film",
        "https://ent.sina.cn/tv"
    ]
    news_url = news_urls[1]
    news_content = ""
    for url in news_urls:
        # 获取网页源代码
        res = session.request("GET", url, timeout=30)
        res.encoding = "utf-8"
        html = res.text

        # # 使用pyquery解析网页源代码
        # doc = pq(html)
        # h_tags = doc('h2, h3')

        # 使用BeautifulSoup解析网页源代码
        soup = BeautifulSoup(html, 'html.parser')
        h_tags = soup.find_all(["h2", "h3"])

        result = []
        for h_tag in h_tags:
            if h_tag.text not in result:
                result.append(h_tag.text)
        content = '\n\n'.join(f'{i}、{h_tag}' for i, h_tag in enumerate(result[:11]))
        news_content += f'{content}\n\n'
    if news_content:
        news_content = news_content.replace('0、\n娱乐 \n电视前沿 \n\n', '📺 电视前沿\n')
        news_content = news_content.replace('0、\n娱乐 \n电影宝库 \n\n', '🎬 电影快讯\n')
        wecom_digest = news_content
        news_content = re.sub('\n+', '\n', news_content)
        wecom_content = news_content.replace('\n', '<br>')
        wecom_content = wecom_content.replace('🎬 电影快讯', '<big><big><b>🎬 电影快讯</b></big></big><small>')
        wecom_content = wecom_content.replace('📺 电视前沿', '</small>📺 电视前沿')
        wecom_content = wecom_content.replace('📺 电视前沿', '<br><big><big><b>📺 电视前沿</b></big></big><small>')
        wecom_content = f'<div style="border-radius: 12px; overflow: hidden;"><img src="{pic_url}" alt="封面"></div>{wecom_content}'
        server.set_cache('is_get_news', 'entertainment', True)
        server.set_cache('is_get_news', 'hour', '')
        return wecom_title, wecom_digest, wecom_content, news_url

    else:
        return wecom_title, '影视快讯', '影视快讯', news_url


def get_token():
    payload = {
        'iat': int(time.time()) - 30,
        'exp': int(time.time()) + 900,
        'sub': sub
    }
    headers = {
        'kid': kid
    }

    encoded_jwt = jwt.encode(payload, private_key,algorithm='EdDSA', headers=headers)
    # logger.info(f'和风token:{encoded_jwt}')
    return encoded_jwt


def get_weather():
    city_url = f"{api_host}/geo/v2/city/lookup"
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "location": city
    }

    r = requests.get(city_url, headers=headers, params=params)
    city_data = r.json()

    daily_weather_iconDay = '100'
    if city_data['code'] == '200':

        city_data = city_data['location'][0]
        city_id = city_data['id']
        city_name = city_data["name"]

        weather_url = f"{api_host}/v7/weather/3d"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        params = {
            "location": city_id
        }

        response = requests.get(weather_url, headers=headers, params=params)

        weather_data = response.json()
        if weather_data['code'] == '200':
            daily_weather_data = weather_data["daily"][0]
            daily_weather_iconDay = daily_weather_data["iconDay"]

            daily_weather_desc = daily_weather_data["textDay"]
            daily_weather_tempMin = daily_weather_data["tempMin"]
            daily_weather_tempMax = daily_weather_data["tempMax"]
            cond = f'{daily_weather_desc}  {daily_weather_tempMin}°~{daily_weather_tempMax}°'
        else:
            cond = '风雨难测°'
            logger.error(f'{plugin_name}获取天气信息失败')
    else:
        city_name = '你在天涯海角'
        cond = '风雨难测°'
        logger.error(
            f'{plugin_name}获取城市名失败,请确定 ➊【城市名称】是否设置正确，示例：北京。➋【和风天气】的 key 设置正确')
        logger.error(
            f'{plugin_name}【和风天气】的 KEY 在 https://dev.qweather.com 申请，创建项目后进入控制台新建项目然后添加 KEY')
        logger.error(
            f'{plugin_name}在项目管理找到新建的项目，KEY 下面有个查看，点开查看，即可查看需要填入到插件的 API KEY 值')
    logger.info(
        f'{plugin_name}获取天气：{city_name}，{cond}，图标代码：{daily_weather_iconDay}')
    return city_name, cond, daily_weather_iconDay


# 获取当天日期
def get_date():
    today = time.strftime("%Y-%m", time.localtime())
    today_day = time.strftime("%d", time.localtime())
    today_month = time.strftime("%m", time.localtime())
    today_year = time.strftime("%Y", time.localtime())
    return today, today_day, today_month, today_year

# 获取当天星期
def get_weekday():
    week_day_dict = {
        0: '一',
        1: '二',
        2: '三',
        3: '四',
        4: '五',
        5: '六',
        6: '日',
    }
    date = datetime.now()
    day = date.weekday()
    weekday = week_day_dict[day]
    return weekday

# 获取当天农历
def get_lunar_date(today_day, today_month, today_year):
    solar_date = datetime(int(today_year), int(
        today_month), int(today_day))  # 新建一个阳历日期
    solar_to_lunar_date = ZhDate.from_datetime(solar_date)  # 阳历日期转换农历日期
    # 输出中文农历日期
    lunar_date = solar_to_lunar_date.chinese()
    # 二零二二年三月初一 壬寅年 (虎年)提取三月初一
    lunar_date = re.search(r'年(.*?) ', lunar_date)
    if lunar_date:
        lunar_date = lunar_date.group(1)
        pattern = re.compile(r"二十([一二三四五六七八九])")
        lunar_date = pattern.sub(lambda m: f"廿{m.group(1)}", lunar_date)
    else:
        lunar_date = ''
    return lunar_date

# 获取心灵鸡汤
def get_quote():
    quote_url = 'https://v1.hitokoto.cn'
    quote = session.request("GET", quote_url, timeout=30)
    response = quote.json()
    quote_content = response['hitokoto']
    line_length = 21
    lines = []
    for i in range(0, len(quote_content), line_length):
        lines.append(quote_content[i:i + line_length])
    if len(lines) > 2:
        lines[1] = lines[1][:-1] + "..."
    quote_content = '\n'.join(lines[:2])
    return quote_content


def process_weather_data(daily_weather_iconDay):
    daily_weather_iconDay = int(daily_weather_iconDay)
    # Define colors
    today_day_color = (252, 215, 102)
    line_color = (255, 255, 255, 50)
    weekday_color = (255, 255, 255)
    today_color = (255, 255, 255)
    lunar_date_color = (255, 255, 255)
    quote_content_color = (255, 255, 255, 150)
    icon_color = (255, 255, 255)
    city_color = (255, 255, 255)
    weather_desc_color = (255, 255, 255)
    # Set colors for fog, haze, and dust
    if daily_weather_iconDay in [500, 501, 509, 510, 514, 515, 502, 511, 512, 513]:
        today_day_color = (169, 67, 56)
        line_color = (72, 63, 61, 50)
        weekday_color = (72, 63, 61)
        today_color = (72, 63, 61)
        lunar_date_color = (72, 63, 61)
        quote_content_color = (72, 63, 61, 150)
        icon_color = (72, 63, 61)
        city_color = (72, 63, 61)
        weather_desc_color = (72, 63, 61)
    # Define unicode values and background names
    default_weather_values = (hex(0xf1ca), 'sunny')
    weather_data = {
        99999:  default_weather_values,
        100:  (hex(0xf1cc), 'sunny'),
        101:  (hex(0xf1cd), 'cloud'),
        102:  (hex(0xf1ce), 'cloud'),
        103:  (hex(0xf1cf), 'cloud'),
        104:  (hex(0xf1d0), 'cloud'),
        300:  (hex(0xf1d5), 'rain'),
        301:  (hex(0xf1d6), 'rain'),
        302:  (hex(0xf1d7), 'rain'),
        303:  (hex(0xf1d8), 'rain'),
        304:  (hex(0xf1d9), 'rain'),
        305:  (hex(0xf1da), 'rain'),
        306:  (hex(0xf1db), 'rain'),
        307:  (hex(0xf1dc), 'rain'),
        308:  (hex(0xf1dd), 'rain'),
        309:  (hex(0xf1de), 'rain'),
        310:  (hex(0xf1df), 'rain'),
        311:  (hex(0xf1e0), 'rain'),
        312:  (hex(0xf1e1), 'rain'),
        313:  (hex(0xf1e2), 'rain'),
        314:  (hex(0xf1e3), 'rain'),
        315:  (hex(0xf1e4), 'rain'),
        316:  (hex(0xf1e5), 'rain'),
        317:  (hex(0xf1e6), 'rain'),
        318:  (hex(0xf1e7), 'rain'),
        399:  (hex(0xf1ea), 'rain'),
        400:  (hex(0xf1eb), 'snow'),
        401:  (hex(0xf1ec), 'snow'),
        402:  (hex(0xf1ed), 'snow'),
        403:  (hex(0xf1ee), 'snow'),
        404:  (hex(0xf1ef), 'snow'),
        405:  (hex(0xf1f0), 'snow'),
        406:  (hex(0xf1f1), 'snow'),
        407:  (hex(0xf1f2), 'snow'),
        408:  (hex(0xf1f3), 'snow'),
        409:  (hex(0xf1f4), 'snow'),
        410:  (hex(0xf1f5), 'snow'),
        499:  (hex(0xf1f8), 'snow'),
        500:  (hex(0xf1f9), 'fog'),
        501:  (hex(0xf1fa), 'fog'),
        502:  (hex(0xf1fb), 'haze'),
        503:  (hex(0xf1fc), 'dust'),
        504:  (hex(0xf1fd), 'dust'),
        507:  (hex(0xf1fe), 'dust'),
        508:  (hex(0xf1ff), 'dust'),
        509:  (hex(0xf200), 'haze'),
        510:  (hex(0xf201), 'haze'),
        511:  (hex(0xf202), 'haze'),
        512:  (hex(0xf203), 'haze'),
        513:  (hex(0xf204), 'haze'),
        514:  (hex(0xf205), 'fog'),
        515:  (hex(0xf206), 'fog')
    }
    bg_name = weather_data.get(
        daily_weather_iconDay, default_weather_values)[1]
    unicode_value = weather_data.get(
        daily_weather_iconDay, default_weather_values)[0]
    # bg_name, unicode_value = weather_data.get(daily_weather_iconDay, default_weather_values)
    unicode_text = chr(int(unicode_value, 16))
    return bg_name, unicode_text, today_day_color, line_color, weekday_color, today_color, lunar_date_color, quote_content_color, icon_color, city_color, weather_desc_color

# 绘制天气封面图片


def generate_image():
    # 画布大小
    width = 1500
    height = 640
    weekday = get_weekday()
    # 获取天气数据
    city_name, cond, daily_weather_iconDay = get_weather()
    today, today_day, today_month, today_year = get_date()
    lunar_date = get_lunar_date(today_day, today_month, today_year)
    quote_content = get_quote()
    bg_name, unicode_text, today_day_color, line_color, weekday_color, today_color, lunar_date_color, quote_content_color, icon_color, city_color, weather_desc_color = process_weather_data(daily_weather_iconDay)

    # 加载图片
    bg = Image.open(f"{plugin_path}/bg/{bg_name}.png")

    # 创建画布
    image = Image.new("RGBA", (width, height), (0, 0, 255, 0))
    square = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    # suqredraw = ImageDraw.Draw(square)

    # 绘制天气背景，覆盖整个画布
    square.paste(bg, (0, 0), mask=bg)

    # 加载字体
    icon_font = ImageFont.truetype(f"{plugin_path}/font/qweather-icons.ttf", 85)
    num_font_Bold = ImageFont.truetype(f"{plugin_path}/font/ALIBABA_Bold.otf", 345)
    num_font_Regular = ImageFont.truetype(f"{plugin_path}/font/ALIBABA_Regular.otf", 62)
    week_font_Regular = ImageFont.truetype(f"{plugin_path}/font/zh.ttf", 140)
    text_font = ImageFont.truetype(f"{plugin_path}/font/syht.otf", 53)
    quote_font = ImageFont.truetype(f"{plugin_path}/font/syht.otf", 60)

    day_x = 85
    day_y = 35
    # 绘制日期
    draw.text((day_x, day_y), today_day, fill=today_day_color,font=num_font_Bold, align='center')
    # today_day_width, today_day_height = draw.textsize(today_day, num_font_Bold)
    # 获取文字宽度
    today_day_width = draw.textlength(today_day, num_font_Bold)

    # 绘制竖线
    # 定义线段的起始坐标和终止坐标
    x0, y0 = day_x + today_day_width + 25, day_y + 118
    x1, y1 = x0, y0 + 210

    # 绘制白色线段，宽度为4
    draw.line((x0, y0, x1, y1), fill=line_color, width=4)

    # 绘制星期
    draw.text((day_x + today_day_width + 80, day_y + 95),'星', fill=weekday_color, font=week_font_Regular)
    draw.text((day_x + today_day_width + 80 + 120 + 20, day_y + 95),'期', fill=weekday_color, font=week_font_Regular)
    draw.text((day_x + today_day_width + 80 + 120 + 130 + 20, day_y + 95),weekday, fill=weekday_color, font=week_font_Regular)
    # 绘制年月
    year_month_width = draw.textlength(today, num_font_Regular)
    draw.text((day_x + today_day_width + 80, day_y + 270),today, fill=today_color, font=num_font_Regular)
    draw.text((day_x + today_day_width + 80 + year_month_width + 20,day_y + 270), lunar_date, fill=lunar_date_color, font=text_font)

    # 绘制鸡汤
    draw.text((day_x + 20, day_y+400), quote_content, fill=quote_content_color, font=quote_font)

    # 绘制天气图标
    icon_width = draw.textlength(unicode_text, icon_font)
    draw.text((width - 105 - icon_width, day_y + 100), unicode_text, fill=icon_color, font=icon_font, align='center')

    # 绘制城市
    city_width = draw.textlength(city_name, text_font)
    draw.text((width - 105 - city_width, day_y + 195), city_name, fill=city_color, font=text_font)
    # 绘制天气说明
    cond_width = draw.textlength(cond, text_font)
    draw.text((width - 105 - cond_width + 18, day_y + 270), cond, fill=weather_desc_color, font=text_font)
    # 保存图片
    image_output = Image.alpha_composite(square, image)
    image_output.save(f"{plugin_path}/weather.png")
    image_output = image_output.convert("RGB")
    image_output.save(f"{plugin_path}/weather.jpg", quality=97)
    image_path = f'{plugin_path}/weather.jpg'
    try:
        if not os.path.exists(image_path):
            image_path = f'{plugin_path}/logo.jpg'
    except Exception as e:
        logger.error(f'{plugin_name}检查文件是否存在时发生异常，原因：{e}')
    return image_path, lunar_date, weekday


def get_pic_url(image_path):
    filename = os.path.basename(image_path)
    pic_url = 'https://raw.githubusercontent.com/Alano-i/wecom-notification/main/MR-Plugins/daily_news/daily_news/logo.jpg'
    try:
        if server.site_url:
            # pic_url = f"{server.site_url}/api/plugins/{plugin_id}/{filename}"
            pic_url = f"{server.site_url}/api/frontend/get_plugin_logo?path=%2Fdata%2Fplugins%2F{plugin_id}%2F{filename}"

        else:
            logger.error(f"{plugin_name}未配置 NotifyHub 站点外网访问地址，请前往 系统设置 -> 网络设置 -> 站点访问地址 配置站点外网 URL")
    except Exception as e:
        logger.error(f"{plugin_name}获取通知封面前缀出错，原因：{e}")
    return pic_url


def send_notify(msg_title, msg_digest, msg_content, author, link_url, image_path, pic_url, news,is_mpnews):
    news_name = {
        'daily': '热点新闻',
        'entertainment': '热点影视快讯'
    }
    # logger.info(f"is_mpnews:{is_mpnews}")
    if notify_switch:
        try:
            # 按渠道发送（单个渠道）
            server.send_notify_by_channel(
                channel_name=bind_channel,
                title=msg_title,
                is_mpnews=is_mpnews,
                digest=msg_digest,
                content=msg_content if is_mpnews else msg_digest,
                push_img_url=pic_url,        # 可选
                push_link_url=link_url       # 可选
            )

            # 按通道发送（通道会绑定一个或多个渠道）
            # server.send_notify_by_router(
            #     route_id=BIND_ROUTES,
            #     title="IPTV 频道更新通知",
            #     content=content,
            #     push_img_url=None, # 可选
            #     push_link_url=None # 可选
            # )
            logger.info(f"{plugin_name}✅ 已发送通知")
        except Exception as e:
            logger.error(f"❌ 发送通知失败: {e}")
    else:
        logger.info(f"{plugin_name}通知开关未开启，跳过发送通知")


def auto_run():
    try:
        logger.info(f'{plugin_name}启动应用自动运行，开始获取每日新闻和天气')
        server.set_cache('is_get_news', 'daily_news', False)
        server.set_cache('is_get_news', 'entertainment', False)
        server.set_cache('is_get_news', 'hour', 8)
        # server.common.set_cache('is_get_news', 'entertainment', True)
        # server.common.set_cache('is_get_news', 'hour', '')
        if main():
            logger.info(f'{plugin_name}启动应用自动运行，获取每日新闻和天气完成！')
    except Exception as e:
        logger.error(f'{plugin_name}启动应用自动运行执行失败，原因：{e}')


def main():
    exit_falg = False
    hour = server.get_cache('is_get_news', 'hour') or datetime.now().time().hour
    get_news_flag_entertainment = True
    get_news_flag_daily = True
    generate_image_flag = False
    if not news_type:
        logger.error(f'{plugin_name}未设置新闻类型，请先设置！')
        return False
    for news in news_type:
        if news == 'entertainment' and hour != 8 and server.get_cache('is_get_news', 'entertainment'):
            logger.info(f'{plugin_name}今天已获取过影视快讯，将在明天 8:00 再次获取。')
            get_news_flag_entertainment = False
            continue
        if news == 'daily':
            is_mpnews=False
            wecom_title, wecom_digest, wecom_content, news_url, exit_falg = get_daily_news()
            if exit_falg:
                get_news_flag_daily = False
                continue
        
        if not generate_image_flag:
            image_path, lunar_date, weekday = generate_image()
            generate_image_flag = True
            pic_url = get_pic_url(image_path)
            logger.info(f'{plugin_name}获取封面图片地址：{pic_url}')
            author = f'农历{lunar_date} 星期{weekday}'
        if news == 'entertainment':
            is_mpnews=True
            wecom_title, wecom_digest, wecom_content, news_url = get_entertainment_news(pic_url)
        send_notify(wecom_title, wecom_digest, wecom_content,author, news_url, image_path, pic_url, news,is_mpnews)
    return get_news_flag_entertainment or get_news_flag_daily


@after_setup(plugin_id=plugin_id, desc="查询每日新闻")
def setup_cron_jobs():
    register_cron_job("0 8-18,23 * * *", "查询每日新闻", task, random_delay_seconds=10)
    # register_cron_job("55 * * * *", "查询每日新闻2", auto_run, random_delay_seconds=10)


def task():
    if datetime.now().time().hour in [8, 23]:
        server.set_cache('is_get_news', 'daily_news', False)
        server.set_cache('is_get_news', 'entertainment', False)
    if datetime.now().time().hour != 23:
        logger.info(f'{plugin_name}定时任务启动，开始获取每日新闻和天气')
        if main():
            logger.info(f'{plugin_name}定时任务获取每日新闻和天气完成！')



daily_news_router = APIRouter(prefix="/daily_news", tags=["daily_news"])

@daily_news_router.get("/{filename}")
async def cover(filename: str):
    # 图片在当前插件目录下的 cover 目录中
    file_path = os.path.join(plugin_path, filename)
    logger.info(f"{plugin_name}收到请求图片: {file_path}")
    if os.path.exists(file_path) and os.path.isfile(file_path):
        # 自动根据后缀推断类型
        ext = os.path.splitext(filename)[-1].lower()
        media_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
        }.get(ext, "application/octet-stream")
        # return FileResponse(file_path, media_type=media_type, filename=filename)  # filename 参数用于下载时的默认文件名，浏览器下载图片
        response = FileResponse(file_path, media_type=media_type)   # 浏览器直接显示图片
        # 设置缓存头，比如缓存 7 天
        response.headers["Cache-Control"] = "public, max-age=604800"
        return response
    else:
        return {"error": "Image not found"}
