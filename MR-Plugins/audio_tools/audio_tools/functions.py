import os
import json
import re
import shutil
import io
from urllib.parse import quote
from cn2an import cn2an
import time
from datetime import datetime
import requests
from pypinyin import lazy_pinyin
import logging
import xml.etree.ElementTree as ET
logger = logging.getLogger(__name__)

plugins_name = '「有声书工具箱」'
# 将大写的集改为数字
def convert_chinese_numbers(text,fill_num):
    """
    输入：xxx 第五百二十三集 xxx 输出：xxx 第0523集 xxx
    """
    pattern = r'第\s*([0-9一二三四五六七八九十零百千万]+)\s*(集|章|回)(?:\s*(.+))?'
    match = re.search(pattern, text)
    if match:
        num = match.group(1)
        if not num.isdigit():
            num = str(cn2an(num))
            num = str(int(num)).zfill(fill_num)
        chapter = match.group(3)
        if chapter:
            chapter = chapter.strip()
        else:
            chapter = ''
        new_text = f"第{num}集 {chapter}".strip()
        return new_text
    return text

def convert_num(text,fill_num):
    # 使用正则表达式提取数字部分和剩余文本部分
    """
    输入：第68集 轮月 输出：0068 轮月
    """
    match = re.search(r'第\s*(\d+)\s*(集|章|回)\s*(.+)', text)
    if match:
        number = str(int(match.group(1))).zfill(fill_num)
        rest_of_string = match.group(3)
        result = number + " " + rest_of_string
        return result
    else:
        return text
    
def is_valid_format(text,fill_num):
    # pattern = r'^第\s*(\d+)\s*集$'
    """
    输入：三国 第068集 输出：第0068集
    """
    pattern = r'.*第\s*(\d+)\s*集$'
    match = re.match(pattern, text)
    
    if match:
        number = str(int(match.group(1))).zfill(fill_num)
        return True, f'第{number}集'
    else:
        return False, text

def add_space(text,fill_num):
    """
    输入：0068轮月 输出：0068 轮月
    """
    match = re.search(r'(\d+)(.+)', text)
    if match:
        number = str(int(match.group(1))).zfill(fill_num)
        rest_of_string = match.group(2).strip()
        if rest_of_string.startswith(("-", "_")):
            rest_of_string = rest_of_string.lstrip("-_").strip()

            result = number + " " + rest_of_string            
        else:
            result = number + " " + rest_of_string

        return result
    return text

def extract_number(text):
    """
    输入：0068 0067 轮月 输出：68
    """
    # 使用正则表达式匹配数字
    match = re.search(r'\d+', text)
    if match:
        # 提取第一个匹配到的数字并转换为整数
        number = int(match.group())
        return number
    else:
        return ''
    
def get_book_name(text):
    # 使用正则表达式匹配书名
    pattern = r"^([\u4e00-\u9fa5]+[\w\s·]+)"
    match = re.search(pattern, text)
    if match:
        new_text = match.group(0).strip()
        return new_text
    else:
        return ''

# 处理文件名规范为 0236 xxxx 或者 第0236集 格式
def sortout_filename(filename,series,fill_num):
    fill_num = int(fill_num)
    """
    传入文件路径，filename = '/a/file.mp3'
    """
    # 获取文件名（不带后缀）
    filename_text = os.path.splitext(filename)[0]
    filename_text_ori = filename_text
    # 去掉文件名中的书名，只保留当前音频的名称
    if series:
        filename_text = filename_text.replace(series, '').strip()
        filename_text = filename_text.replace('《》', '').strip()
        filename_text = filename_text.replace('  ', ' ').strip()
    try:
        if filename_text.isdigit():
            filename_text = f'第{filename_text.zfill(fill_num)}集'
        else:
            filename_text = convert_chinese_numbers(filename_text,fill_num)
            filename_text = convert_num(filename_text,fill_num)
            need_flag, filename_text = is_valid_format(filename_text,fill_num)
            if not need_flag:
                filename_text = add_space(filename_text,fill_num)
        # if filename_text:
        #     trck_num = extract_number(filename_text)
    except Exception as e:
        logger.error(f"{plugins_name}处理 ['{filename_text_ori}'] 文件名时出错了: {e}")
        filename_text = filename_text_ori
    return filename_text

