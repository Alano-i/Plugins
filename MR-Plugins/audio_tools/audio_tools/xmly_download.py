import subprocess
import os
import logging
import requests
import re
import json
import pathlib
import shutil
from requests import auth
from requests.adapters import HTTPAdapter
from mbot.core.plugins import PluginContext,PluginMeta,plugin
from requests.packages.urllib3.util.retry import Retry
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
import time
import datetime
import urllib3
from urllib3.exceptions import MaxRetryError, ConnectionError, TimeoutError
from .functions import *
from .podcast import podcast_add_main
from .audio_tools import audio_clip, push_msg_to_mbot, move_to_dir, all_add_tag, add_cover

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('https://', adapter)
logger = logging.getLogger(__name__)
user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
# user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
def xmly_dl_config(config):
    global plugins_name,src_base_path_book, src_base_path_music,dst_base_path
    global sub_infos_set,update_podcast_config,magic,headers,mbot_url
    mbot_url = config.get('mbot_url','')
    plugins_name = config.get('plugins_name','')
    src_base_path_book = config.get('src_base_path_book','')
    src_base_path_music = config.get('src_base_path_music','')
    src_base_path_music = process_path(src_base_path_music)
    src_base_path_book = process_path(src_base_path_book)
    update_podcast_config = config.get('update_podcast_config',False)
    dst_base_path = config.get('dst_base_path','')
    sub_infos_set = config.get('sub_infos','')
    magic = config.get('magic','')
    if src_base_path_book:
        src_base_path_book = process_path(src_base_path_book)
    if src_base_path_music:
        src_base_path_music = process_path(src_base_path_music)
    headers = {
        'cookie': magic,
        'user-agent': user_agent,
    }

def get_downloaded_list_root_only(folder_path):
    file_extensions = ['.mp3', '.mp4', '.m4a', '.m4b', '.flac']  # 支持的文件扩展名
    episode_numbers = []
    # 遍历指定文件夹中的文件
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        # 检查文件是否是文件并且扩展名在支持的范围内
        if os.path.isfile(file_path) and any(file.lower().endswith(ext) for ext in file_extensions):
            # 使用正则表达式匹配集的数字部分
            episode_number = get_num(file)
            if episode_number:
                episode_numbers.append(episode_number)
    episode_numbers = sorted(episode_numbers)
    return episode_numbers

def get_downloaded_list(folder_path):
    file_extensions = ['.mp3', '.mp4', '.m4a', '.m4b', '.flac']  # 支持的文件扩展名
    episode_numbers = []

    # 使用 os.walk 遍历文件夹和所有子目录
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for file in filenames:
            file_path = os.path.join(dirpath, file)
            # 检查文件是否是文件并且扩展名在支持的范围内
            if os.path.isfile(file_path) and any(file.lower().endswith(ext) for ext in file_extensions):
                # 使用正则表达式匹配集的数字部分
                episode_number = get_num(file)
                if episode_number:
                    episode_numbers.append(episode_number)

    episode_numbers = sorted(episode_numbers)
    return episode_numbers

