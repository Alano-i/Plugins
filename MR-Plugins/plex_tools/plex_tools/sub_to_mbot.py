import requests
import logging
import time
from plexapi.server import PlexServer
from mbot.openapi import mbot_api
from moviebotapi.core.models import MediaType
# from moviebotapi.subscribe import SubStatus, Subscribe
server = mbot_api
# web = server.config.web
# port = web.port

plugins_name = '「PLEX 工具箱」'
logger = logging.getLogger(__name__)
def import_config(config):
    global tmdb_api_key, mbot_url, mbot_api_key, plex_url, plex_token
    mbot_url = config.get('mbot_url','')
    mbot_api_key = config.get('mbot_api_key','')
    plex_url = config.get('plex_url','')
    plex_token = config.get('plex_token','')

# 通过 tmdb_id 订阅影片
def movie_sub(title, tmdb_id, i=0, video_len=0,filter_name=''):
    # url=f"http://localhost:{port}/api/subscribe/sub_tmdb?tmdb_id={tmdb_id}&media_type=Movie&access_key={mbot_api_key}"
    counter_text = f'{i+1}/{video_len} ' if video_len else ''
    for v in range(3):
        try:
            # 通过 tmdb_id 获取 Mbot自建影视元数据
            media_meta = server.meta.get_media_by_tmdb(MediaType.Movie, tmdb_id)
            if media_meta:
                douban_id = media_meta.douban_id
                if douban_id:
                    # 提交订阅
                    if filter_name:
                        server.subscribe.sub_by_douban(int(douban_id), filter_name)
                    else:
                        server.subscribe.sub_by_douban(int(douban_id))
                else:
                    # 如果没有获取到 douban_id 采用 tmdb_id 提交订阅，此接口无法获取到订阅人，无法自动选择过滤器
                    logger.info(f"{plugins_name}['{title}'] 通过 tmdb_id 获取 豆瓣ID 失败或豆瓣中没有该影片，采用 tmdb 接口提交订阅")
                    server.subscribe.sub_by_tmdb(MediaType.Movie, int(tmdb_id))
            if v>0:
                logger.info(f"{plugins_name}['{title}'] {counter_text}提交 {v+1}/3 次订阅成功")
            else:
                logger.info(f"{plugins_name}['{title}'] {counter_text}提交订阅成功")
            break
        except Exception as e:
            logger.error(f"{plugins_name}['{title}'] {counter_text}提交订阅 {v+1}/3 次失败，原因：{e}")
            time.sleep(2)
            continue

# 通过 tmdb_id、季编号 订阅电视剧
def tv_sub(title, tmdb_id, season_number, i=0, video_len=0):
    # web接口
    # url=f"http://localhost:{port}/api/subscribe/sub_tmdb?tmdb_id={tmdb_id}&season_number={season_number}&media_type=TV&access_key={mbot_api_key}"
    # response = requests.get(url)
    # if response.status_code == 200:
    #     logger.info(f"{plugins_name}['{title}'] {counter_text}提交订阅成功")
    # else:
    #     logger.error(f"{plugins_name}['{title}'] {counter_text}提交订阅失败")
    # 内部接口
    counter_text = f'{i+1}/{video_len} ' if video_len else ''
    for v in range(3):
        try:
            server.subscribe.sub_by_tmdb(MediaType.TV, tmdb_id, season_number)
            if v>0:
                logger.info(f"{plugins_name}['{title}'] {counter_text}提交 {v+1}/3 次订阅成功")
            else:
                logger.info(f"{plugins_name}['{title}'] {counter_text}提交订阅成功")
            break
        except Exception as e:
            logger.error(f"{plugins_name}['{title}'] {counter_text}提交订阅 {v+1}/3 次失败，原因：{e}")
            time.sleep(2)
            continue



def push_sub(videos, media_type='Movie'):
    logger.info(f"{plugins_name}正在查找本地媒体，请稍候...")
    video_len=len(videos.all())
    for video,i in zip(videos.all(),range(video_len)):
        title = video.title
        guids=video.guids
        tmdb_id=''
        for v in guids:
            if v.id.split("://")[0]== 'tmdb':
                tmdb_id=v.id.split("://")[1]
        if media_type=='show':
            for s in video:
                # 通过 tmdb_id、季编号 订阅电视剧
                season_number = str(s.index)
                tv_sub(title, tmdb_id, season_number, i, video_len)
        else:
            # 通过 tmdb_id 订阅电影
            movie_sub(title, tmdb_id, i, video_len)
        time.sleep(1)

def push_sub_main(lib_name):
    try:
        plex = PlexServer(plex_url, plex_token)
    except Exception as e:
        logger.error(f"{plugins_name}连接 Plex 服务器失败，停止任务，原因：{e}")
        return
    try:
        videos = plex.library.section(lib_name)
        if videos:
            media_type=videos.TYPE
            push_sub(videos,media_type)
    except Exception as e:
        logger.error(f"{plugins_name}获取媒体出现错误! 原因：{e}")