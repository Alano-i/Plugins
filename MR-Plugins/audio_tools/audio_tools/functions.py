import os
import json
import re
import io
from urllib.parse import quote
from cn2an import cn2an
import time
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

def create_hard_link(src_path,dst_path):
    if os.path.exists(dst_path) or os.path.islink(dst_path):
        os.remove(dst_path) # 如果目标文件已经存在，删除它
    # os.link(src_path, dst_path) # 创建硬链接
    os.symlink(src_path, dst_path) # 创建软链接
    # shutil.copyfile(src_path, dst_path) # 复制文件

def hlink(src_base_path, dst_base_path):
    try:
        one = True
        for root, dirs, files in os.walk(src_base_path):
            for file_name in files:
                src_file_path = os.path.join(root, file_name)
                dst_file_path = os.path.join(dst_base_path, os.path.relpath(src_file_path, src_base_path))
                dst_dir_path = os.path.dirname(dst_file_path)
                if not os.path.exists(dst_dir_path):
                    os.makedirs(dst_dir_path)
                if os.path.isfile(src_file_path):
                    if os.path.exists(dst_file_path) or os.path.islink(dst_file_path):
                        os.remove(dst_file_path) # 如果目标文件已经存在，删除它
                    os.symlink(src_file_path, dst_file_path)
                    # shutil.copyfile(src_file_path, dst_file_path)
            for dir_name in dirs:
                src_dir_path = os.path.join(root, dir_name)
                dst_dir_path = os.path.join(dst_base_path, os.path.relpath(src_dir_path, src_base_path))
                if not os.path.exists(dst_dir_path):
                    os.makedirs(dst_dir_path)
                one = False
                hlink(src_dir_path, dst_dir_path)
        # if one:
        #     logger.info(f'{plugins_name}WEB 素材已软链接到容器')
    except Exception as e:
        logger.error(f'{plugins_name}将有声书素材已软链接到容器出错，原因: {e}')
def get_fill_num(num):
    fill_num = 2 if num < 100 else 3 if num < 1000 else 4
    return fill_num

def get_audio_files(directory):
    # 获取文件夹及其子文件夹中的所有音频文件
    audio_extensions = ['.mp3', '.m4a', '.flac']
    audio_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if os.path.splitext(file)[1].lower() in audio_extensions:
                audio_files.append(os.path.join(root, file))
    audio_num = len(audio_files)
    fill_num = get_fill_num(audio_num)
    return sorted(audio_files, key=lambda x: os.path.basename(x)),fill_num  # 升序 01 02 03
    # return sorted(audio_files, key=lambda x: os.path.basename(x), reverse=True)  # 降序 03 02 01

def process_path(path):
    path = f"/{path.strip('/')}" if path else path
    return path

def get_state(config):
    return bool(config and config.lower() != 'off')