# filename = '第02回暂避画舫10.m4a'
# series = '茶馆'
# xxx = sortout_filename(filename,series,2)
# ss=1

def url_encode(url):
    return quote(url, safe='/:.')

def write_json_file(file_path, json_data):
    for i in range(3):
        try:
            with io.open(file_path, 'w', encoding='utf-8') as fp:
                json.dump(json_data, fp, ensure_ascii=False, indent=4)
            break
        except Exception as e:
            logger.error(f'{plugins_name}{i+1}/3 次写入新json数据到文件出错，原因: {e}')
            time.sleep(3)
            continue

def write_xml_file(file_path,xml_data):
    result = False
    for i in range(3):
        try:
            with io.open(file_path, 'w', encoding='utf-8') as fp:
                fp.write(xml_data)
            result = True
            break
        except Exception as e:
            logger.error(f'{plugins_name}{i+1}/3 次写入新xml数据到文件出错，原因: {e}')
            time.sleep(3)
            result = False
    return result
    
def read_json_file(file_path):
    json_data = {}
    for i in range(3):
        try:
            with io.open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            break
        except Exception as e:
            logger.error(f'{plugins_name}{i+1}/3 次读取json文件出错，原因: {e}')
            time.sleep(3)
            continue
    return json_data

def read_txt_file(file_path):
    txt_data = ''
    for i in range(3):
        try:
            with io.open(file_path, 'r', encoding='utf-8') as f:
                txt_data = f.read().strip()
            break
        except Exception as e:
            logger.error(f"{plugins_name}{i+1}/3 次读取 ['{file_path}'] 文件出错，原因: {e}")
            time.sleep(3)
            continue
    return txt_data

#完成文件夹的复制和合并，目标中有同名的会覆盖，没有就复制过去
def merge_folders(src, dest):
    for item in os.listdir(src):
        src_item = os.path.join(src, item)
        dest_item = os.path.join(dest, item)

        if os.path.isdir(src_item):
            if os.path.exists(dest_item):
                if os.path.isdir(dest_item):
                    merge_folders(src_item, dest_item)
                else:
                    os.remove(dest_item)
                    shutil.copytree(src_item, dest_item, copy_function=os.link)
            else:
                shutil.copytree(src_item, dest_item, copy_function=os.link)
        else:
            if os.path.exists(dest_item):
                os.remove(dest_item)
            # shutil.copy2(src_item, dest_item)
            os.link(src_item, dest_item)  # 创建硬链接

def merge_folders_copy_only(src, dest):
    for item in os.listdir(src):
        src_item = os.path.join(src, item)
        dest_item = os.path.join(dest, item)

        if os.path.isdir(src_item):
            if os.path.exists(dest_item):
                if os.path.isdir(dest_item):
                    merge_folders_copy_only(src_item, dest_item)
                else:
                    os.remove(dest_item)
                    shutil.copytree(src_item, dest_item)
            else:
                shutil.copytree(src_item, dest_item)
        else:
            if os.path.exists(dest_item):
                os.remove(dest_item)
            shutil.copy2(src_item, dest_item)

def merge_folders_copy_del(src, dest):
    for item in os.listdir(src):
        src_item = os.path.join(src, item)
        dest_item = os.path.join(dest, item)

        if os.path.isdir(src_item):
            if os.path.exists(dest_item):
                if os.path.isdir(dest_item):
                    merge_folders_copy_del(src_item, dest_item)
                else:
                    os.remove(dest_item)
                    move_dir_with_copy_del(src_item, dest_item)
            else:
                move_dir_with_copy_del(src_item, dest_item)
        else:
            if os.path.exists(dest_item):
                os.remove(dest_item)
            shutil.copy2(src_item, dest_item) 