def get_new_track(album_id,index_on=False,index_offset=0,sub_start=1):
    base_url = "https://www.ximalaya.com/revision/album/v1/getTracksList"
    page_size =100
    num_pages = 50
    # url=f"https://www.ximalaya.com/revision/album/v1/getTracksList?albumId={album_id}&pageNum={page_num}&pageSize={page_size}"
    new_track_list = []
    new_track_info = {}
    all_track_list = []
    new_ep_mum_list = []
    track_info = {}
    for page_num in range(1, num_pages + 1):
        response = session.request("GET", base_url, params={"albumId": album_id, "pageNum": page_num, "pageSize": page_size}, headers=headers, timeout=30)  
        data = response.json()
        
        if "data" in data and "tracks" in data["data"]:
            tracks = data["data"]["tracks"]
            if len(tracks) > 0:
                for track in tracks:
                    title = track["title"]
                    ep = 0
                    if index_on:
                        ep = int(track['index']) + index_offset
                        title = f'第{ep}集 {title}'
                    title_num = get_num(title)
                    ep_num = title_num or int(track['index'])+index_offset
                    track_info = {
                        'index': track['index'],
                        'trackId': track['trackId'],
                        'title': track["title"]
                    }
                    # 所有集信息
                    all_track_list.append(track_info)
                    if ep_num not in downloaded_list and int(ep_num) >= int(sub_start):
                        new_track_info = {
                            'index': track['index'],
                            'trackId': track['trackId'],
                            'title': track["title"]
                        }
                        # 新增集信息
                        new_ep_mum_list.append(ep_num)
                        new_track_list.append(new_track_info) 
                        # new_ep_info.extend([(track["index"], track["trackId"], track["title"]) for track in tracks])
            else:
                break
        else:
            print(f"Error fetching data from page {page_num}")
    return new_track_list,new_ep_mum_list

def get_all_track(album_id,page):
    base_url = "https://www.ximalaya.com/revision/album/v1/getTracksList"
    page_size =30
    num_pages = 168
    # url=f"https://www.ximalaya.com/revision/album/v1/getTracksList?albumId={album_id}&pageNum={page_num}&pageSize={page_size}"
    track_id_list = []
    track_info={}
    all_track_list = []
    if not page:
        for page_num in range(1, num_pages + 1):
            response = session.request("GET", base_url, params={"albumId": album_id, "pageNum": page_num, "pageSize": page_size}, headers=headers, timeout=30)  
            data = response.json()
            if "data" in data and "tracks" in data["data"]:
                tracks = data["data"]["tracks"]
                if len(tracks) > 0:
                    for track in tracks:

                        track_info = {
                            'index': track['index'],
                            'trackId': track['trackId'],
                            'title': track["title"]
                        }
                        # 所有集信息列表
                        all_track_list.append(track_info)
                        # 所有集 ID 列表
                        track_id_list.append(track['trackId']) 
                else:
                    break
            else:
                logger.error(f"在第 {page_num} 页没有匹配到音频信息")
    else:
        response = session.request("GET", base_url, params={"albumId": album_id, "pageNum": page, "pageSize": page_size}, headers=headers, timeout=30)
        data = response.json()
        if "data" in data and "tracks" in data["data"]:
            tracks = data["data"]["tracks"]
            if len(tracks) > 0:
                for track in tracks:

                    track_info = {
                        'index': track['index'],
                        'trackId': track['trackId'],
                        'title': track["title"]
                    }
                    all_track_list.append(track_info)

                    track_id_list.append(track['trackId']) 
        else:
            logger.error(f"在第 {page} 页没有匹配到音频信息")
    return all_track_list

def modify_file_name(path,index_on,index,index_offset,book_title):
    directory, file_name = os.path.split(path)
    # 替换_为空格，去掉括号和括号内的内容
    new_file_name = re.sub(r'[_-]', ' ', file_name)  # 将_替换为空格
    # new_file_name = re.sub(r'[\（\(【].*?[\）\)】]', '', new_file_name)  # 去掉括号及其内部内容

    # 匹配并删除所有括号及其内容，除非括号内的内容仅仅是 上、中、下 或者 0-99 的数字
    # 调整正则表达式以考虑方括号中指定内容的周围空格。
    new_file_name = re.sub(r'[\（\(\[「『【]\s*(?:(上|中|下|\d{1,2})\s*[\）\)\]」』】]|.*?[\）\)\]」』】])', r'(\1)', new_file_name)
    # 移除空括号
    new_file_name = re.sub(r'[\（\(\[「『【]\s*[\）\)\]」』】]', '', new_file_name).strip()

    # 去除多余的空格
    new_file_name = ' '.join(new_file_name.split())
    # 将扩展名从.mp4替换为.m4a
    new_file_name = re.sub(r'\.mp4$', '.m4a', new_file_name)
    # try:
    #     if index:
    #         ep = int(index) + int(index_offset)
    #         new_file_name = f"第{ep}集 {new_file_name}"
    # except Exception as e:
    #     logger.error(f'{plugins_name}添加集号失败, 原因: {e}')
    new_path = os.path.join(directory,new_file_name)
    return new_path

