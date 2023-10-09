import requests
from lxml import etree
import random
import re
import requests
import time
from time import sleep
from mbot.openapi import mbot_api
from mbot.core.plugins import plugin
from moviebotapi.core.models import MediaType
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from .sub_to_mbot import movie_sub, tv_sub

logger = logging.getLogger(__name__)
plugins_name = '「PLEX 工具箱」'
server = mbot_api
session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('https://', adapter)
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.50'}
tmdb_api_key = ''

@plugin.task('get_top250', '「更新 TOP250 列表」', cron_expression='30 8 * * *')
def task():
    logger.info(f'{plugins_name}定时任务启动，开始获取最新 TOP250 列表')
    get_top250()
    logger.info(f'{plugins_name}定时获取最新 TOP250 列表完成')
    
def get_top250_config(config):
    global tmdb_api_key
    if config.get('tmdb_api_key'):
        logger.info(f'{plugins_name}已设置 TMDB API KEY')
        tmdb_api_key = config.get('tmdb_api_key')
    else:
        logger.info(f'{plugins_name}未设置 TMDB API KEY，请先设置')
        
def get_douban_top250_cn_name():
    url = 'https://movie.douban.com/top250'
    response = session.request("GET", url, headers=headers, timeout=30)  
    html = etree.HTML(response.text)
    old_douban_top250_list = server.common.get_cache('top250', 'douban') or []
    # logger.info(f'{plugins_name}「豆瓣TOP250」列表已有缓存，共 {len(old_douban_top250_list)} 部电影，如下：\n{old_douban_top250_list}')
    # movies = {}  如果想要 movies = {1: '肖申克的救赎', 2: '霸王别姬', 3: '阿甘正传'}
    movies = []         #  movies = ['肖申克的救赎', '霸王别姬', '阿甘正传']
    for start in range(0, 250, 25):
        page_url = f'{url}?start={start}'
        response = session.request("GET", page_url, headers=headers, timeout=30)
        if response.status_code == 200:
            html = etree.HTML(response.text)
            for i in range(1, 26):
                xpath_str = f'//*[@id="content"]/div/div[1]/ol/li[{i}]/div/div[2]/div[1]/a/span[1]/text()'
                title = html.xpath(xpath_str)[0]
                movies.append(title)         # movies = ['肖申克的救赎', '霸王别姬', '阿甘正传']
                # movies[start + i] = title  # movies = {1: '肖申克的救赎', 2: '霸王别姬', 3: '阿甘正传'}
        else:
            logger.error(f'{plugins_name}请求豆瓣 TOP250 失败：{response.text}')
    if movies:
        if old_douban_top250_list != movies:
            server.common.set_cache('top250', 'douban', movies)
            new_douban_top250_list = server.common.get_cache('top250', 'douban') or []
            logger.info(f'{plugins_name}最新「豆瓣TOP250」列表已存入缓存，共 {len(movies)} 部电影，如下：\n{new_douban_top250_list}')
        else:
            logger.info(f'{plugins_name}最新「豆瓣TOP250」列表与缓存相同，共 {len(movies)} 部电影，如下：\n{movies}')
    else:
        logger.error(f'{plugins_name}获取「豆瓣TOP250」列表失败')

def get_douban_top250():
    url = 'https://movie.douban.com/top250'
    response = session.request("GET", url, headers=headers, timeout=30)  
    html = etree.HTML(response.text)
    movies = []
    for start in range(0, 250, 25):
        page_url = f'{url}?start={start}'
        response = session.request("GET", page_url, headers=headers, timeout=30)
        if response.status_code == 200:
            html = etree.HTML(response.text)
            for i in range(1, 26):
                title_xpath = f'//*[@id="content"]/div/div[1]/ol/li[{i}]/div/div[2]/div[1]/a/span[1]/text()'
                year_xpath = f'//*[@id="content"]/div/div[1]/ol/li[{i}]/div/div[2]/div[2]/p/text()'
                year_info = html.xpath(year_xpath)[1].strip()
                title = html.xpath(title_xpath)[0]
                match = re.search(r'\d{4}', year_info)
                if match:
                    year = match.group(0)
                else:
                    year = ''
                movies.append({'title': title, 'year': int(year)})
        else:
            logger.error(f'{plugins_name}请求豆瓣 TOP250 失败：{response.text}')
    return movies

