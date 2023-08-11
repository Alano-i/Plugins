import subprocess
import os
import logging
import requests
import re
import json
import pathlib
import shutil
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
from .audio_tools import audio_clip, move_to_dir, all_add_tag, add_cover
session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('https://', adapter)
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
logger = logging.getLogger(__name__)


def xmly_dl_config(config):
    global plugins_name,src_base_path_book, src_base_path_music,dst_base_path
    global sub_infos_set,update_podcast_config
    plugins_name = config.get('plugins_name','')
    src_base_path_book = config.get('src_base_path_book','')
    src_base_path_music = config.get('src_base_path_music','')
    update_podcast_config = config.get('update_podcast_config',False)
    dst_base_path = config.get('dst_base_path','')
    sub_infos_set = config.get('sub_infos','')
    if src_base_path_book:
        src_base_path_book = process_path(src_base_path_book)
    if src_base_path_music:
        src_base_path_music = process_path(src_base_path_music)

def get_downloaded_list(folder_path):
    file_extensions = ['.mp3', '.mp4', '.m4a']  # 支持的文件扩展名
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

def get_new_track(album_id):
    base_url = "https://www.ximalaya.com/revision/album/v1/getTracksList"
    page_size =100
    num_pages = 50
    # url=f"https://www.ximalaya.com/revision/album/v1/getTracksList?albumId={album_id}&pageNum={page_num}&pageSize={page_size}"
    new_track_list = []
    for page_num in range(1, num_pages + 1):
        # response = requests.get(base_url, params={"albumId": album_id, "pageNum": page_num, "pageSize": page_size}, headers=headers)
        response = session.request("GET", base_url, params={"albumId": album_id, "pageNum": page_num, "pageSize": page_size}, headers=headers, timeout=30)  
        data = response.json()
        if "data" in data and "tracks" in data["data"]:
            tracks = data["data"]["tracks"]
            if len(tracks) > 0:
                for track in tracks:
                    title = track["title"]
                    title_num = get_num(title)
                    ep_num = title_num or track['index']
                    if ep_num not in downloaded_list:
                        new = {
                            'index': track['index'],
                            'trackId': track['trackId'],
                            'title': track["title"]
                        }
                        new_track_list.append(new) 
                        # new_ep_info.extend([(track["index"], track["trackId"], track["title"]) for track in tracks])
            else:
                break
        else:
            print(f"Error fetching data from page {page_num}")
    return new_track_list

def get_all_track(album_id,page):
    base_url = "https://www.ximalaya.com/revision/album/v1/getTracksList"
    page_size =30
    num_pages = 166
    # url=f"https://www.ximalaya.com/revision/album/v1/getTracksList?albumId={album_id}&pageNum={page_num}&pageSize={page_size}"
    track_list = []
    if not page:
        for page_num in range(1, num_pages + 1):
            response = session.request("GET", base_url, params={"albumId": album_id, "pageNum": page_num, "pageSize": page_size}, headers=headers, timeout=30)  
            data = response.json()
            if "data" in data and "tracks" in data["data"]:
                tracks = data["data"]["tracks"]
                if len(tracks) > 0:
                    for track in tracks:
                        track_list.append(track['trackId']) 
                else:
                    break
            else:
                print(f"Error fetching data from page {page_num}")
    else:
        response = session.request("GET", base_url, params={"albumId": album_id, "pageNum": page, "pageSize": page_size}, headers=headers, timeout=30)
        data = response.json()
        if "data" in data and "tracks" in data["data"]:
            tracks = data["data"]["tracks"]
            if len(tracks) > 0:
                for track in tracks:
                    track_list.append(track['trackId']) 
        else:
            print(f"Error fetching data from page {page_num}")
    return track_list