def aes_decrypt(ciphertext, key):
    key = bytes.fromhex(key)
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted = cipher.decrypt(ciphertext)
    return unpad(decrypted, AES.block_size).decode('utf-8')

def save_track(path,url,title,ext,index_on = False,index=0,index_offset=0):
    track_url = url

    if index_on:
        ep = int(index)+int(index_offset)
        title = f'第{ep}集 {title}'
        
    save_path = os.path.join(path, f"{title}.{ext}")
    os.makedirs(path, exist_ok=True)
    retries = 5
    retry_delay = 3
    for i in range(retries):
        try:
            http = urllib3.PoolManager()
            response = http.request('GET', track_url)
            with io.open(save_path, "wb") as f:
                f.write(response.data)
            return save_path
        except (ConnectionError, TimeoutError, MaxRetryError) as e:
            logger.error(f'「{title}」保存 {track_url} 到本地 {i+1}/{retries} 次请求异常，原因：{e}')
            time.sleep(retry_delay)
            continue
        except Exception as e:
            logger.error(f'「{title}」保存 {track_url} 到本地 {i+1}/{retries} 次请求异常，原因：{e}')
            continue
    return ''

def cover_size(url):
    new_columns = 1000
    new_rows = 1000
    pattern = r'(columns=\d+&rows=\d+)'
    new_url = re.sub(pattern, f'columns={new_columns}&rows={new_rows}', url)
    return new_url
def fetch_track_by_id(track_id,path,folder_path_base,index_on = False,index=0,index_offset=0):
    if not track_id or not path: return ''
    folder_path_base = folder_path_base or path
    key = "aaad3e4fd540b0f79dca95606e72bf93"
    # headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'}
    timestamp = int(time.time())
    device = 'web'
    # device = 'iPhone'
    # url = f"http://mobile.ximalaya.com/v1/track/baseInfo?device=iPhone&trackId={track_id}"
    url = f"https://mobile.ximalaya.com/mobile-playpage/track/v3/baseInfo/{timestamp}?device={device}&trackId={track_id}"
    response = session.request("GET", url, headers=headers, timeout=30)
    if response.status_code == 200:
        data = response.json()
        uid = data.get('trackInfo', {}).get('uid', '')
        # title = data['trackInfo']['title']
        # playUrl = data['trackInfo']['playUrlList'][0]['url']
        title = data.get('trackInfo', {}).get('title', '')
        trackId = data.get('trackInfo', {}).get('trackId', '')
        playUrl = data.get('trackInfo', {}).get('playUrlList', [{}])[0].get('url', '')
        if playUrl:
            str2 = playUrl.replace('-','+').replace('_','/')
            num = len(str2) % 4
            if num: str2 += '=' * (4 - num)
            ciphertext = base64.b64decode(str2)
            decrypted = aes_decrypt(ciphertext, key)
            cover_url = data.get('trackInfo', {}).get('coverLarge', '')
            cover_url = cover_size(cover_url) if cover_url else ''
            isFree = data.get('trackInfo', {}).get('isFree', None)
            track_type = data.get('trackInfo', {}).get('playUrlList', [{}])[0].get('type', 'mp3')
            track_ext = track_type.split('_')[0].lower()
            track_info= {
                'title': title,
                'index': index,
                'trackId': trackId,
                'download_url': decrypted,
                'cover_url': cover_url,
                'isFree': isFree,
                'track_type': track_type,
            }
            logger.info(f"「获取喜马拉雅」解析后的信息：\n{track_info}")
            # path = '/Users/alano/Downloads/12563'
            cover_art_path = os.path.join(folder_path_base, 'cover.jpg')
            try:
                if cover_url and not os.path.exists(cover_art_path):
                    save_track(path, cover_url, 'cover','jpg',False,index,0)
            except Exception as e:
                logger.error(f'{plugins_name}下载喜马拉雅封面异常, 原因: {e}')
            try:
                if decrypted:
                    save_path = save_track(path, decrypted, title,track_ext,index_on,index,index_offset)
                    return save_path
                else:
                    if title:
                        logger.error(f"['{title}'] 没有解析到下载地址")
                    else:
                        logger.error(f"没有解析到下载地址")
                    return ''
            except Exception as e:
                logger.error(f'{plugins_name}下载喜马拉雅音频异常, 原因: {e}')
                return ''
        else:
            if title:
                logger.error(f"['{title}'] 没有解析到下载地址,可能是下载限流了，明天再来试试！")
            else:
                logger.error(f"没有解析到下载地址,可能是下载限流了，明天再来试试！")
            return ''
    else:
        logger.error(f"请求 {track_id} 所在的页面失败")
        return ''
