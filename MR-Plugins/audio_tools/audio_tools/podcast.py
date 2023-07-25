import os
import re
import json
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import mutagen
from datetime import timedelta
import logging
import ffmpeg
from urllib.parse import quote
from mbot.openapi import mbot_api
server = mbot_api
logger = logging.getLogger(__name__)
# dst_base_path = "/app/frontend/static/podcast/audio"
plugins_name = '「有声书工具箱」'

def podcast_config(config,path):
    global mbot_url,dst_base_path,pic_url,message_to_uid,src_base_path,channel
    mbot_url = config.get('mbot_url','')
    src_base_path = config.get('src_base_path','')
    dst_base_path = path
    pic_url = config.get('pic_url','')
    message_to_uid = config.get('uid','')
    channel = config.get('channel','qywx')

def url_encode(url):
    return quote(url, safe='/:.')

def create_hard_link(src_path,dst_path):
    if os.path.exists(dst_path) or os.path.islink(dst_path):
        os.remove(dst_path) # 如果目标文件已经存在，删除它
    # os.link(src_path, dst_path) # 创建硬链接
    os.symlink(src_path, dst_path) # 创建软链接
    # shutil.copyfile(src_path, dst_path) # 复制文件

def update_xml_url(file_path,display_title,link):
    try:
        # 判断文件是否存在
        if not os.path.exists(file_path):
            # 文件不存在，初始化一个空的JSON内容
            json_data = {}
            with open(file_path, "w") as file:
                json.dump(json_data, file, indent=4, ensure_ascii=False)
        # 定义新增的内容
        new_content = {
            display_title: link
        }
        # 读取原始JSON文件内容
        try:
            with open(file_path, "r") as file:
                original_data = json.load(file)
        except Exception as e:
            original_data = {}
        # 合并新增内容到原始内容
        original_data.update(new_content)
        # 将更新后的内容写回到同一文件中
        with open(file_path, "w") as file:
            json.dump(original_data, file, indent=4, ensure_ascii=False)
        logger.info(f'{file_path} 文件已更新')
    except Exception as e:
        logger.error(f"保存播客链接到json文件出错，原因：{e}")

def get_xml_url():
    file_path = f"{src_base_path}/podcast.json"
    # 判断文件是否存在
    if not os.path.exists(file_path):
        logger.error(f"保存播客链接的json文件不存在，可能还从未生成！")
    # 读取原始JSON文件内容
    try:
        with open(file_path, "r") as file:
            original_data = json.load(file)
        if original_data:
            result = "\n".join([f"{key}：{value}" for key, value in original_data.items()])
            if result:
                logger.info(f"已生成的有声书播客 RSS URL 如下：\n{result}")
    except Exception as e:
        logger.error(f"保存播客链接到json文件出错，原因：{e}")

def get_audio_info(file_path):
    org_title = ''
    year = ''
    authors = ''
    duration_formatted = ''
    try:
        ext = os.path.splitext(file_path)[1].lower()
        audio = mutagen.File(file_path)
        if audio:
            # 时长
            duration = int(audio.info.length)
            duration_formatted = str(timedelta(seconds=duration))
            if ext == '.mp3':
                # 读取原音频标题
                if 'TIT2' in audio.tags:
                    org_title = audio.tags['TIT2'].text[0]
                else:
                    org_title = ''
                # 年份
                if 'TDRC' in audio.tags:
                    year = audio.tags['TDRC'].text[0]
                else:
                    year = ''
                # 艺术家
                if 'TPE1' in audio.tags:
                    authors = audio.tags['TPE1'].text[0]
                else:
                    authors = ''
                # 简介
                if 'TXXX:summary' in audio.tags:
                    # 获取TXXX标签"summary"的值
                    summary = audio.tags.getall('TXXX:summary')[0].text[0]
                else:
                    authors = ''
            if ext == '.m4a':
                # 标题
                org_title = audio.tags.get('©nam', [''])[0]
                # 年份
                year = audio.tags.get('©day', [''])[0]
                # 艺术家
                authors = audio.tags.get('©ART', [''])[0]
                # 简介
                summary = audio.tags.get('summ', [''])[0]
            if ext == '.flac':
                org_title = audio.get('title', [''])[0]
                year = audio.get('date', [''])[0]
                authors = audio.get('artist', [''])[0]
                summary = audio.get('SUMMARY', [''])[0]
    except Exception as e:
        logger.error(f"获取音频基本信息出错，原因：{e}")
    return org_title,year,authors,duration_formatted,summary