# 根据豆瓣电影名称和发行年份，在TMDB API中进行查询
def tmdb_search_movie(title, year):
    API_URL = 'https://api.themoviedb.org/3'
    for j in range(5):
        try:
            response = requests.get(
                f'{API_URL}/search/movie',
                params={
                    'api_key': tmdb_api_key,
                    'query': title,
                    'year': year,
                    'with_genres': '18' # 限制搜索结果只包含电影类型的影片
                }
            )
            break
        except Exception as e:
            logger.error(f"{plugins_name} 第 {j+1} 次获取 ['{title}'] 的 tmdb_id 失败，原因：{e}")
            continue
    if response.status_code != 200:
        return None
    results = response.json().get('results')
    if not results:
        return None
    # 如果存在多个结果，则返回第一个结果
    return results[0]

# 根据豆瓣电影名称和发行年份，通过 Mbot 接口进行查询
def search_movie_by_mbot(title, year):
    tmdb_id = None
    # title = '海上钢琴师'
    # year = '1998'
    language = 'zh-CN'
    # 订阅电影 = server.subscribe.sub_by_tmdb(MediaType.Movie, tmdb_id)
    # 搜索电影
    result = server.tmdb.search(MediaType.Movie, title, year, language)
    if result:
        tmdb_id = result[0].id
    else:
        tmdb_id = None
    return tmdb_id

def get_douban_top250_tmdb_list():
    douban_top250 = get_douban_top250()
    old_douban_top250_list = server.common.get_cache('top250', 'douban') or []
    # 根据豆瓣Top 250电影列表，建立电影名称和TMDB ID之间的对应关系
    douban_top250_tmdb_list = []
    for movie in douban_top250:
        title = movie['title']
        year = movie['year']
        for i in range(5):
            tmdb_id = search_movie_by_mbot(title, year)
            if tmdb_id:
                douban_top250_tmdb_list.append(tmdb_id)
                break
            else:
                logger.error(f"{plugins_name} 第 {i+1}/5 次获取{movie} 的 tmdb_id 失败")
        # result = tmdb_search_movie(title, year)
        # if result:
        #     douban_top250_tmdb_list.append(result['id'])
        # else:
        #     logger.error(f"{plugins_name}获取{movie} tmdb_id 失败")
    if douban_top250_tmdb_list:
        if old_douban_top250_list != douban_top250_tmdb_list and len(douban_top250_tmdb_list) == 250:
            server.common.set_cache('top250', 'douban', douban_top250_tmdb_list)
            new_douban_top250_list = server.common.get_cache('top250', 'douban') or []
            logger.info(f'{plugins_name}最新「豆瓣TOP250」列表已存入缓存，共 {len(douban_top250_tmdb_list)} 部电影，如下：\n{new_douban_top250_list}')
        else:
            logger.info(f'{plugins_name}最新「豆瓣TOP250」列表与缓存相同，或获取不足250部，不更新缓存，共 {len(douban_top250_tmdb_list)} 部电影，如下：\n{douban_top250_tmdb_list}')
    else:
        logger.error(f'{plugins_name}获取「豆瓣TOP250对应的 tmdb id」列表失败')

# 通过 IMDb ID 获取 TMDb ID
def get_tmdb_id(imdb_id):
    find_url = f'https://api.themoviedb.org/3/find/{imdb_id}?api_key={tmdb_api_key}&external_source=imdb_id'
    find_response = session.request("GET", find_url, headers=headers, timeout=30)
    tmdb_id = ''
    if find_response.status_code == 200:
        find_data = find_response.json()
        tmdb_id = find_data['movie_results'][0]['id']
    else:
        logger.error(f'{plugins_name}通过 IMDb ID 获取 TMDb ID 失败')
    return tmdb_id