# 硬链接，将整个目录树（包括所有子目录和文件）从 src 硬链接到 dst，如果已存在则先删除
def hard_link(src, dst):
    work_flag = True
    try:
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)  # 删除目标目录
            shutil.copytree(src, dst, copy_function=os.link)
        elif os.path.isfile(src): # 处理文件的情况
            if os.path.exists(dst):
                os.remove(dst)  # 删除目标文件
            os.link(src, dst)  # 创建硬链接
    except Exception as e:
        if os.path.isfile(src):
            logger.error(f"{plugins_name}硬链接 ['{src}'] -> ['{dst}'] 出错，跳过, 原因：{e}")
        else:
            logger.error(f"{plugins_name}硬链接 ['{src}'] -> ['{dst}'] 出错，跳过")
        work_flag = False
    return work_flag

# 软链接，递归地复制目录，包括所有子目录和文件，并创建软链接
def light_link(src, dst):
    result = True
    try:
        if os.path.isdir(src):
            os.makedirs(dst, exist_ok=True)  # 创建目标目录
            for entry in os.listdir(src):
                src_entry = os.path.join(src, entry)
                dst_entry = os.path.join(dst, entry)
                light_link(src_entry, dst_entry)
        elif os.path.isfile(src):  # 处理文件的情况
            if os.path.lexists(dst):  # 如果目标文件已存在，则先删除
                os.remove(dst)
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)  # 创建目标目录
            os.symlink(src, dst)  # 创建软链接
    except Exception as e:
        logger.error(f"{plugins_name}软链接 ['{src}'] -> ['{dst}'] 出错，原因: {e}")
        result = False
    return result



def hlink(src_base_path, dst_base_path):
    result = light_link(src_base_path, dst_base_path)
    logger.info(f"{plugins_name}已完成 ['{src_base_path}'] -> ['{dst_base_path}'] 链接")
    return result

def get_fill_num(num):
    fill_num = 2 if num < 100 else 3 if num < 1000 else 4
    return fill_num

 # 将字符串转换为拼音表示
def pinyin_sort_key(s):
    return ''.join(lazy_pinyin(s))

def get_num(text):
    number = ''
    match = re.search(r'第\s?(\d+)\s?[集章回]', text)
    if match:
        number = int(match.group(1).strip())
    else:
        match_f = re.search(r'\d+', text)
        if match_f:
            number = int(match_f.group(0).strip())  # Changed here
    return number

def get_audio_files(directory):
    # 获取文件夹及其子文件夹中的所有音频文件
    audio_extensions = ['.mp3', '.m4a', '.flac', '.m4b']
    audio_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if os.path.splitext(file)[1].lower() in audio_extensions:
                audio_files.append(os.path.join(root, file))
    audio_num = len(audio_files)
    fill_num = get_fill_num(audio_num)
    # 排序
    sorted_audio_files = sorted(audio_files, key=lambda x: pinyin_sort_key(os.path.basename(x)))
    return sorted_audio_files,fill_num,audio_num  # 升序 01 02 03
    # return sorted(audio_files, key=lambda x: os.path.basename(x), reverse=True)  # 降序 03 02 01

def process_path(path):
    path = path.strip()
    path = f"/{path.strip('/')}" if path else path
    return path

def get_state(config):
    return bool(config and config.lower() != 'off')

def extract_file_or_folder_path(path):
    first_path, _ = os.path.split(path)
    if os.path.isdir(path):  # 判断路径是否是一个目录
        return first_path,path  # 如果是目录，则直接返回该路径
    elif os.path.isfile(path):
        return first_path,os.path.dirname(path)  # 如果是文件，则提取其所在文件夹的路径