def get_audio_files(directory):
    audio_extensions = ['.mp3', '.m4a', '.flac']
    audio_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if os.path.splitext(file)[1].lower() in audio_extensions:
                audio_files.append(os.path.join(root, file))
    return sorted(audio_files, key=lambda x: os.path.basename(x))  # 升序 01 02 03
    # return sorted(audio_files, key=lambda x: os.path.basename(x), reverse=True)  # 降序 03 02 01

def create_itunes_rss_xml(audio_files_batch, base_url, cover_image_url, podcast_title, podcast_summary, podcast_category, podcast_author, index_range,audio_path,book_title,podcast_url):
    rss = Element('rss', attrib={'xmlns:itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd', 'version': '2.0'})
    if not podcast_author or not podcast_summary:
        aa,bb,podcast_au,cc,podcast_summ = get_audio_info(audio_files_batch[0])
    podcast_author = podcast_author or podcast_au
    podcast_summary = podcast_summary or podcast_summ

    channel = SubElement(rss, 'channel')
    SubElement(channel, 'podcast_url').text = podcast_url
    SubElement(channel, 'title').text = podcast_title
    # SubElement(channel, 'link').text = "https://www.apple.com.cn/apple-podcasts/"
    SubElement(channel, 'link').text = cover_image_url
    SubElement(channel, 'language').text = 'zh-cn'
    SubElement(channel, 'itunes:summary').text = podcast_summary
    SubElement(channel, 'itunes:category', attrib={'text': podcast_category})
    SubElement(channel, 'itunes:author').text = podcast_author
    # Use itunes:image instead of image
    SubElement(channel, 'itunes:image', attrib={'href': cover_image_url})
    SubElement(channel, 'description').text = podcast_summary  # Set description as well
    pub_date = datetime.now()
    # xxxx = pub_date.strftime('%a, %d %b %Y %H:%M:%S GMT')
    for i, audio_file in enumerate(audio_files_batch, start=index_range[0]):
        org_title,pub_year,authors,duration,summary = get_audio_info(audio_file)
        item = SubElement(channel, 'item')
        if not org_title:
            title_text = os.path.splitext(os.path.basename(audio_file))[0].replace(book_title,"")
            title_text = re.sub(r'[《》「」\[\]]', '', title_text).strip()
        else:
            title_text = org_title
        SubElement(item, 'title').text = title_text
        audio_url_m = f'{base_url}{audio_path.replace(src_base_path,"")}{audio_file.replace(audio_path,"")}'
        audio_url = url_encode(audio_url_m)
        SubElement(item, 'enclosure', attrib={'url': audio_url, 'type': 'audio/mpeg'})
        SubElement(item, 'guid').text = audio_url_m
        if pub_year:
            try:
                pub_year = int(str(pub_year))
            except Exception as e:
                pass
            if isinstance(pub_year, int) and len(str(pub_year)) == 4:
                pub_date = pub_date.replace(year=int(pub_year))
        SubElement(item, 'pubDate').text = pub_date.strftime('%a, %d %b %Y %H:%M:%S GMT')
        SubElement(item, 'itunes:duration').text = duration  # Replace with actual duration if available
        pub_date += timedelta(minutes=1)
    return minidom.parseString(tostring(rss)).toprettyxml(indent='    ')

def save_cover(input_file,audio_path):
    try:
        cover_art_path = os.path.join(audio_path, 'cover.jpg')
        ffmpeg.input(input_file).output(cover_art_path, map='0:v', f='image2').run(overwrite_output=True)
    except Exception as e:
        pass

def save_cover_back(filename,audio_path):
    try:
        exts = ['.m4a', '.mp3']
        file_name, file_ext = os.path.splitext(filename)
        file_ext = file_ext.lower()
        # 判断是否为音频文件
        if file_ext in exts:
            # 构造输入文件和输出文件的路径
            cover_art_path = os.path.join(audio_path, 'cover.jpg')
            cover_audio = mutagen.File(filename)
            if file_ext == '.m4a':
                # # 获取封面数据
                if 'covr' in cover_audio:
                    cover_data = cover_audio['covr'][0]
                    # 将封面存到本地
                    with open(cover_art_path, 'wb') as f:
                        f.write(bytes(cover_data))
            elif file_ext == '.mp3':
                for key, value in cover_audio.tags.items():
                    if 'APIC:' in key:
                        cover_data = value.data
                        # 将封面存到本地
                        with open(cover_art_path, 'wb') as f:
                            f.write(bytes(cover_data))
                        break
    except Exception as e:
        logger.error(f"保存有声书封面失败，原因：{e}")