# 通过 IMDb ID 获取 TMDb ID，通过 Mbot 接口实现
def get_tmdb_id_by_mbot(imdb_id):
    """
    此接口接受 tmdb_id 和 imdb_id 参数传入
    """
    for i in range(5):
        result = server.tmdb.get_external_ids(MediaType.Movie,imdb_id)
        if result:
            break
    if result:
        tmdb_id = result.id
    else:
        tmdb_id = None
        logger.error(f'{plugins_name}通过 IMDb ID 获取 TMDb ID 失败')
    return tmdb_id

# 通过 TMDb ID 获取电影中文名
def get_chinese_name(imdb_id):
    tmdb_id = get_tmdb_id(imdb_id)
    title_url = f'https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={tmdb_api_key}&language=zh-CN'
    title_response = session.request("GET", title_url, headers=headers, timeout=30)
    if title_response.status_code == 200:
        title_data = title_response.json()
        chinese_title = title_data['title']
        chinese_title = chinese_title.replace('Top Gun: Maverick', '壮志凌云2：独行侠')
        chinese_title = chinese_title.replace('Spider-Man: No Way Home', '蜘蛛侠：英雄无归')
        return chinese_title
    else:
        logger.error(f'{plugins_name}通过 TMDb ID 获取电影中文名失败')
        return imdb_id
        
def get_imdb_top_250():
    if not tmdb_api_key:
        logger.info(f'{plugins_name}未设置 TMDB API KEY，请先设置')
        return
    old_imdb_top250_list = server.common.get_cache('top250', 'imdb') or []
    # logger.info(f'{plugins_name}「IMDB TOP250」列表已有缓存，共 {len(old_imdb_top250_list)} 部电影，如下：\n{old_imdb_top250_list}')
    url = 'https://www.imdb.com/chart/top'
    try:
        for i in range(5):
            response = session.request("GET", url, headers=headers, timeout=90)
            if response.status_code == 200:
                # 使用etree解析HTML内容
                html = etree.HTML(response.text)
                # # 使用XPath选择器提取所有电影的IMDb ID
                ######################## 旧版 imdb top250网页 ########################
                # imdb_id_elements = html.xpath('//td[@class="titleColumn"]/a/@href')
                ######################## 新版 imdb top250网页 ########################
                imdb_id_elements = html.xpath('//*[@id="__next"]/main/div/div[3]/section/div/div[2]/div/ul/li/div[2]/div/div/div[1]/a/@href')
               
                imdb_ids = [imdb_id.split('/')[2] for imdb_id in imdb_id_elements]
                if imdb_ids:
                    break
                else:
                    logger.error(f"{plugins_name} 第 {i+1}/5 次请求 IMDB 网站解析 TOP250 列表失败")
    except Exception as e:
        logger.error(f"{plugins_name}获取 IMDB TOP250 失败，原因：{e}")

    if imdb_ids:
        if old_imdb_top250_list != imdb_ids and len(imdb_ids) == 250:
            server.common.set_cache('top250', 'imdb', imdb_ids)
            new_imdb_top250_list = server.common.get_cache('top250', 'imdb') or []
            logger.info(f'{plugins_name}最新「IMDB TOP250」列表已存入缓存，共 {len(imdb_ids)} 部电影，如下：\n{new_imdb_top250_list}')
        else:
            logger.info(f'{plugins_name}最新「IMDB TOP250」列表与缓存相同，或获取不足250部，不更新缓存，共 {len(imdb_ids)} 部电影，如下：\n{imdb_ids}')
    else:
        logger.error(f'{plugins_name}获取「IMDB TOP250」列表失败')

    #     imdb_top250_chinese_name = []
    #     for imdb_id in imdb_ids:
    #         try:
    #             chinese_name = get_chinese_name(imdb_id)
    #             imdb_top250_chinese_name.append(chinese_name)
    #         except Exception as e:
    #             logger.error(f"{plugins_name} 获取影片中文名失败，请检查网络，原因：{e}")
    #             break
    #     #    logger.info(imdb_top250_chinese_name)
    # else:
    #     logger.error(f'{plugins_name}获取 IMDB TOP250 电影的 TMDb ID 失败')

    # if imdb_top250_chinese_name:
    #     if old_imdb_top250_list != imdb_top250_chinese_name:
    #         server.common.set_cache('top250', 'imdb', imdb_top250_chinese_name)
    #         new_imdb_top250_list = server.common.get_cache('top250', 'imdb') or []
    #         logger.info(f'{plugins_name}最新「IMDB TOP250」列表已存入缓存，共 {len(imdb_top250_chinese_name)} 部电影，如下：\n{new_imdb_top250_list}')
    #     else:
    #         logger.info(f'{plugins_name}最新「IMDB TOP250」列表与缓存相同，共 {len(imdb_top250_chinese_name)} 部电影，如下：\n{imdb_top250_chinese_name}')
    # else:
    #     logger.error(f'{plugins_name}获取「IMDB TOP250」列表失败')