# track_id = "657306328"
# folder_path_base = '/Users/alano/Downloads'
# path = '/Users/alano/Downloads/25'
# fetch_track_by_id(track_id,path,folder_path_base)
def xmly_download(save_path,dl,album_id,page,track,index_on,index_offset):
    result = True
    try:
        if dl == 'track':
            if album_id:
                page = ''
                all_track_list = get_all_track(album_id,page) if album_id else []
                # logger.error(f"all_track_list[0]:{all_track_list[0]}")
                # 在 all_track_list 中找到 trackId 所在项
                track_info = next((item for item in all_track_list if item["trackId"] == int(track)), {})
                # logger.error(f"track_info:{track_info}")
                if track_info:
                    track_id = track_info['trackId']
                    index = int(track_info['index'])
                    result = fetch_track_by_id(track_id,save_path,save_path,index_on,index,index_offset)
                else:
                    logger.error("没有获取到音频信息")
                    return False
            else:
                logger.error("未设置专辑ID（指定单集下载也需要设置），请设置后重试")
                return False
            # logger.error(f"result:{result}")
        elif dl == 'all' or dl == 'page':
            page = '' if dl == 'all' else page
            page = int(page) if page else ''
            # all_tracks = get_all_track(album_id,page) if album_id else []
            all_track_list = get_all_track(album_id,page) if album_id else []
            
            empty_count = 0
            for track_info in all_track_list:
                track_id = track_info['trackId']
                title = track_info['title']
                index = track_info['index']
                result = fetch_track_by_id(track_id,save_path,save_path,index_on,index,index_offset)
                if not result:
                    empty_count += 1
                else:
                    empty_count = 0
                if empty_count >= 8:
                    logger.error(f'{plugins_name}连续8次尝试下载喜马拉雅音频都出错了，停止任务')
                    break  # 如果连续出现3个空元素，跳出循环
    except Exception as e:
        logger.error(f'{plugins_name}下载喜马拉雅音频异常, 原因: {e}')
        result = False
    result = True if result else False
    return result

def move_all_files(src_path, dst_path):
    for root, dirs, files in os.walk(src_path):
        for file in files:
            source_file = os.path.join(root, file)
            target_file = os.path.join(dst_path, file)
            shutil.move(source_file, target_file)