def push_msg_to_mbot(msg_title, msg_digest, link_url,cover_image_url):
    image_url = cover_image_url if cover_image_url else pic_url
    msg_data = {
        'title': msg_title,
        'a': msg_digest,
        'pic_url': image_url,
        'link_url': link_url,
    }
    try:
        if message_to_uid:
            for _ in message_to_uid:
                server.notify.send_message_by_tmpl('{{title}}', '{{a}}', msg_data, to_uid=_, to_channel_name = channel)
        else:
            server.notify.send_message_by_tmpl('{{title}}', '{{a}}', msg_data)
        if msg_title:
            logger.info(f'{plugins_name}已推送消息')
        return
    except Exception as e:
        logger.error(f'{plugins_name}推送消息异常, 原因: {e}')

def podcast_main(book_title, audio_path, podcast_summary, podcast_category, podcast_author,is_group):
    base_url = f'{mbot_url}/static/podcast/audio'
    audio_files = get_audio_files(audio_path)
    cover_file = os.path.join(audio_path, "cover.jpg")
    if audio_files and not os.path.exists(cover_file): save_cover(audio_files[0],audio_path)
    if os.path.exists(cover_file):
        # audio_path = '/Media/音乐/有声书/ABC/DEF'
        # src_base_path = '/Media/音乐/有声书'
        add_path = audio_path.replace(src_base_path,'')
        cover_file_hlink = f"{dst_base_path}{add_path}/cover.jpg"
        create_hard_link(cover_file,cover_file_hlink)
        cover_image_url = f"{base_url}{add_path}/cover.jpg"
    else:
        cover_image_url = ''
    cover_image_url = url_encode(cover_image_url)
    if is_group:
        batch_size = 100
        num_batches = (len(audio_files) + batch_size - 1) // batch_size
    else:
        batch_size = len(audio_files)
        num_batches = 1
    link_group = []
    for batch_num in range(num_batches):
        start_index = batch_num * batch_size
        end_index = start_index + batch_size
        audio_files_batch = audio_files[start_index:end_index]
        index_range = (start_index + 1, min(start_index + batch_size, len(audio_files)))
        if is_group:
            podcast_title = f'{book_title} {index_range[0]}-{index_range[1]}'
        else:
            podcast_title = f'{book_title}'
        # rss_xml = create_itunes_rss_xml(
        #     audio_files_batch,
        #     base_url,
        #     cover_image_url,
        #     podcast_title,
        #     podcast_summary,
        #     podcast_category,
        #     podcast_author,
        #     index_range,
        #     audio_path,
        #     book_title,
        #     podcast_url
        # )
        """
        dst_base_path = "/app/frontend/static/podcast/audio"
        audio_path = "/Media/音乐/有声书/三国"
        """
        if is_group:
            out_file = f'{audio_path}/{book_title} {index_range[0]}-{index_range[1]}.xml'
            display_title = f"{book_title} {index_range[0]}-{index_range[1]}"
        else:
            out_file = f'{audio_path}/{book_title}.xml'
            display_title = book_title
        # with open(out_file, 'w', encoding='utf-8') as f:
        #     f.write(rss_xml)
        file_name = os.path.basename(out_file)
        out_file_hlink = f"{dst_base_path}/{add_path}/{file_name}"
        link = f"{base_url}/{add_path}/{file_name}"
        link = url_encode(link)
        rss_xml = create_itunes_rss_xml(
            audio_files_batch,
            base_url,
            cover_image_url,
            podcast_title,
            podcast_summary,
            podcast_category,
            podcast_author,
            index_range,
            audio_path,
            book_title,
            link
        )
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(rss_xml)
        create_hard_link(out_file,out_file_hlink)
        update_xml_url(f"{src_base_path}/podcast.json",display_title,link)
        link_group.append(link)
    link_url = '\n'.join(link_group)
    logger.info(f"有声书「{book_title}」的播客 RSS URL 链接如下：\n{link_url}")
    msg_title = f"{book_title} - 已生成播客源URL"
    msg_digest = link_url
    push_msg_to_mbot(msg_title, msg_digest,link_url,cover_image_url)