def get_imdb_top_250_cn_name():
    if not tmdb_api_key:
        logger.info(f'{plugins_name}未设置 TMDB API KEY，请先设置')
        return
    old_imdb_top250_list = server.common.get_cache('top250', 'imdb') or []
    # logger.info(f'{plugins_name}「IMDB TOP250」列表已有缓存，共 {len(old_imdb_top250_list)} 部电影，如下：\n{old_imdb_top250_list}')
    url = 'https://www.imdb.com/chart/top'
    response = session.request("GET", url, headers=headers, timeout=30)
    if response.status_code == 200:
        html = etree.HTML(response.text)
        # 获取 imdbtop250 电影 imdb id
        imdb_ids = html.xpath('//td[@class="titleColumn"]/a/@href')
        imdb_ids = [id.split('/')[2] for id in imdb_ids]
        imdb_top250_chinese_name = []
        for imdb_id in imdb_ids:
            try:
                chinese_name = get_chinese_name(imdb_id)
                imdb_top250_chinese_name.append(chinese_name)
            except Exception as e:
                logger.error(f"{plugins_name} 获取影片中文名失败，请检查网络，原因：{e}")
                break
    else:
        logger.error(f'{plugins_name}获取 IMDB TOP250 电影的 TMDb ID 失败')
    if imdb_top250_chinese_name:
        if old_imdb_top250_list != imdb_top250_chinese_name:
            server.common.set_cache('top250', 'imdb', imdb_top250_chinese_name)
            new_imdb_top250_list = server.common.get_cache('top250', 'imdb') or []
            logger.info(f'{plugins_name}最新「IMDB TOP250」列表已存入缓存，共 {len(imdb_top250_chinese_name)} 部电影，如下：\n{new_imdb_top250_list}')
        else:
            logger.info(f'{plugins_name}最新「IMDB TOP250」列表与缓存相同，共 {len(imdb_top250_chinese_name)} 部电影，如下：\n{imdb_top250_chinese_name}')
    else:
        logger.error(f'{plugins_name}获取「IMDB TOP250」列表失败')

def is_local(tmdb_id):
    title = ''
    release_date = ''
    local_movie = server.media_server.search_by_tmdb(tmdb_id)
    if not local_movie:
        local_flag = False
        # 通过 tmdb id 查询缺失的豆瓣top电影类型的信息
        result = server.tmdb.get(MediaType.Movie, tmdb_id)
        if result:
            title = result.title
            release_date = result.release_date
        else:
            title = '未知'
            release_date = '未知'
    else:
        local_flag = True
    return local_flag, title, release_date