def format_reader(reader):
    return reader.strip().strip(',,').strip(',').replace("演播","").replace("主播","").replace("领衔","").replace("/","&").replace("、","&").replace("，","&").replace(" ,","&").replace(", ","&").replace(",,","&").replace(",","&").replace(" , ","&").replace("//","&").replace("&&","&").replace("丶","&").replace("& ","&").replace(" & ","&").replace(" &","&").strip()

def get_bookname_and_author(save_path_name):
    # pattern = r'^(.+?)[\.\-\s*]+(.+?)[\.\-\s*]+'
    pattern = r'^(.+?)[\.\-\s*_]+(.+?)[\.\-\s*_]+(.+?)(?:[\.\-\s*_]+(.+?))?$'
    match = re.search(pattern, save_path_name)
    if match:
        book_title = match.group(1).strip()
        podcast_author = match.group(2).strip()
        reader = match.group(3)
        reader = format_reader(reader)
        return book_title, podcast_author,reader
    else:
        return '', '',''
    
def fetch_xml_data(url):
    xml_data = ''
    for retry_count in range(3):
        try:
            response = requests.get(url, timeout=10)  # 设置超时时间为10秒
            response.raise_for_status()  # 如果请求不成功，会引发异常
            xml_data = response.text
            break
        except requests.exceptions.RequestException as e:
            logger.error(f"\n第 {retry_count+1}/3 次获取 {url} 出错:\n原因: {e}")
            time.sleep(1)
            continue
    return xml_data

def update_json(data):
    try:
        # 遍历 JSON 数据
        for key, value in data.items():
            podcast_url = value['podcast_url']
            # 获取 XML 数据
            xml_data = fetch_xml_data(podcast_url)
            if xml_data:
                try:
                    root = ET.fromstring(xml_data)
                    podcast_author = root.find('.//{http://www.itunes.com/dtds/podcast-1.0.dtd}author')
                    if podcast_author:
                        podcast_author = podcast_author.text
                    else:
                        podcast_author = ''
                    audio_num = len(root.findall('.//item'))
                    # 更新 JSON 数据
                    value['podcast_author'] = podcast_author
                    value['audio_num'] = audio_num
                except Exception as e:
                    logger.error(f"{key} - 解析出错，原因: {e}")
                    time.sleep(1)
                    continue
        return data
    except Exception as e:
        logger.error(f"出错，原因: {e}")
        return ''

def get_local_info(audio_path,podcast_summary,reader):
    desc_path = os.path.join(audio_path, "desc.txt")
    reader_path = os.path.join(audio_path, "reader.txt")
    if not podcast_summary and os.path.exists(desc_path):
        podcast_summary = read_txt_file(desc_path)
    if not reader and os.path.exists(reader_path):
        reader = read_txt_file(reader_path)
    return podcast_summary,reader