def modify_file_name(path):
    directory, file_name = os.path.split(path)
    # 替换_为空格，去掉括号和括号内的内容
    new_file_name = re.sub(r'[_-]', ' ', file_name)  # 将_替换为空格
    new_file_name = re.sub(r'[\（\(].*?[\）\)]', '', new_file_name)  # 去掉括号及其内部内容
    # 去除多余的空格
    new_file_name = ' '.join(new_file_name.split())
    # 将扩展名从.mp4替换为.m4a
    new_file_name = re.sub(r'\.mp4$', '.m4a', new_file_name)
    new_path = os.path.join(directory,new_file_name)
    return new_path

def run_bash_script(command):
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stderr:
            print(result.stderr)    
    except subprocess.CalledProcessError as e:
        logger.info("Error:", e)
        exit(-1)

def run_command(command, capture, **kwargs):
    """Run a command while printing the live output"""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        **kwargs,
    )
    while True:  # Could be more pythonic with := in Python3.8+
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if capture:
            logger.info(line.decode().strip())

def xmly(save_path,dl,album_id,page,track):
    sh_path = "/data/plugins/audio_tools/xmlyfetcher"
    # sh_path = '/usr/local/bin/xmlyfetcher'
    if dl == 'all':
        bash_command = f"{sh_path} -o {save_path} {album_id} all"
    if dl == 'page':
        bash_command = f"{sh_path} -o {save_path} {album_id} page {page}"
    if dl == 'track':
        bash_command = f"{sh_path} -o {save_path} {album_id} track {track}"
        # bash_command = f"/data/plugins/audio_tools/xmlyfetcher -o /data/test_xmly 49964578 track 423744747"
    logger.info(f"bash_command:{bash_command}")
    run_bash_script(bash_command)
    # run_command(
    #     [
    #         "./xmlyfetcher",
    #         f"-o  {save_path}",
    #         album_id,
    #         f"track {track}",
    #     ],
    #     True,
    #     cwd=pathlib.Path(__file__).parent.absolute(),
    # )


def aes_decrypt(ciphertext, key):
    key = bytes.fromhex(key)
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted = cipher.decrypt(ciphertext)
    return unpad(decrypted, AES.block_size).decode('utf-8')

def save_track(path,url,title,ext):
    track_url = url
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
def fetch_track_by_id(track_id,path,folder_path_base):
    if not track_id or not path: return ''
    folder_path_base = folder_path_base or path
    key = "aaad3e4fd540b0f79dca95606e72bf93"
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'}
    timestamp = int(time.time())
    device = 'web'
    device = 'iPhone'
    # url = f"http://mobile.ximalaya.com/v1/track/baseInfo?device=iPhone&trackId={track_id}"
    url = f"https://mobile.ximalaya.com/mobile-playpage/track/v3/baseInfo/{timestamp}?device={device}&trackId={track_id}"
    # response = requests.get(url)
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
            isFree = data.get('trackInfo', {}).get('isFree', False)
            track_type = data.get('trackInfo', {}).get('playUrlList', [{}])[0].get('type', 'mp3')
            track_ext = track_type.split('_')[0].lower()
            track_info= {
                'title': title,
                'trackId': trackId,
                'download_url': decrypted,
                'cover_url': cover_url,
                'isFree': isFree,
                'track_type': track_type,
            }
            logger.info(f"「获取喜马拉雅」解析后的信息：\n{track_info}\n")
            # path = '/Users/alano/Downloads/12563'
            cover_art_path = os.path.join(folder_path_base, 'cover.jpg')
            try:
                if cover_url and not os.path.exists(cover_art_path):
                    save_track(path, cover_url, 'cover','jpg')
            except Exception as e:
                logger.error(f'{plugins_name}下载喜马拉雅封面异常, 原因: {e}')
            try:
                if decrypted:
                    save_path = save_track(path, decrypted, title,track_ext)
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

