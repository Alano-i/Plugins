import os
import re
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import mutagen
from datetime import timedelta
import logging
import ffmpeg
from .functions import *
from mbot.openapi import mbot_api
server = mbot_api
logger = logging.getLogger(__name__)
# dst_base_path = "/app/frontend/static/podcast/audio"
# dst_base_path = "/data/plugins/podcast"
# src_base_path = '/Media/有声书'

def podcast_config(config):
    global plugins_name,mbot_url,src_base_path,dst_base_path,pic_url,message_to_uid,channel,src_base_path_music,src_base_path_book
    plugins_name = config.get('plugins_name','')
    mbot_url = config.get('mbot_url','')
    src_base_path_book = config.get('src_base_path_book','')
    src_base_path_music = config.get('src_base_path_music','')
    dst_base_path = config.get('dst_base_path','')
    pic_url = config.get('pic_url','')
    message_to_uid = config.get('uid','')
    channel = config.get('channel','qywx')
    

def update_xml_url(file_path,display_title,link,cover_image_url):
    try:
        if not os.path.exists(file_path):
            # 文件不存在，初始化一个空的JSON内容
            json_data = {}
            write_json_file(file_path,json_data)
        # 定义新增的内容
        new_content = {
            display_title: {
                "podcast_url": link,
                "cover_url": cover_image_url
            }
        }
        # 读取原始JSON文件内容
        original_data = read_json_file(file_path)
        # # 合并新增内容到原始内容
        # original_data.update(new_content)
        # 如果原内容中已经存在相同的键(display_title)，则更新内容
        if display_title in original_data:
            original_data[display_title].update(new_content[display_title])
        else:
            original_data.update(new_content)
        # 将新内容放在最前面
        updated_data = {**new_content, **original_data}
        # 将更新后的内容写回到同一文件中
        write_json_file(file_path,updated_data)
        logger.info(f'{file_path} 文件已更新')
        json_dst_path = os.path.join(dst_base_path, 'podcast.json')
        light_link(file_path,json_dst_path)
    except Exception as e:
        logger.error(f"保存播客链接到json文件出错，原因：{e}")

def get_xml_url(json_data, send_sms):
    try:
        if json_data:
            result_list = []
            for key, value in json_data.items():
                result_list.append(f"{key}：{value['podcast_url']}")
                if send_sms:
                    msg_title = f"{key} - 播客源URL"
                    msg_digest = f"轻点卡片 - 再点右上角 - 在默认浏览器中打开，可快速添加至播客App中。"
                    link_url = value['podcast_url']
                    cover_image_url = value['cover_url']
                    push_msg_to_mbot(msg_title, msg_digest,link_url,cover_image_url)
            result = "\n".join(result_list)
            if result:
                logger.info(f"已生成的有声书播客 RSS URL 如下：\n{result}")
    except Exception as e:
        logger.error(f"获取播客链接出错，原因：{e}")

def get_filename(audio_file,book_title):
    title_text = os.path.splitext(os.path.basename(audio_file))[0].replace(book_title,"").strip('/')
    title_text = re.sub(r'[《》「」\[\]]', '', title_text).strip()
    return title_text