def get_lost_douban_top250(sub_set=False,filter_name=''):
    logger.info(f'{plugins_name}开始查询媒体库中缺失的豆瓣 TOP250 影片')
    lost_doubantop250_list = []
    lost_doubantop250 = {}
    douban_top250_tmdb_ids = server.common.get_cache('top250', 'douban') or []
    if not douban_top250_tmdb_ids:
        douban_top250_tmdb_ids = [278, 10997, 13, 597, 101, 129, 637, 424, 157336, 27205, 37165, 28178, 10376, 20453, 5528, 10681, 10775, 269149, 37257, 21835, 81481, 238, 77338, 1402, 43949, 8392, 746, 354912, 31439, 155, 671, 122, 770, 532753, 14160, 255709, 4935, 389, 517814, 360814, 51533, 25838, 10515, 640, 87827, 365045, 423, 13345, 121, 9475, 804, 11216, 207, 490132, 47759, 120, 603, 240, 8587, 242452, 10451, 550, 453, 4922, 14574, 582, 47002, 100, 10867, 15121, 411088, 19995, 857, 21334, 510, 12445, 274, 120467, 11324, 1954, 1124, 9470, 489, 23128, 673, 680, 18329, 311, 74308, 3082, 53168, 2832, 11423, 807, 4977, 22, 672, 69504, 25538, 37703, 158445, 31512, 398818, 142, 162, 16804, 76, 197, 49026, 745, 11104, 128, 177572, 80, 4291, 37185, 194, 161285, 51739, 294682, 9559, 2517, 210577, 30421, 1100466, 122906, 37797, 336026, 594, 10191, 348678, 242, 10494, 92321, 585, 674, 4348, 10193, 165213, 396535, 20352, 68718, 24238, 54186, 587, 74037, 55157, 9261, 333339, 205596, 526431, 77117, 55156, 10950, 843, 4588, 324786, 209764, 346, 150540, 539, 605, 372058, 176, 359940, 152532, 49519, 292362, 2503, 598, 11471, 205, 47423, 81, 315846, 132344, 497, 77, 39693, 31743, 45380, 265195, 872, 475557, 505192, 62, 295279, 244786, 82690, 14310, 508442, 12405, 425, 26466, 40751, 15804, 16859, 7350, 13398, 89825, 508, 475149, 44214, 16074, 901, 45612, 380, 11036, 334541, 57627, 644, 424694, 8290, 39915, 280, 76341, 548, 12477, 40213, 782, 12429, 16869, 1541, 406997, 220289, 473267, 695932, 604, 313369, 1372, 525832, 1830, 25050, 43824, 122973, 286217, 12444, 33320, 2502, 9345, 18311, 4476, 2501, 8055, 198277, 116745, 675, 1427, 324857, 14069]
    try:
        for tmdb_id in douban_top250_tmdb_ids:
            local_flag, title, release_date = is_local(tmdb_id)
            if not local_flag:
                lost_doubantop250 = {
                    "title" : title,
                    "tmdb_id": tmdb_id,
                    "release_date": release_date
                }
                lost_doubantop250_list.append(lost_doubantop250)

            # local_movie = server.media_server.search_by_tmdb(tmdb_id)
            # if not local_movie:
            #     # 通过 tmdb id 查询缺失的豆瓣top电影类型的信息
            #     result = server.tmdb.get(MediaType.Movie, tmdb_id)
            #     if result:
            #         title = result.title
            #         release_date = result.release_date
            #     else:
            #         title = '未知'
            #         release_date = '未知'
            #     lost_doubantop250 = {
            #         "title" : title,
            #         "tmdb_id": tmdb_id,
            #         "release_date": release_date
            #     }
            #     lost_doubantop250_list.append(lost_doubantop250)
        logger.info(f'{plugins_name}媒体库中缺失豆瓣TOP250： {len(lost_doubantop250_list)} 部电影，如下：\n{lost_doubantop250_list}')
        # 订阅缺失的 豆瓣TOP250
        if sub_set and lost_doubantop250_list:
            lost_doubantop250_count = len(lost_doubantop250_list)
            for lost_doubantop250,i in zip(lost_doubantop250_list,range(lost_doubantop250_count)):
                title = lost_doubantop250['title']
                tmdb_id = lost_doubantop250['tmdb_id']
                movie_sub(title, tmdb_id, i, lost_doubantop250_count,filter_name)
                time.sleep(1)
                # if i>=0: return
    except Exception as e:
        logger.error(f"{plugins_name}获取媒体库中缺失的豆瓣 TOP250 列表失败，原因：{e}")


