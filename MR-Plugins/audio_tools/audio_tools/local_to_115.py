import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

ET.register_namespace('itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')

# 有声书源文件夹和目标文件夹路径
# src_root = '/Volumes/影音视界/有声书'
# dst_root = '/Users/alano/Downloads/提取有声书115'

# 是否跳过开关
skip_exists = False

# # 替换的源URL
# src_url = 'https://mr.xxx.com:88'
# # 替换的目标URL，115中的路径
# dst_url = 'https://podcast.xxx.com'
# dst_mbot_url = 'https://mbot.xxx.com'
# dst_path = '/影音视界/有声书'
# dst_115_url = f'{dst_url}{dst_path}'


def lacal_to_115_config(config):
    global plugins_name,src_url, dst_url,dst_mbot_url,dst_path,dst_115_url,dst_root,src_root
    plugins_name = config.get('plugins_name','')
    src_url = config.get('src_url','')
    dst_url = config.get('dst_url','')
    dst_mbot_url = config.get('dst_mbot_url','')
    dst_path = config.get('dst_path','')
    dst_root = config.get('dst_root','')
    src_root = config.get('src_root','')
    dst_115_url = f'{dst_url}{dst_path}' if dst_url and dst_path else ''


# 提取有声书文件夹中的 XML 文件和图片
def extract_files(src_dir, dst_dir, path=''):
    # 遍历源文件夹中的所有文件和子文件夹
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            # 文件名完全匹配"cover.jpg"
            # if file.endswith('.xml') or file == 'cover.jpg' or file == 'desc.jpg' or file == 'desc.png' or file == 'cover.png':
            if file == 'cover.jpg' or file == 'desc.jpg' or file == 'desc.png' or file == 'cover.png':
            # if file == 'desc.jpg':
                # 计算源文件的完整路径
                src_file = os.path.join(root, file)
                
                # 计算目标文件夹的路径，保持源文件夹结构
                relative_path = os.path.relpath(root, src_dir)
                middle_path = Path(src_dir).name if path else ''
                # dst_subfolder = os.path.join(dst_dir, middle_path, relative_path)
                if relative_path == ".":
                    dst_subfolder = os.path.join(dst_dir, middle_path)
                else:
                    dst_subfolder = os.path.join(dst_dir, middle_path, relative_path)
                
                # 如果目标文件夹不存在，创建它
                if not os.path.exists(dst_subfolder):
                    os.makedirs(dst_subfolder)
                
                # 计算目标文件的完整路径
                dst_file = os.path.join(dst_subfolder, file)
                
                # 将文件复制到目标文件夹
                shutil.copy(src_file, dst_file)
                logger.info(f"复制文件: {src_file} 到 {dst_file}")

def process_xml_file(src_path, dst_path):
    tree = ET.parse(src_path)
    root = tree.getroot()
    channel = root.find('channel')

    # 处理 podcast_url, link
    for tag in ['podcast_url', 'link']:
        elem = channel.find(tag)
        if elem is not None and elem.text and src_url in elem.text:
            elem.text = elem.text.replace(src_url, dst_mbot_url)

    # 处理 itunes:image
    image_elem = channel.find('{http://www.itunes.com/dtds/podcast-1.0.dtd}image')
    if image_elem is not None and 'href' in image_elem.attrib:
        if src_url in image_elem.attrib['href']:
            image_elem.attrib['href'] = image_elem.attrib['href'].replace(src_url, dst_mbot_url)

    # 处理 item 下的 enclosure, guid
    for item in channel.findall('item'):
        enclosure = item.find('enclosure')
        if enclosure is not None and 'url' in enclosure.attrib:
            if f'{src_url}/static/podcast/audio' in enclosure.attrib['url']:
                enclosure.attrib['url'] = enclosure.attrib['url'].replace(f'{src_url}/static/podcast/audio',dst_115_url)
        guid = item.find('guid')
        if guid is not None and guid.text and f'{src_url}/static/podcast/audio' in guid.text:
            guid.text = guid.text.replace(f'{src_url}/static/podcast/audio',dst_115_url)

    # 确保目标目录存在
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    tree.write(dst_path, encoding='utf-8', xml_declaration=True)

# 遍历源文件夹，处理每个 XML 文件
def walk_and_process(src_dir, path):
    for root_dir, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.xml'):
                src_path = os.path.join(root_dir, file)
                rel_path = os.path.relpath(src_path, src_dir)
                middle_path = Path(src_dir).name if path else ''
                dst_path = os.path.join(dst_root, middle_path,rel_path,)
                # 如果目标文件已存在且跳过开关为真，则跳过处理
                if os.path.exists(dst_path) and skip_exists:
                    logger.info(f'已存在，跳过: {dst_path}')
                    continue
                process_xml_file(src_path, dst_path)
                logger.info(f'已处理: {src_path} -> {dst_path}')

# 替换 podcast.json 中的 URL
def replace_podcast_url(src_root):
    json_path = os.path.join(src_root, 'podcast.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        content = f.read()
    new_content = content.replace(src_url, dst_mbot_url)
    new_json_path = os.path.join(dst_root, 'podcast.json')
    with open(new_json_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

def local_to_115(path=''):
    src_dir = path if path else src_root
    extract_files(src_dir, dst_root, path)
    walk_and_process(src_dir, path)
    replace_podcast_url(src_root)
    return True

# if __name__ == '__main__':
#     local_to_115()