def get_audio_info(file_path,book_title,short_filename,fill_num):
    org_title = ''
    year = ''
    authors = ''
    duration_formatted = ''
    summary = ''
    trck_num = ''
    ext = os.path.splitext(file_path)[1].lower()
    try:
        audio = mutagen.File(file_path)
    except Exception as e:
        logger.warning(f"{plugins_name}获取音频 ['{file_path}'] 出错，原因：{e}")
        org_title = os.path.splitext(os.path.basename(file_path))[0]
        return org_title,year,authors,duration_formatted,summary,trck_num
    if audio:
        # 时长
        duration = int(audio.info.length)
        duration_formatted = str(timedelta(seconds=duration))
        if book:
            try:
                if ext == '.mp3':
                    # 读取原音频标题
                    try:
                        org_title = audio.tags['TIT2'].text[0]
                    except Exception as e:
                        org_title = ''
                    # 年份
                    try:
                        year = audio.tags['TDRC'].text[0]
                    except Exception as e:
                        year = ''
                    # 艺术家
                    try:
                        authors = audio.tags['TPE1'].text[0]
                    except Exception as e:
                        authors = ''
                    # 音轨序号
                    try:
                        trck_num = audio.tags['TRCK'].text[0]
                        if '/' in trck_num:
                            trck_num = trck_num.split('/')[0]
                    except Exception as e:
                        trck_num = ''
                    # 简介
                    # if 'TXXX:summary' in audio.tags:
                    try:
                        # 获取TXXX标签"summary"的值
                        summary = audio.tags.getall('TXXX:summary')[0].text[0]
                    except Exception as e:
                        summary = ''
                if ext == '.m4a' or ext == '.m4b':
                    # 标题
                    org_title = audio.tags.get('©nam', [''])[0]
                    # 年份
                    year = audio.tags.get('©day', [''])[0]
                    # 艺术家
                    authors = audio.tags.get('©ART', [''])[0]
                    # 简介
                    summary = audio.tags.get('summ', [''])[0]
                    trck_num = audio.tags.get('trkn', [('','')])[0][0]
                if ext == '.flac':
                    org_title = audio.get('title', [''])[0]
                    year = audio.get('date', [''])[0]
                    authors = audio.get('artist', [''])[0]
                    summary = audio.get('SUMMARY', [''])[0]
                    trck_num = audio.get('tracknumber', [''])[0]
                if short_filename:
                    org_title = sortout_filename(os.path.basename(file_path),book_title,fill_num)
                    if not trck_num:
                        trck_num = extract_number(org_title)
            except Exception as e:
                logger.error(f"{plugins_name}获取音频 ['{file_path}'] 基本信息出错，原因：{e}")
        else:
            org_title = os.path.splitext(os.path.basename(file_path))[0]

    return org_title,year,authors,duration_formatted,summary,trck_num