def cut(book_title,folder_path_base,folder_path,output_dir,audio_start,audio_end,album):
    audio_files = []
    new_audios = []
    input_dir = folder_path
    clip_configs = 'clip_and_move'
    use_filename = True
    xmly_dl = True
    cliped_folder,series,authors,reader,year,subject,podcast_summary = '','','','','','',''
    series = book_title or series
    series,authors,reader,year,subject,podcast_summary = get_audio_info_all(folder_path_base,series,authors,reader,year,subject,podcast_summary)
    book_dir_name = get_book_dir_name(book_title, authors, reader)
    cliped_folder = book_dir_name
    art_album = series
    result = audio_clip(input_dir,output_dir,cliped_folder,audio_start,audio_end,clip_configs,authors,year,reader,series,podcast_summary,album,art_album,use_filename,subject,xmly_dl)
    if result:
        # folder_path_base = '/Media/downloads/有声书/阴阳刺青师-墨大先生-头陀渊'
        # cliped_folder_dir = '/Media/downloads/有声书/阴阳刺青师-墨大先生-头陀渊/tmp/阴阳刺青师'
        # audio = '/Media/downloads/有声书/阴阳刺青师-墨大先生-头陀渊/tmp/阴阳刺青师/1-100/1.mp3'
        audio_files,fill_num,audio_num = get_audio_files(os.path.join(folder_path, book_dir_name))
        if audio_files:
            for audio_file in audio_files:
                new_audio = os.path.join(src_base_path_book, book_dir_name, audio_file.split(f"/tmp/{book_dir_name}/")[1])
                new_audios.append(new_audio)
        move_all_files(folder_path, folder_path_base)
        shutil.rmtree(folder_path)
        cover_image_url = ''
        try:
            cover_image_path = os.path.join(output_dir, cliped_folder,'cover.jpg')
            cover_image_path_hlink = f"{dst_base_path}/{book_dir_name}_cover.jpg"
            light_link(cover_image_path,cover_image_path_hlink)
            if os.path.exists(cover_image_path_hlink):
                cover_image_url = f'{mbot_url}/static/podcast/audio/{book_dir_name}_cover.jpg'
                cover_image_url = url_encode(cover_image_url)
            else:
                cover_image_url = ''
        except Exception as e:
            logger.error(f"{plugins_name}构造消息参数出现错误，原因：{e}")
        try:
            if new_audios:
                link_url = f'{mbot_url}/static/podcast/index.html'
                msg_title = f'{series} - 新增 {len(new_audios)} 个音频'
                msg_digest = [os.path.basename(path) for path in new_audios]
                # msg_digest = ['第2集 久别重逢.m4a','第3集 久别.m4a']
                msg_digest = '\n'.join([f"• {item}" for item in msg_digest])
                push_msg_to_mbot(msg_title, msg_digest,cover_image_url,link_url)
        except Exception as e:
            logger.error(f"{plugins_name}发送更新消息失败，原因：{e}")
    return new_audios

