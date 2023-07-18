import requests
import logging
import time
from plexapi.server import PlexServer

plugins_name = '「PLEX 工具箱」'
logger = logging.getLogger(__name__)
def import_config(config):
    global tmdb_api_key, mbot_url, mbot_api_key, plex_url, plex_token
    mbot_url = config.get('mbot_url','')
    mbot_api_key = config.get('mbot_api_key','')
    plex_url = config.get('plex_url','')
    plex_token = config.get('plex_token','')

def push_sub(videos, media_type='Movie'):
    logger.info(f"{plugins_name}正在查找本地媒体，请稍候...")
    video_len=len(videos.all())
    for video,i in zip(videos.all(),range(video_len)):
        title = video.title
        guids=video.guids
        tmdbid=''
        for v in guids:
            if v.id.split("://")[0]== 'tmdb':
                tmdbid=v.id.split("://")[1]
        if media_type=='show':
            for s in video:
                season_number = str(s.index)
                url=f"{mbot_url}/api/subscribe/sub_tmdb?tmdb_id={tmdbid}&season_number={season_number}&media_type=TV&access_key={mbot_api_key}"
                response = requests.get(url)
                if response.status_code == 200:
                    logger.info(f"{plugins_name}['{title}'] {i+1}/{video_len} 导入（提交订阅）成功")
                else:
                    logger.error(f"{plugins_name}['{title}'] {i+1}/{video_len} 导入（提交订阅）失败")
        else:
            url=f"{mbot_url}/api/subscribe/sub_tmdb?tmdb_id={tmdbid}&media_type=Movie&access_key={mbot_api_key}"
            response = requests.get(url)
            if response.status_code == 200:
                logger.info(f"{plugins_name}['{title}'] {i+1}/{video_len} 导入（提交订阅）成功")
            else:
                logger.error(f"{plugins_name}['{title}'] {i+1}/{video_len} 导入（提交订阅）失败")
        time.sleep(0.5)

def push_sub_main(lib_name):
    try:
        plex = PlexServer(plex_url, plex_token)
    except Exception as e:
        logger.error(f"{plugins_name}连接 Plex 服务器失败,原因：{e}")
    try:
        videos = plex.library.section(lib_name)
        if videos:
            media_type=videos.TYPE
            push_sub(videos,media_type)
    except Exception as e:
        logger.error(f"{plugins_name}获取媒体出现错误! 原因：{e}")