def get_lost_imdb_top250(sub_set,filter_name=''):
    logger.info(f'{plugins_name}开始查询媒体库中缺失的 IMDB TOP250 影片')
    lost_imdbtop250_list = []
    imdb_top250_tmdb_ids_list = []
    imdb_top250_tmdb_id = ''
    lost_imdb_top250 = {}
    imdb_top250_ids = server.common.get_cache('top250', 'imdb') or []
    if not imdb_top250_ids:
        imdb_top250_ids = ['tt0111161', 'tt0068646', 'tt0468569', 'tt0071562', 'tt0050083', 'tt0108052', 'tt0167260', 'tt0110912', 'tt0120737', 'tt0060196', 'tt0109830', 'tt9362722', 'tt0137523', 'tt0167261', 'tt1375666', 'tt0080684', 'tt0133093', 'tt0099685', 'tt0073486', 'tt0114369', 'tt0038650', 'tt0047478', 'tt0102926', 'tt0120815', 'tt0317248', 'tt0816692', 'tt0118799', 'tt0120689', 'tt0076759', 'tt0103064', 'tt0088763', 'tt0245429', 'tt0253474', 'tt0054215', 'tt6751668', 'tt0110413', 'tt0110357', 'tt0172495', 'tt0120586', 'tt0407887', 'tt2582802', 'tt0482571', 'tt0114814', 'tt0034583', 'tt0095327', 'tt0056058', 'tt1675434', 'tt0027977', 'tt0064116', 'tt0095765', 'tt0047396', 'tt0078748', 'tt0021749', 'tt0078788', 'tt0209144', 'tt1853728', 'tt0082971', 'tt0910970', 'tt0405094', 'tt0043014', 'tt0050825', 'tt4154756', 'tt0081505', 'tt0032553', 'tt0051201', 'tt4633694', 'tt0090605', 'tt0169547', 'tt1345836', 'tt0057012', 'tt0361748', 'tt0364569', 'tt2380307', 'tt0086879', 'tt0114709', 'tt0112573', 'tt0082096', 'tt7286456', 'tt4154796', 'tt0119698', 'tt0119217', 'tt0087843', 'tt5311514', 'tt1187043', 'tt0045152', 'tt0057565', 'tt0180093', 'tt8267604', 'tt0435761', 'tt0086190', 'tt0091251', 'tt0338013', 'tt0062622', 'tt2106476', 'tt0105236', 'tt0056172', 'tt0033467', 'tt0022100', 'tt0044741', 'tt0053125', 'tt0053604', 'tt0052357', 'tt0211915', 'tt0036775', 'tt0066921', 'tt0093058', 'tt0086250', 'tt8503618', 'tt1255953', 'tt0113277', 'tt1049413', 'tt0056592', 'tt0070735', 'tt1832382', 'tt0017136', 'tt0095016', 'tt0119488', 'tt0097576', 'tt0208092', 'tt0040522', 'tt0075314', 'tt0986264', 'tt8579674', 'tt5074352', 'tt0363163', 'tt1745960', 'tt0059578', 'tt0372784', 'tt0012349', 'tt0053291', 'tt10272386', 'tt0993846', 'tt0042192', 'tt6966692', 'tt0055031', 'tt0120382', 'tt0089881', 'tt0112641', 'tt0469494', 'tt0457430', 'tt1130884', 'tt0105695', 'tt0167404', 'tt0107290', 'tt0268978', 'tt0040897', 'tt0055630', 'tt0071853', 'tt0477348', 'tt0266697', 'tt0057115', 'tt0042876', 'tt0084787', 'tt0266543', 'tt10872600', 'tt0080678', 'tt0071315', 'tt0081398', 'tt0434409', 'tt0031381', 'tt0046912', 'tt0347149', 'tt0120735', 'tt2096673', 'tt1305806', 'tt5027774', 'tt1392214', 'tt0117951', 'tt0050212', 'tt6791350', 'tt0116282', 'tt1291584', 'tt1205489', 'tt0264464', 'tt0096283', 'tt0405159', 'tt0118849', 'tt4729430', 'tt0083658', 'tt1201607', 'tt0015864', 'tt2024544', 'tt0112471', 'tt2278388', 'tt0052618', 'tt2267998', 'tt0047296', 'tt0072684', 'tt0017925', 'tt0050986', 'tt0107207', 'tt0077416', 'tt2119532', 'tt0041959', 'tt0353969', 'tt0046268', 'tt0015324', 'tt3011894', 'tt0031679', 'tt1392190', 'tt0978762', 'tt0097165', 'tt0198781', 'tt0892769', 'tt0050976', 'tt0073195', 'tt3170832', 'tt0118715', 'tt0046438', 'tt1950186', 'tt0019254', 'tt0395169', 'tt0382932', 'tt0075148', 'tt0091763', 'tt3315342', 'tt1895587', 'tt0088247', 'tt15097216', 'tt1979320', 'tt0381681', 'tt0092005', 'tt0074958', 'tt0758758', 'tt0032138', 'tt0036868', 'tt0113247', 'tt0070047', 'tt0317705', 'tt0325980', 'tt0035446', 'tt0107048', 'tt0476735', 'tt0032551', 'tt0058946', 'tt1028532', 'tt4016934', 'tt0048473', 'tt0245712', 'tt0032976', 'tt0061512', 'tt0059742', 'tt0025316', 'tt0053198', 'tt0060827', 'tt1454029', 'tt0129167', 'tt0079470', 'tt0103639', 'tt0099348']
    # 将imdb id转为tmdb id
    for imdb_id in imdb_top250_ids:
        # imdb_top250_tmdb_id = get_tmdb_id(imdb_id)
        imdb_top250_tmdb_id = get_tmdb_id_by_mbot(imdb_id)
        if imdb_top250_tmdb_id:
            imdb_top250_tmdb_ids_list.append(imdb_top250_tmdb_id)
    try:
        for tmdb_id in imdb_top250_tmdb_ids_list:
            local_flag, title, release_date = is_local(tmdb_id)
            if not local_flag:
                lost_imdb_top250 = {
                    "title" : title,
                    "tmdb_id": tmdb_id,
                    "release_date": release_date
                }
                lost_imdbtop250_list.append(lost_imdb_top250)
        logger.info(f'{plugins_name}媒体库中缺失 IMDB TOP250： {len(lost_imdbtop250_list)} 部电影，如下：\n{lost_imdbtop250_list}')
        # 订阅缺失的 IMDB TOP250
        if sub_set and lost_imdbtop250_list:
            lost_imdbtop250_count = len(lost_imdbtop250_list)
            for lost_imdbtop250,i in zip(lost_imdbtop250_list,range(lost_imdbtop250_count)):
                title = lost_imdbtop250['title']
                tmdb_id = lost_imdbtop250['tmdb_id']
                movie_sub(title, tmdb_id, i, lost_imdbtop250_count,filter_name)
                time.sleep(1)
                # if i>=0: return
    except Exception as e:
        logger.error(f"{plugins_name} 获取媒体库中缺失的 IMDB TOP250 列表失败，原因：{e}")

def get_lost_top250(sub_set,filter_name):
    get_lost_douban_top250(sub_set,filter_name)
    get_lost_imdb_top250(sub_set,filter_name)

def get_top250():
    get_douban_top250_tmdb_list()
    get_imdb_top_250()