def xmly_main():
    global downloaded_list,sub_infos
    sub = True
    result = True
    try:
        lines = sub_infos_set.strip().split('\n')
        sub_infos = []
        for line in lines:
            parts = line.split(',')
            sub_infos.append(parts)
    except Exception as e:
        logger.error(f'{plugins_name}获取有声书订阅信息异常, 原因: {e}')
        return False
    for sub_info in sub_infos:
        index_on,index_offset,sub_start,audio_start,audio_end = False,0,1,0,0
        try:
            book_title = sub_info[0]
            author = sub_info[1]
            reader = sub_info[2]
            sub_start = sub_info[3]
            downloaded_path_base = process_path(sub_info[4])
            album_id = int(sub_info[5])
            audio_start = int(sub_info[6])
            audio_end = int(sub_info[7])
            try:
                index_on = sub_info[8]
                if index_on == 'true':
                    index_on = True
                elif index_on == 'false':
                    index_on = False
            except Exception as e:
                index_on = False
            try:
                index_offset = int(sub_info[8])
            except Exception as e:
                index_offset = 0

            folder_path_base = os.path.join(downloaded_path_base, f"{book_title} - {author} - {reader}")
        except Exception as e:
            logger.error(f'{plugins_name}获取喜马拉雅订阅信息异常, 请确保参数数量正确，参数用英文逗号分隔，严格按设置下面的说明填写。具体原因: {e}')
            result = False
            continue

        album = ''
        new_audios = ''
        folder_path = os.path.join(folder_path_base, 'tmp')
        os.makedirs(folder_path_base, exist_ok=True)  # 创建目录
        os.makedirs(folder_path, exist_ok=True)
        cover_art_path = os.path.join(folder_path_base, 'cover.jpg')
        if os.path.exists(cover_art_path):
            shutil.copy(cover_art_path, os.path.join(folder_path, 'cover.jpg'))
        # downloaded_list = get_downloaded_list(folder_path_base)

        book_dir_name = get_book_dir_name(book_title, author, reader)

        local_book_path = os.path.join(src_base_path_book, book_dir_name)
        downloaded_list = get_downloaded_list(local_book_path)
        new_track_list,new_ep_mum_list = get_new_track(album_id,index_on,index_offset,sub_start)
        new_ep_text = format_sorted_list(new_ep_mum_list)
        new_dl_list= []
        if new_track_list:
            logger.info(f"「{book_title}」在喜马拉雅有新的剧集：第 {new_ep_text} 集")
            # logger.info(f"喜马拉雅已更新集：{new_track_list}\n")
            empty_count = 0
            dl_flag = False
            for track in new_track_list:
                index = track['index']
                save_path = fetch_track_by_id(track['trackId'],folder_path,folder_path_base,index_on,index,index_offset)
                if not save_path:
                    empty_count += 1
                else:
                    empty_count = 0
                if empty_count >= 8:
                    logger.error(f'{plugins_name}连续8次尝试下载喜马拉雅音频都出错了，停止任务')
                    break
                dl_path = save_path
                if dl_path:
                    if os.path.exists(dl_path):
                        logger.info(f"下载后原文件名:{dl_path}")
                        new_path = modify_file_name(dl_path,index_on,index,index_offset,book_title)
                        new_dl_list.append(new_path)
                        logger.info(f"文件重命名:{new_path}\n")
                        os.rename(dl_path, new_path)
                        dl_flag = True
                        # dst_path = os.path.join(src_base_path_book, book_title ,os.path.basename(new_path))
                        # if not hard_link(new_path, dst_path):
                        #     xxxx=1
            if dl_flag:
                new_audios = cut(book_title,folder_path_base,folder_path,src_base_path_book,audio_start,audio_end,album)
            else:
                continue
        else:
            logger.info(f"「{book_title}」在喜马拉雅未更新，跳过任务")
            continue
            # return True
        if new_audios:
            if len(new_audios) == 0:
                result = False
            else:
                episode_number_list=[]
                try:
                    for new_audio in new_audios:
                        episode_number = get_num(os.path.basename(new_audio))
                        if episode_number:
                            episode_number_list.append(episode_number)
                    new_audio_ep_num_text = format_sorted_list(episode_number_list)
                except Exception as e:
                    new_audio_ep_num_text = ''
            
                # logger.info(f"新增 {len(new_audios)} 个音频：{new_audios}")
                new_audios_detail = f"第 {new_audio_ep_num_text} 集" if new_audio_ep_num_text else new_audios
                logger.info(f"{plugins_name}新增 {len(new_audios)} 个音频：{new_audios_detail}")

                xml_path = os.path.join(src_base_path_book, book_dir_name, f'{book_title}.xml')
                audio_path = os.path.join(src_base_path_book, book_dir_name)
                result = podcast_add_main(book_title,author,reader,book_dir_name,audio_path,xml_path,new_audios,album_id,sub)
        else:
            result = False if new_ep_text else True
    return result
 
@plugin.task('update_podcast', '「更新播客」', cron_expression='5 8-23 * * *')
def task():
    if update_podcast_config:
        logger.info(f'{plugins_name}定时任务启动，开始同步喜马拉雅并更新播客')
        if xmly_main():
            logger.info(f'{plugins_name}同步喜马拉雅并更新播客完成')
        else:
            logger.info(f'{plugins_name}同步喜马拉雅并更新播客失败')