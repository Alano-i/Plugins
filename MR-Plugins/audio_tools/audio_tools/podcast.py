import os
import re
import time
import io
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import xml.etree.ElementTree as ET
import mutagen
import logging
import ffmpeg
from .functions import *
from mbot.openapi import mbot_api
from moviebotapi.common import MenuItem
server = mbot_api
logger = logging.getLogger(__name__)
# dst_base_path = "/app/frontend/static/podcast/audio"
# dst_base_path = "/data/plugins/podcast"
# src_base_path = '/Media/有声书'

def get_nickname():
    try:
        user = server.user.get(1)
        nickname = user.nickname
        if nickname:
            return nickname
        else:
            return ''
    except Exception as e:
        logger.error(f"{plugins_name}获取昵称出错，原因：{e}")
        return ''

def podcast_menu():
    try:
        """授权并添加菜单"""
        href = '/common/view?hidePadding=true#/static/podcast/index.html'
        # 授权管理员和普通用户可访问
        # server.auth.add_permission([1, 2], href)
        server.auth.add_permission([1], href)
        # 获取菜单，把我的播客源添加到"影片推荐"菜单分组
        menus = server.common.list_menus()
        menu_list=[]
        for menu in menus:
            if menu.title == '我的':
                for x in menu.pages:
                    menu_list.append(x.title)
                if '播客源' not in menu_list:
                    menu_item = MenuItem()
                    menu_item.title = '播客源'
                    menu_item.href = href
                    menu_item.icon = 'Podcasts'
                    # 放在一个位置
                    # menu.pages.insert(0, menu_item)
                    # 放在最后一个位置
                    menu.pages.append(menu_item)
                    break
        server.common.save_menus(menus)
    except Exception as e:
        logger.error(f"{plugins_name}添加导航菜单出错，原因：{e}")

def podcast_config(config):
    global plugins_name,mbot_url,dst_base_path,pic_url,message_to_uid,channel,src_base_path_music,src_base_path_book
    plugins_name = config.get('plugins_name','')
    mbot_url = config.get('mbot_url','').strip('/')
    src_base_path_book = config.get('src_base_path_book','')
    src_base_path_music = config.get('src_base_path_music','')
    dst_base_path = config.get('dst_base_path','')
    src_base_path_music = process_path(src_base_path_music)
    src_base_path_book = process_path(src_base_path_book)
    pic_url = config.get('pic_url','')
    message_to_uid = config.get('uid','')
    channel = config.get('channel','qywx')
    