def get_season_episode(trck_num,is_group):
    season_num = ''
    episode_num = ''
    if trck_num:
        try:
            trck_num = int(trck_num)
        except Exception as e:
            trck_num = 0
        if is_group:
            season_num = max(((trck_num - 1) // 100),0)
        else:
            season_num = max(((trck_num - 1) // 100+1),0)
        episode_num = trck_num
    if season_num == 0 or not season_num: season_num = '1'
    if episode_num == 0: episode_num = ''
    return str(season_num), str(episode_num)

def create_itunes_rss_xml(audio_files, base_url, cover_image_url, podcast_title, podcast_summary, podcast_category, podcast_author,audio_path,book_title,podcast_url,is_group,short_filename,fill_num):
    rss = Element('rss', attrib={'xmlns:itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd', 'version': '2.0'})
    if not podcast_author or not podcast_summary:
        try:
            if audio_files:
                aa,bb,podcast_au,cc,podcast_summ,dd = get_audio_info(audio_files[0],book_title,short_filename,fill_num)
        except Exception as e:
            logger.error(f"{plugins_name}获取第一个文件的信息失败，原因：{e}")
    podcast_author = podcast_author or podcast_au
    podcast_summary = podcast_summary or podcast_summ
    channel = SubElement(rss, 'channel')
    SubElement(channel, 'podcast_url').text = podcast_url
    SubElement(channel, 'title').text = podcast_title
    SubElement(channel, 'link').text = cover_image_url
    SubElement(channel, 'language').text = 'zh-cn'
    SubElement(channel, 'itunes:author').text = podcast_author
    SubElement(channel, 'itunes:summary').text = podcast_summary # 简介
    SubElement(channel, 'itunes:type').text = "serial"
    SubElement(channel, 'itunes:explicit').text = "false"   # 是否存在露骨内容
    SubElement(channel, 'itunes:category', attrib={'text': podcast_category})
    SubElement(channel, 'itunes:image', attrib={'href': cover_image_url}) # 封面
    SubElement(channel, 'description').text = podcast_summary  # 简介
    pub_date = datetime.now()
    for i, audio_file in enumerate(audio_files, start=1):

        org_title,pub_year,authors,duration,summary,trck_num = get_audio_info(audio_file,book_title,short_filename,fill_num)
        if not book: trck_num = i
        season_num, episode_num = get_season_episode(trck_num,is_group)
        item = SubElement(channel, 'item')
        if not org_title:
            title_text = get_filename(audio_file,book_title)
        else:
            title_text = org_title
        SubElement(item, 'itunes:episodeType').text = "full"  # 完整的内容，可选trailer:预告  bonus:类似特别篇
        SubElement(item, 'itunes:season').text = season_num  # 季编号
        SubElement(item, 'itunes:episode').text = episode_num    # 集编号
        SubElement(item, 'title').text = title_text    # 集标题
        audio_url_m = f'{base_url}{audio_path.replace(src_base_path,"")}{audio_file.replace(audio_path,"")}'
        audio_url = url_encode(audio_url_m)
        SubElement(item, 'enclosure', attrib={'url': audio_url, 'type': 'audio/mpeg'})   # 指向音频文件的url
        SubElement(item, 'guid').text = audio_url_m    # 全局唯一标识符
        if pub_year:
            try:
                pub_year = int(str(pub_year))
            except Exception as e:
                pub_year = ''
            if isinstance(pub_year, int) and len(str(pub_year)) == 4:
                pub_date = pub_date.replace(year=int(pub_year))
        SubElement(item, 'pubDate').text = pub_date.strftime('%a, %d %b %Y %H:%M:%S GMT+8')
        SubElement(item, 'itunes:duration').text = duration  # Replace with actual duration if available
        SubElement(item, 'itunes:explicit').text = 'false'  # 是否存在露骨内容
        # pub_date += timedelta(minutes=1)
        pub_date += timedelta(seconds=1)
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
        logger.error(f"{plugins_name}保存有声书 ['{filename}'] 封面失败，原因：{e}")

def push_msg_to_mbot(msg_title, msg_digest, link_url,cover_image_url):
    image_url = cover_image_url if cover_image_url else pic_url
    link_url = f"podcast:{link_url}" if link_url else ''
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

def podcast_main(book_title, audio_path, podcast_summary, podcast_category, podcast_author,is_group,short_filename,is_book):
    global src_base_path,book
    src_base_path = src_base_path_book if is_book else src_base_path_music
    book = is_book
    if not audio_path:
        logger.info(f"{plugins_name}未设置输入路径，请设置后重试")
        return False
    base_url = f'{mbot_url}/static/podcast/audio'
    # base_url = f'{mbot_url}/plugins/podcast'
    audio_files,fill_num = get_audio_files(audio_path)
    cover_file_jpg = os.path.join(audio_path, "cover.jpg")
    cover_file_png = os.path.join(audio_path, "cover.png")
    cover_file = cover_file_png if os.path.exists(cover_file_png) else cover_file_jpg
    if audio_files and not os.path.exists(cover_file): save_cover(audio_files[0],audio_path)
    # audio_path = '/Media/有声书/ABC/DEF'
    # src_base_path = '/Media/有声书'
    add_path = audio_path.replace(src_base_path,'').strip('/') # ABC/DEF
    if os.path.exists(cover_file):
        cover_file_hlink = f"{dst_base_path}/{add_path}/{os.path.basename(cover_file)}"
        time.sleep(2)
        light_link(cover_file,cover_file_hlink)
        cover_image_url = f"{base_url}/{add_path}/{os.path.basename(cover_file)}"
    else:
        cover_image_url = ''
    cover_image_url = url_encode(cover_image_url)
    podcast_title = book_title
    out_file = f'{audio_path}/{book_title}.xml'
    display_title = book_title
    file_name = os.path.basename(out_file).strip('/')
    out_file_hlink = f"{dst_base_path}/{add_path}/{file_name}"
    link = f"{base_url}/{add_path}/{file_name}"
    link = url_encode(link)
    rss_xml = create_itunes_rss_xml(
        audio_files,
        base_url,
        cover_image_url,
        podcast_title,
        podcast_summary,
        podcast_category,
        podcast_author,
        audio_path,
        book_title,
        link,
        is_group,
        short_filename,
        fill_num
    )
    write_xml_file(out_file,rss_xml)
    light_link(out_file,out_file_hlink)
    podcast_json_path = src_base_path_book or src_base_path_music   
    update_xml_url(os.path.join(podcast_json_path, 'podcast.json'),display_title,link,cover_image_url)        
    link_url = link
    logger.info(f"有声书「{book_title}」的播客 RSS URL 链接如下：\n{link_url}")
    msg_title = f"{book_title} - 播客源URL"
    # msg_digest = f"{link_url}\n\n轻点卡片 - 再点右上角 - 在默认浏览器中打开，可快速添加至播客App中。"
    msg_digest = f"轻点卡片 - 再点右上角 - 在默认浏览器中打开，可快速添加至播客App中。"
    push_msg_to_mbot(msg_title, msg_digest,link_url,cover_image_url)
    return True