def read_abs_file(audio_path):
    abs_path = os.path.join(audio_path, 'metadata.abs')
    title,authors,reader,publishedYear,genres,description = '','','','','',''
    try:
        with io.open(abs_path, 'r', encoding='utf-8') as file:
            metadata = file.read()
    except Exception as e:
        metadata= ''
        # logger.error(f"读取metadata.abs出错：{e}")
    if metadata:
        try:
            title = metadata.split("title=")[1].split("\n")[0].strip()
        except Exception as e:
            pass
        try:
            authors = metadata.split("authors=")[1].split("\n")[0].strip()
        except Exception as e:
            pass
        try:
            reader = metadata.split("narrators=")[1].split("\n")[0].strip()
        except Exception as e:
            pass
        try:
            publishedYear = int(metadata.split("publishedYear=")[1].split("\n")[0].strip())
        except Exception as e:
            pass
        try:
            genres = metadata.split("genres=")[1].split("\n")[0].strip()
            if genres:
                genres = genres.replace("Audiobook, ", "").replace("Audiobook,", "").replace("Audiobook", "").strip(",").strip()
        except Exception as e:
            pass
        try:
            description_start = metadata.find("[DESCRIPTION]")
            chapter_start = metadata.find("[CHAPTER]", description_start)
            if chapter_start != -1:  # 如果存在[CHAPTER]
                description_end = chapter_start
            else:  # 如果不存在[CHAPTER]
                description_end = len(metadata)
            description = metadata[description_start:description_end].replace("[DESCRIPTION]", "").strip()
            # description = metadata[description_start + len("[DESCRIPTION]"):].strip()
        except Exception as e:
            pass
    try:
        description,reader = get_local_info(audio_path,description,reader)
    except Exception as e:
        pass
    title_dir, authors_dir, reader_dir = '','',''
    if not title or not authors or '.' in title or '-' in title:
        title_dir, authors_dir, reader_dir = get_bookname_and_author(os.path.basename(audio_path))
    title = title_dir or title
    authors = authors_dir or authors
    reader = reader_dir or reader
    return title,authors,reader,publishedYear,genres,description

def get_audio_info_all(audio_path,book_title,podcast_author,reader,pub_year,podcast_category,podcast_summary):

    title_abs,authors_abs,reader_abs,publishedYear_abs,genres_abs,description_abs = read_abs_file(audio_path)
    book_title = book_title or title_abs
    podcast_author = podcast_author or authors_abs
    reader = reader or reader_abs
    pub_year = str(pub_year or publishedYear_abs)
    podcast_category = podcast_category or genres_abs
    podcast_summary = podcast_summary or description_abs
    return book_title,podcast_author,reader,pub_year,podcast_category,podcast_summary


def move_dir_with_copy_del(src_dir, dst_dir):
    """
    Move a directory by copying its contents to the destination and then deleting the source.
    """
    try:
        # Copy the entire directory
        shutil.copytree(src_dir, dst_dir)
        # Remove the original directory
        shutil.rmtree(src_dir)
    except Exception as e:
        logger.error(f"{plugins_name}将 [{src_dir}] -> [{dst_dir}] 先复制再删除失败，原因：{e}")
    

# 格式化连续的数字
def format_sorted_list(nums):
    if not nums:
        return ""

    # 首先，对列表进行排序
    nums.sort()

    # 用于保存结果范围的列表
    ranges = []

    # 从第一个数字开始
    start = nums[0]
    end = nums[0]

    for num in nums[1:]:
        # 如果当前数字正好是序列中的下一个
        if num == end + 1:
            end = num
        else:
            # 如果有范围，将范围添加到结果列表中，否则只添加数字
            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")
            # 设置新的起始和结束
            start = end = num

    # 处理最后的范围或数字
    if start == end:
        ranges.append(str(start))
    else:
        ranges.append(f"{start}-{end}")

    return ','.join(ranges)
    
# 生成有声书目录名
def get_book_dir_name(book_title, authors, reader):
    author_text = f" - {authors}" if authors else ' - 未知作者'
    reader_text = f" - {reader}" if reader else ' - 未知演播者'
    book_dir_name = f"{book_title}{author_text}{reader_text}"
    return book_dir_name

# 生成处理标识文件
def create_podcast_flag_file(audio_path):
    try:
        if os.path.exists(audio_path):
            # 获取当前时间并格式化为指定格式
            current_time = datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
            # 创建空的UTF-8编码文本文件
            podcast_file = os.path.join(audio_path, 'podcast.txt')
            with open(podcast_file, 'w', encoding='utf-8') as file:
                file.write(f'看到该文件，表示此文件夹已生成播客源\n\n{current_time}')
        else:
            logger.error(f"{plugins_name} 目录 {audio_path} 不存在，跳过生成已处理标识文件")
    except Exception as e:
        logger.error(f"{plugins_name} 生成已处理标识文件失败，原因：{e}")