def xmly_download(save_path,dl,album_id,page,track):
    result = True
    try:
        if dl == 'track':
            result = fetch_track_by_id(track,save_path,save_path)
            # logger.error(f"result:{result}")
        elif dl == 'all' or dl == 'page':
            page = '' if dl == 'all' else page
            page = int(page) if page else ''
            all_tracks = get_all_track(album_id,page) if album_id else []
            empty_count = 0
            for track_id in all_tracks:
                result = fetch_track_by_id(track_id,save_path,save_path)
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
    cliped_folder = series
    art_album = series
    result = audio_clip(input_dir,output_dir,cliped_folder,audio_start,audio_end,clip_configs,authors,year,reader,series,podcast_summary,album,art_album,use_filename,subject,xmly_dl)
    if result:
        # folder_path_base = '/Media/downloads/有声书/阴阳刺青师-墨大先生-头陀渊'
        # cliped_folder_dir = '/Media/downloads/有声书/阴阳刺青师-墨大先生-头陀渊/tmp/阴阳刺青师'
        # audio = '/Media/downloads/有声书/阴阳刺青师-墨大先生-头陀渊/tmp/阴阳刺青师/1-100/1.mp3'
        audio_files,fill_num,audio_num = get_audio_files(os.path.join(folder_path, book_title))
        if audio_files:
            for audio_file in audio_files:
                new_audio = os.path.join(src_base_path_book, book_title, audio_file.split(f"/tmp/{book_title}/")[1])
                new_audios.append(new_audio)
        move_all_files(folder_path, folder_path_base)
        shutil.rmtree(folder_path)
    return new_audios

def xmly_main():
    global downloaded_list,sub_infos
    result = True
    # sub_infos=[['阴阳刺青师','/Media/downloads/有声书/阴阳刺青师-墨大先生-头陀渊','75986638','0','0']]
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
        book_title = sub_info[0]
        folder_path_base = sub_info[1]
        album_id = int(sub_info[2])
        audio_start = int(sub_info[3])
        audio_end = int(sub_info[4])
        album = ''
        new_audios = ''
        folder_path = os.path.join(folder_path_base, 'tmp')
        os.makedirs(folder_path_base, exist_ok=True)  # 创建目录
        os.makedirs(folder_path, exist_ok=True)
        cover_art_path = os.path.join(folder_path_base, 'cover.jpg')
        if os.path.exists(cover_art_path):
            shutil.copy(cover_art_path, os.path.join(folder_path, 'cover.jpg'))
        downloaded_list = get_downloaded_list(folder_path_base)
        new_track_list = get_new_track(album_id)
        new_dl_list= []
        if new_track_list:
            logger.info(f"喜马拉雅已更新集：{new_track_list}\n")
            empty_count = 0
            for track in new_track_list:
                save_path = fetch_track_by_id(track['trackId'],folder_path,folder_path_base)
                # xmly(folder_path,'track',album_id,'',track['trackId'])
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
                        new_path = modify_file_name(dl_path)
                        new_dl_list.append(new_path)
                        logger.info(f"文件重命名:{new_path}\n")
                        os.rename(dl_path, new_path)
                        # dst_path = os.path.join(src_base_path_book, book_title ,os.path.basename(new_path))
                        # if not hard_link(new_path, dst_path):
                        #     xxxx=1
            if dl_path:
                new_audios = cut(book_title,folder_path_base,folder_path,src_base_path_book,audio_start,audio_end,album)
            else:
                continue
        else:
            logger.info(f"「{book_title}」在喜马拉雅未更新，停止任务")
            continue
            # return True
        logger.info(f"新增音频：{new_audios}")
        xml_path = os.path.join(src_base_path_book, book_title, f'{book_title}.xml')
        audio_path = os.path.join(src_base_path_book, book_title)
        result = podcast_add_main(book_title,audio_path,xml_path,new_audios)
    return result
 
@plugin.task('update_podcast', '「更新播客」', cron_expression='5 8-23 * * *')
def task():
    if update_podcast_config:
        logger.info(f'{plugins_name}定时任务启动，开始同步喜马拉雅并更新播客')
        if xmly_main():
            logger.info(f'{plugins_name}同步喜马拉雅并更新播客完成')
        else:
            logger.info(f'{plugins_name}同步喜马拉雅并更新播客失败')
