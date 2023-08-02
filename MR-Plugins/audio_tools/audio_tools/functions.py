import os
import json
import re
import shutil
import io
from urllib.parse import quote
from cn2an import cn2an
import time
from pypinyin import lazy_pinyin
import logging
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

# filename = '陈坤 - 重生.flac'
# series = '音乐'
# xxx = sortout_filename(filename,series,2)

def url_encode(url):
    return quote(url, safe='/:.')

def write_json_file(file_path, json_data):
    for i in range(3):
        try:
            with io.open(file_path, 'w', encoding='utf-8') as fp:
                json.dump(json_data, fp, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f'{plugins_name}{i+1}/3 次写入新json数据到文件出错，原因: {e}')
            time.sleep(3)
            continue

def write_xml_file(file_path,xml_data):
    for i in range(3):
        try:
            with io.open(file_path, 'w', encoding='utf-8') as fp:
                fp.write(xml_data)
        except Exception as e:
            logger.error(f'{plugins_name}{i+1}/3 次写入新xml数据到文件出错，原因: {e}')
            time.sleep(3)
            continue
def read_json_file(file_path):
    json_data = {}
    for i in range(3):
        try:
            # 打开原始 JSON 文件
            with io.open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
        except Exception as e:
            logger.error(f'{plugins_name}{i+1}/3 次读取json文件出错，原因: {e}')
            time.sleep(3)
            continue
    return json_data


# 硬链接，将整个目录树（包括所有子目录和文件）从 src 硬链接到 dst，如果已存在则先删除
def hard_link(src, dst):
    try:
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)  # 删除目标目录
            shutil.copytree(src, dst, copy_function=os.link)
        elif os.path.isfile(src):  # 使用 "elif" 来处理文件的情况
            if os.path.exists(dst):
                os.remove(dst)  # 删除目标文件
            os.link(src, dst)  # 创建硬链接
    except Exception as e:
        logger.error(f"{plugins_name}硬链接 ['{src}'] -> ['{dst}'] 出错")

# 软链接，递归地复制目录，包括所有子目录和文件，并创建软链接
def light_link(src, dst):
    try:
        if os.path.isdir(src):
            os.makedirs(dst, exist_ok=True)  # 创建目标目录
            for entry in os.listdir(src):
                src_entry = os.path.join(src, entry)
                dst_entry = os.path.join(dst, entry)
                light_link(src_entry, dst_entry)
        elif os.path.isfile(src):  # 使用 "elif" 来处理文件的情况
            if os.path.lexists(dst):  # 如果目标文件已存在，则先删除
                os.remove(dst)
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)  # 创建目标目录
            os.symlink(src, dst)  # 创建软链接
    except Exception as e:
        logger.error(f"{plugins_name}软链接 ['{src}'] -> ['{dst}'] 出错，原因: {e}")

def hlink(src_base_path, dst_base_path):
    light_link(src_base_path, dst_base_path)
    logger.info(f"{plugins_name}已完成 ['{src_base_path}'] -> ['{dst_base_path}'] 链接")

def get_fill_num(num):
    fill_num = 2 if num < 100 else 3 if num < 1000 else 4
    return fill_num

 # 定义一个函数，将字符串转换为拼音表示
def pinyin_sort_key(s):
    return ''.join(lazy_pinyin(s))  

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
    return sorted_audio_files,fill_num  # 升序 01 02 03
    # return sorted(audio_files, key=lambda x: os.path.basename(x), reverse=True)  # 降序 03 02 01

def process_path(path):
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

def get_bookname_and_author(save_path_name):
    pattern = r'^(.+?)[\.\-\s*]+(.+?)[\.\-\s*]+'
    # 使用正则表达式匹配书名和播客作者
    match = re.search(pattern, save_path_name)
    if match:
        book_title = match.group(1).strip()
        podcast_author = match.group(2).strip()
        # narrators = match.group(3).strip().replace("演播","").strip()
        return book_title, podcast_author
    else:
        return '', ''