def update_xml_url0(file_path,display_title,link,cover_image_url,podcast_author,audio_num,reader,album_id='',sub=False):
    result = True
    try:
        if not os.path.exists(file_path):
            # 文件不存在，初始化一个空的JSON内容
            json_data = {}
            write_json_file(file_path,json_data)
        xmly_url = f"https://www.ximalaya.com/album/{album_id}" if album_id else ''
        # 定义新增的内容
        new_content = {
            display_title: {
                "podcast_url": link,
                "podcast_author": podcast_author,
                "reader": reader,
                "sub": sub,
                "xmly_url": xmly_url,
                "audio_num": audio_num,
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
        result = light_link(file_path,json_dst_path)
    except Exception as e:
        logger.error(f"{plugins_name}保存播客链接到json文件出错，原因：{e}")
        result = False
    return result

def update_xml_url(file_path, display_title, link, cover_image_url, podcast_author, audio_num, reader, album_id='', sub=False):
    reader = format_reader(reader)
    result = True
    try:
        if not os.path.exists(file_path):
            # 文件不存在，初始化一个空的JSON内容
            json_data = {}
            write_json_file(file_path, json_data)
        xmly_url = f"https://www.ximalaya.com/album/{album_id}" if album_id else ''
        # 定义新增的内容
        new_content_details = {
            "podcast_url": link,
            "sub": sub,
            "xmly_url": xmly_url,
            "audio_num": audio_num,
            "cover_url": cover_image_url
        }
        # 读取原始JSON文件内容
        original_data = read_json_file(file_path)

        # 确保每个新的或更新的条目在显示标题、播客作者和阅读器中都位于顶部。
        # 检查display_title是否存在
        if display_title in original_data:
            """
            使用 pop 方法从 original_data 字典中提取与键 display_title 对应的值，并将该值存储在 display_data 变量中。
            同时，pop 方法还会从 original_data 字典中删除 display_title 键及其对应的值。这是为了确保当我们稍后将更新后的 display_title 数据添加回 original_data 时，它会位于字典的顶部。
            """
            display_data = original_data.pop(display_title)

            # 检查podcast_author是否存在
            if podcast_author in display_data:
                author_data = display_data.pop(podcast_author)
                # 如果reader存在，则更新内容
                if reader in author_data:
                    reader_data = author_data.pop(reader)
                    reader_data.update(new_content_details)
                else:
                    reader_data = new_content_details
        
                # 确保更新后的演播者处于顶部
                author_data = {**{reader: reader_data}, **author_data}
                
                display_data = {**{podcast_author: author_data}, **display_data}
            else:
                # display_data[podcast_author] = {reader: new_content_details}
                display_data = {**{podcast_author: {reader: new_content_details}}, **display_data}

            
            original_data = {**{display_title: display_data}, **original_data}
        else:
            # original_data[display_title] = {display_title: {podcast_author: {reader: new_content_details}}}
            original_data = {**{display_title: {podcast_author: {reader: new_content_details}}}, **original_data}
        # 将更新后的内容写回到同一文件中
        write_json_file(file_path, original_data)
        logger.info(f'{file_path} 文件已更新')
        json_dst_path = os.path.join(dst_base_path, 'podcast.json')
        result = light_link(file_path, json_dst_path)
    except Exception as e:
        logger.error(f"{plugins_name}保存播客链接到json文件出错，原因：{e}")
        result = False
    return result

def update_xml_url_add(file_path,display_title,audio_num=None,album_id='',sub=False):
    result = True
    link,podcast_author,reader,cover_image_url = '','','','',
    original_data = {}
    try:
        if os.path.exists(file_path):
            # 读取原始JSON文件内容
            original_data = read_json_file(file_path)
            if display_title in original_data:
                link = original_data.get(display_title, {}).get('podcast_url','')
                podcast_author = original_data.get(display_title, {}).get('podcast_author','')
                reader = original_data.get(display_title, {}).get('reader','')
                cover_image_url = original_data.get(display_title, {}).get('cover_url','')
        
        xmly_url = f"https://www.ximalaya.com/album/{album_id}" if album_id else ''
        
        # 定义新增的内容
        new_content = {
            display_title: {
                "podcast_url": link,
                "podcast_author": podcast_author,
                "reader": reader,
                "sub": sub,
                "xmly_url": xmly_url,
                "audio_num": audio_num,
                "cover_url": cover_image_url
            }
        }
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
        result = light_link(file_path,json_dst_path)
    except Exception as e:
        logger.error(f"{plugins_name}保存播客链接到json文件出错，原因：{e}")
        result = False
    return result

def get_xml_url(json_data, send_sms):
    try:
        if json_data:
            result_list = []
            for key, value in json_data.items():
                result_list.append(f"{key}：{value['podcast_url']}")
                if send_sms:
                    msg_title = f"{key} - 播客源"
                    msg_digest = f"轻点卡片 - 再点右上角 - 在默认浏览器中打开，可快速添加至播客App中。"
                    link_url = value['podcast_url']
                    cover_image_url = value['cover_url']
                    push_msg_to_mbot(msg_title, msg_digest,link_url,cover_image_url)
            result = "\n".join(result_list)
            if result:
                logger.info(f"已生成的有声书播客 RSS URL 如下：\n{result}")
    except Exception as e:
        logger.error(f"{plugins_name}获取播客链接出错，原因：{e}")

def get_filename(audio_file,book_title):
    title_text = os.path.splitext(os.path.basename(audio_file))[0].replace(book_title,"").strip('/')
    title_text = re.sub(r'[《》「」\[\]]', '', title_text).strip()
    return title_text

def get_audio_info(file_path,book_title,short_filename,fill_num):
    org_title,year,authors,duration_formatted,summary,trck_num,reader = '','','','','','',''
    ext = os.path.splitext(file_path)[1].lower()
    try:
        audio = mutagen.File(file_path)
    except Exception as e:
        logger.warning(f"{plugins_name}获取音频 ['{file_path}'] 出错，原因：{e}")
        org_title = os.path.splitext(os.path.basename(file_path))[0]
        return org_title,year,authors,duration_formatted,summary,trck_num,reader
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
                    # 演播者
                    try:
                        reader = audio.tags.getall('TXXX:©nrt')[0].text[0]
                    except Exception as e:
                        reader = ''
                    if not reader:
                        try:
                            reader = audio.tags['TCOM'].text[0]
                        except Exception as e:
                            reader = ''
                    # 音轨序号
                    try:
                        trck_num = audio.tags['TRCK'].text[0]
                        if '/' in trck_num:
                            trck_num = trck_num.split('/')[0]
                    except Exception as e:
                        trck_num = ''
                    # 简介
                    try:
                        # 获取TXXX标签"summary"的值
                        summary = audio.tags.getall('TXXX:summary')[0].text[0]
                    except Exception as e:
                        summary = ''
                    if not summary:
                        try:
                            summary = audio.tags['COMM:简介:chi'].text[0]
                        except Exception as e:
                            summary = ''
                    if not summary:
                        try:
                            summary = audio.tags['COMM::XXX'].text[0]
                        except Exception as e:
                            summary = ''
                    if not summary:
                        try:
                            summary = audio.tags['COMM::eng'].text[0]
                        except Exception as e:
                            summary = ''
            
                if ext == '.m4a' or ext == '.m4b':
                    # 标题
                    org_title = audio.tags.get('©nam', [''])[0]
                    # 年份
                    year = audio.tags.get('©day', [''])[0]
                    # 艺术家
                    authors = audio.tags.get('©ART', [''])[0]
                    # 演播者
                    reader = audio.tags.get('©nrt', [''])[0]
                    if not reader:
                        reader = audio.tags.get('©wrt', [''])[0]
                    # 简介
                    summary = audio.tags.get('summ', [''])[0]
                    if not summary:
                        summary = audio.tags.get('©cmt', [''])[0]
                    # 序号
                    trck_num = audio.tags.get('trkn', [('','')])[0][0]
                if ext == '.flac':
                    org_title = audio.get('title', [''])[0]
                    year = audio.get('date', [''])[0]
                    authors = audio.get('artist', [''])[0]
                    reader = audio.get('composer', [''])[0]
                    summary = audio.get('SUMMARY', [''])[0]
                    if not summary:
                        summary = audio.get('comment', [''])[0]
                    trck_num = audio.get('tracknumber', [''])[0]
                if short_filename:
                    org_title = org_title or os.path.basename(file_path)[0]
                    try:
                        org_title = sortout_filename(org_title,book_title,fill_num)
                    except Exception as e:
                        logger.error(f"{plugins_name}优化文件名 ['{file_path}'] 出错，原因：{e}")
                if not trck_num and org_title:
                    trck_num = extract_number(org_title)
            except Exception as e:
                logger.error(f"{plugins_name}获取音频 ['{file_path}'] 基本信息出错，原因：{e}")
        else:
            org_title = os.path.splitext(os.path.basename(file_path))[0]

    return org_title,year,authors,duration_formatted,summary,trck_num,reader

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
    if episode_num == 0 or not episode_num: episode_num = '1'
    return str(season_num), str(episode_num)

def create_itunes_rss_xml(audio_files, base_url, cover_image_url, podcast_title, podcast_summary, podcast_category, podcast_author,reader,pub_year,audio_path,book_title,podcast_url,is_group,short_filename,fill_num):
    podcast_au,podcast_summ,podcast_reader = '','',''
    podcast_link_url = cover_image_url
    rss = Element('rss', attrib={'xmlns:itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd', 'version': '2.0'})
    if not podcast_author or not podcast_summary:
        try:
            if audio_files:
                aa,bb,podcast_au,cc,podcast_summ,dd,podcast_reader = get_audio_info(audio_files[0],book_title,short_filename,fill_num)
        except Exception as e:
            logger.error(f"{plugins_name}获取第一个文件的信息失败，原因：{e}")
    podcast_author = podcast_author or podcast_au
    podcast_summary = podcast_summary or podcast_summ
    reader = reader or podcast_reader
    reader = format_reader(reader)
    desc_jpg = os.path.join(audio_path, "desc.jpg")
    desc_png = os.path.join(audio_path, "desc.png")
    desc_file = desc_jpg if os.path.exists(desc_jpg) else desc_png
    if os.path.exists(desc_file):
        podcast_link_url = f"{base_url}/{add_path}/{os.path.basename(desc_file)}"
        podcast_link_url = url_encode(podcast_link_url)
    channel = SubElement(rss, 'channel')
    SubElement(channel, 'podcast_url').text = podcast_url
    SubElement(channel, 'title').text = podcast_title
    SubElement(channel, 'reader').text = reader
    SubElement(channel, 'link').text = podcast_link_url
    SubElement(channel, 'language').text = 'zh-cn'
    author_text = f'{podcast_author} · {reader}' if reader else podcast_author
    SubElement(channel, 'itunes:author').text = author_text
    SubElement(channel, 'itunes:summary').text = podcast_summary # 简介
    SubElement(channel, 'itunes:type').text = "serial"
    SubElement(channel, 'itunes:explicit').text = "false"   # 是否存在露骨内容
    SubElement(channel, 'itunes:category', attrib={'text': podcast_category})
    SubElement(channel, 'itunes:image', attrib={'href': cover_image_url}) # 封面
    SubElement(channel, 'description').text = podcast_summary  # 简介
    pub_date = datetime.now()
    for i, audio_file in enumerate(audio_files, start=1):

        org_title,pub_year_in,authors,duration,summary,trck_num,reader_no = get_audio_info(audio_file,book_title,short_filename,fill_num)
        pub_year = pub_year or pub_year_in

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
    return minidom.parseString(tostring(rss)).toprettyxml(indent='    '),podcast_author,reader

def save_cover(input_file,audio_path):
    try:
        cover_art_path = os.path.join(audio_path, 'cover.jpg')
        ffmpeg.input(input_file).output(cover_art_path, map='0:v', f='image2').run(overwrite_output=True)
    except Exception as e:
        pass

def push_msg_to_mbot(msg_title, msg_digest, link_url,cover_image_url):
    nickname = ''
    image_url = cover_image_url if cover_image_url else pic_url
    if "我的播客源" in msg_title:
        nickname = get_nickname()
        msg_title = f'{nickname} 的播客源' if nickname else '我的播客源'
    else:
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

def podcast_main(book_title, audio_path, podcast_summary, podcast_category, podcast_author,reader,pub_year,is_group,short_filename,is_book,album_id='',sub=False):
    global src_base_path,book,add_path
    fill_num = 4
    src_base_path = src_base_path_book if is_book else src_base_path_music
    book = is_book
    if not audio_path:
        logger.info(f"{plugins_name}未设置输入路径，请设置后重试")
        return False
    # podcast_summary,reader = get_local_info(audio_path,podcast_summary,reader)
    base_url = f'{mbot_url}/static/podcast/audio'
    # base_url = f'{mbot_url}/plugins/podcast'
    audio_files,fill_num,audio_num = get_audio_files(audio_path)
    if not audio_files:
        logger.warning(f"{plugins_name}{audio_path} 路径中没有音频文件，跳过生成播客源。")
        return False
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
        if not light_link(cover_file,cover_file_hlink):
            return False
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
    try:
        rss_xml, podcast_author,reader= create_itunes_rss_xml(
            audio_files,
            base_url,
            cover_image_url,
            podcast_title,
            podcast_summary,
            podcast_category,
            podcast_author,
            reader,
            pub_year,
            audio_path,
            book_title,
            link,
            is_group,
            short_filename,
            fill_num
        )
    except Exception as e:
        logger.error(f'{plugins_name}构建 RSS XML内容出错, 原因: {e}')
        return False
    if not write_xml_file(out_file,rss_xml):
        return False
    if not light_link(out_file,out_file_hlink):
        return False
    podcast_json_path = src_base_path_book or src_base_path_music   
    if not update_xml_url(os.path.join(podcast_json_path, 'podcast.json'),display_title,link,cover_image_url,podcast_author,audio_num,reader,album_id,sub):
        return False       
    link_url = link
    logger.info(f"有声书「{book_title}」的播客 RSS URL 链接如下：\n{link_url}")
    msg_title = f"{book_title} - 播客源"
    msg_digest = f"轻点卡片 - 再点右上角 - 在默认浏览器中打开，可快速添加至播客App中。"
    push_msg_to_mbot(msg_title, msg_digest,link_url,cover_image_url)
    create_podcast_flag_file(audio_path)
    return True

def podcast_add_main(book_title,author,reader,book_dir_name,audio_path,xml_path,audio_files,album_id,sub):
    try:
        hlink(audio_path, os.path.join(dst_base_path, book_dir_name))
    except Exception as e:
        logger.warning(f"{plugins_name}['{audio_path}'] -> ['{os.path.join(dst_base_path, book_dir_name)}'] 失败, 原因: {e}")
    if not os.path.exists(xml_path):
        is_group = True
        short_filename = True
        is_book = True
        podcast_author,reader,pub_year,podcast_category,podcast_summary = '','','','',''
        book_title,podcast_author,reader,pub_year,podcast_category,podcast_summary = get_audio_info_all(audio_path,book_title,podcast_author,reader,pub_year,podcast_category,podcast_summary)
        state = podcast_main(book_title, audio_path, podcast_summary, podcast_category, podcast_author,reader,pub_year,is_group,short_filename,is_book,album_id,sub)
        return state

    global book
    book = True
    is_group = True
    short_filename = True
    fill_num = 3
    # 从文件中读取XML内容
    with io.open(xml_path, 'r') as file:
        xml_content = file.read()
    xml_content=xml_content.replace('    ','').replace('\n','')
    # 解析 XML 内容
    root = ET.fromstring(xml_content)
    # 注册命名空间前缀
    ET.register_namespace('itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
    # 更新根元素的属性
    # root.attrib = {'xmlns:itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd', 'version': '2.0'}
    channel = root.find('channel')
    base_url = f'{mbot_url}/static/podcast/audio'
    pub_date = datetime.now()
    if not channel: return False
    for i, audio_file in enumerate(audio_files, start=1):
        audio_file = audio_file.replace('/tmp','')
        # 创建新的 <item> 元素
        item = SubElement(channel, 'item')
        org_title,pub_year_in,authors,duration,summary,trck_num,reader_no = get_audio_info(audio_file,book_title,short_filename,fill_num)
        pub_year = pub_year_in
        season_num, episode_num = get_season_episode(trck_num,is_group)
        if not org_title:
            title_text = get_filename(audio_file,book_title)
        else:
            title_text = org_title
        SubElement(item, 'itunes:episodeType').text = "full"  # 完整的内容，可选trailer:预告  bonus:类似特别篇
        SubElement(item, 'itunes:season').text = season_num  # 季编号
        SubElement(item, 'itunes:episode').text = episode_num    # 集编号
        SubElement(item, 'title').text = title_text    # 集标题
        """
        /Media/downloads/有声书/阴阳刺青师-墨大先生-头陀渊/tmp/阴阳刺青师 第783集 大汉龙钱.m4a
        audio_path = '/Media/有声书/阴阳刺青师-墨大先生-头陀渊'
        """
        src_base_path = src_base_path_book if book else src_base_path_music
        # audio_url_m = f'{base_url}{audio_path.replace(src_base_path,"")}{audio_file.replace(audio_path,"")}'
        audio_url_m = f"{base_url.strip('/')}/{audio_path.replace(src_base_path,'').strip('/')}/{audio_file.replace(audio_path,'').strip('/')}"
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
        pub_date += timedelta(minutes=1)
    modified_xml_content = minidom.parseString(ET.tostring(root, encoding='utf-8')).toprettyxml(indent='    ')
    if not write_xml_file(xml_path,modified_xml_content):
        return False
    else:
        aa,bb,audio_num = get_audio_files(audio_path)
        if book_title and audio_num:
            try:
                json_file_path = os.path.join(src_base_path_book, 'podcast.json')
                # 读取原始JSON文件内容
                js_data = read_json_file(json_file_path)
                link = js_data[book_title][author][reader].get("podcast_url", "")
                cover_image_url = js_data[book_title][author][reader].get("cover_url", "")
                result = update_xml_url(json_file_path, book_title, link, cover_image_url, author, audio_num, reader, album_id, sub)
            except Exception as e:
                logger.error(f'{plugins_name}更新 podcast.json 文件失败, 原因: {e}')
                result = False
            if result: create_podcast_flag_file(audio_path)
            return result
        return True