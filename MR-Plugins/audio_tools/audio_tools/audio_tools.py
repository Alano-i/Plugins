#!/usr/bin/env python3
import os
import re
from cn2an import cn2an
import mutagen
from mutagen.id3 import ID3, APIC
from mutagen.mp4 import MP4, MP4Cover
from mutagen.flac import Picture
from mbot.core.plugins import plugin
from mbot.core.plugins import PluginContext, PluginMeta
from mbot.openapi import mbot_api
from typing import Dict, Any
import threading
import time
import ffmpeg
from urllib.parse import quote
import datetime
import logging
import shutil
from .functions import *
logger = logging.getLogger(__name__)
server = mbot_api
# plugins_name = '「有声书工具箱」'
# plugins_path = '/data/plugins/audio_clip'
# src_base_path = "/Media/有声书"
# dst_base_path = f"/app/frontend/static/podcast/audio"
# dst_base_path = f"/data/plugins/podcast"
# exts = ['.m4a', '.mp3', '.flac', '.wav']

def audio_tools_config(config):
    global plugins_name,mbot_url,pic_url,message_to_uid,src_base_path,channel,dst_base_path,exts
    plugins_name = config.get('plugins_name','')
    mbot_url = config.get('mbot_url','').strip('/')
    pic_url = config.get('pic_url','')
    message_to_uid = config.get('uid','')
    src_base_path = config.get('src_base_path_book','')
    src_base_path = process_path(src_base_path)
    channel = config.get('channel','qywx')

    logger.info(f'{plugins_name}已切换通知通道至「{channel}」')
    if not message_to_uid:
        logger.error(f'{plugins_name}获取推送用户失败, 可能是设置了没保存成功或者还未设置')
    
    dst_base_path = config.get('dst_base_path','')
    exts = config.get('exts','')

def add_cover(output_file,cover_image_path):
    file_name, file_ext = os.path.splitext(output_file)
    file_ext = file_ext.lower()
    if file_ext not in exts:
        return
    # 读取音频文件
    src_audio = mutagen.File(output_file)
    # 判断音频格式是MP3
    if isinstance(src_audio, mutagen.mp3.MP3):
        # 删除旧封面
        if 'APIC:' in src_audio:
            del src_audio.tags['APIC:']
        # 打开图片文件
        with open(cover_image_path, 'rb') as cover_image:
            # 创建APIC标签，将图片数据作为封面写入音频文件
            apic = APIC(
                encoding=3,  # 3表示UTF-8编码
                mime='image/jpeg',  # 图片格式，这里假设是JPEG格式，如果是其他格式请修改
                type=3,  # 3表示封面
                desc=u'Cover',  # 描述
                data=cover_image.read()  # 图片数据
            )
            # 将APIC标签添加到音频文件的metadata中
            src_audio.tags.add(apic)
            # 保存修改后的音频文件
            src_audio.save()
    # 判断音频格式是M4A
    elif isinstance(src_audio, mutagen.mp4.MP4):
        # 删除旧封面
        if 'covr' in src_audio:
            del src_audio['covr']
        # 打开图片文件
        with open(cover_image_path, 'rb') as cover_image:
            # 创建MP4Cover对象，将图片数据作为封面写入音频文件
            cover = MP4Cover(cover_image.read(), imageformat=MP4Cover.FORMAT_JPEG)
            # 将封面数据添加到音频文件的metadata中
            src_audio['covr'] = [cover]
            # 保存修改后的音频文件
            src_audio.save()

    # 判断音频格式是FLAC
    elif isinstance(src_audio, mutagen.flac.FLAC):
        # 删除旧封面
        if 'pictures' in src_audio:
            del src_audio['pictures']
        # 打开图片文件
        with open(cover_image_path, 'rb') as cover_image:
            # 创建Picture对象，将图片数据作为封面写入音频文件
            pic = Picture()
            pic.type = 3  # 3表示封面
            pic.desc = 'Cover'  # 描述
            pic.mime = 'image/jpeg'  # 图片格式，这里假设是JPEG格式，如果是其他格式请修改
            pic.data = cover_image.read()  # 图片数据
            # 将Picture对象添加到音频文件的metadata中
            src_audio.add_picture(pic)
            # 保存修改后的音频文件
            src_audio.save()

def save_cover(input_file,cover_file):
    try:
        ffmpeg.input(input_file).output(cover_file, map='0:v', f='image2').run(overwrite_output=True)
    except Exception as e:
        pass

def audio_cut(input_file, output_file,audio_start,audio_end):
    # 获取总时长
    probe = ffmpeg.probe(input_file)
    duration = float(probe['format']['duration'])
    # 重新定位开始时间和结束时间
    audio_start_seconds = min(float(audio_start), duration)
    audio_end_seconds = max(duration - float(audio_end) - float(audio_start), 0)
    ffmpeg.input(input_file, ss=audio_start_seconds, t=audio_end_seconds).output(output_file, c='copy').run(overwrite_output=True)

def thread_audio_clip(filenames_group, input_dir, cliped_folder, audio_start, audio_end, clip_configs, authors, year, reader, series, summary, album, art_album, group_now, use_filename, subject,fill_num):
    global local_has_cover
    files_num = len(filenames_group)
    for i, filename in enumerate(filenames_group):
        try:
            percent_num = round(((i+1)/files_num)*100, 1)
            clip_percent = f"{percent_num}%"
            if clip_percent == '100.0%':
                logger.info(f"{plugins_name}开始剪辑 {group_now} 分组第 {i+1} 个文件：['{filename}']，已完成 100%，这是当前分组需要处理的最后一个文件")
            else:
                now_video_count = int(files_num - i - 1)
                if datetime.now().second % 5 == 0 or i==0:
                    logger.info(f"{plugins_name}开始剪辑 {group_now} 分组第 {i+1} 个文件：['{filename}']，已完成 {clip_percent}，当前分组剩余 {now_video_count} 个文件需要处理")
            file_name, file_ext = os.path.splitext(filename)
            file_ext = file_ext.lower()
            # 判断是否为音频文件
            if file_ext in exts:
                # 构造输入文件和输出文件的路径
                input_file = os.path.join(input_dir, filename)
                output_file = os.path.join(input_dir, cliped_folder, filename)
                # command = f'ffmpeg -i "{input_file}" -ss {audio_start} -to $(echo "$(ffprobe -i "{input_file}" -show_entries format=duration -v quiet -of csv="p=0")-{audio_end}" | bc) -c copy -map_metadata 0 "{output_file}" -y'
                # os.system(command)
                audio_cut(input_file, output_file,audio_start,audio_end)

                # 若本地不存在cover.jpg,则保存音频中的封面
                cliped_folder_dir = os.path.join(input_dir, cliped_folder)
                cover_art_path = os.path.join(cliped_folder_dir, 'cover.jpg')
                if not os.path.exists(cover_art_path):
                    save_cover(input_file,cover_art_path)
                if local_has_cover:
                    add_cover(output_file,cover_art_path)

########################################################################################################################

                # cover_audio = mutagen.File(input_file)
                # src_audio = mutagen.File(output_file)
                # if file_ext == '.m4a':
                #     # # 获取封面数据
                #     if 'covr' in cover_audio:
                #         cover_data = cover_audio['covr'][0]
                #         # 创建封面对象
                #         cover = MP4Cover(cover_data)
                #         # 添加封面对象到tags中
                #         src_audio.tags['covr'] = [cover]
                #         src_audio.save()
                #         # 将封面存到本地
                #         if not os.path.exists(cover_art_path) and not local_has_cover:
                #             with open(cover_art_path, 'wb') as f:
                #                 f.write(bytes(cover_data))
                #             local_has_cover = True
                #         else:
                #             local_has_cover = True
                # elif file_ext == '.mp3':
                #     for key, value in cover_audio.tags.items():
                #         if 'APIC:' in key:
                #             cover_data = value.data
                #             src_audio.tags.add(value)
                #             src_audio.save()
                #             # 将封面存到本地
                #             if not os.path.exists(cover_art_path) and not local_has_cover:
                #                 with open(cover_art_path, 'wb') as f:
                #                     f.write(bytes(cover_data))
                #                 local_has_cover = True
                #             else:
                #                 local_has_cover = True
                #             break
                # elif file_ext == '.flac':
                #     if 'metadata_block_picture' in cover_audio.tags:
                #         cover_data = cover_audio.tags['metadata_block_picture'][0]
                #         # 将原始文件中的图片块复制到目标文件中
                #         src_audio.tags['metadata_block_picture'] = cover_data
                #         src_audio.save()

################################################################################################################
                if clip_configs == 'clip_and_move':
                    thread_move_to_dir(cliped_folder_dir,filename,authors,year,reader,series,summary,album,art_album,use_filename,subject,fill_num)
        except Exception as e:
            logger.error(f"{plugins_name}['{filename}'] 剪辑失败，原因：{e}")
            return

def audio_clip(input_dir, output_dir, cliped_folder, audio_start, audio_end,clip_configs,authors,year,reader,series,summary,album,art_album,use_filename,subject,xmly_dl):
    # cliped_folder_dir = f'{input_dir}/{cliped_folder}'
    cliped_folder_dir = os.path.join(input_dir, cliped_folder)
    audio_end = int(audio_end)
    # 创建输出目录
    os.makedirs(os.path.join(input_dir, cliped_folder), exist_ok=True)
    global local_has_cover
    local_has_cover = False
    # 遍历输入目录中的所有文件
    filenames = os.listdir(input_dir)
    for filename in filenames:
        if filename.lower() == 'cover.jpg' or filename.lower() == 'cover.png' or filename.lower() == 'desc.jpg' or filename.lower() == 'desc.png':
            local_has_cover = True
            # 构建源文件和目标文件的路径
            src_cover_path = os.path.join(input_dir, filename)
            dst_cover_path = os.path.join(cliped_folder_dir, filename)
            try:
                # 复制文件
                shutil.copy(src_cover_path, dst_cover_path)
                # hard_link(src_cover_path, dst_cover_path)
                # shutil.copyfile(src_cover_path, dst_cover_path)
            except Exception as e:
                logger.error(f"{plugins_name}本地有封面，但复制 ['{filename}'] 到 ['{cliped_folder_dir}'] 失败，原因：{e}")
            break
    filenames_num = len(filenames)
    fill_num = get_fill_num(filenames_num)

    threading_num = 1
    if filenames_num >= 50:
        threading_num = 10
    elif filenames_num >= 30:
        threading_num = 5
    # 每个进程处理文件数量
    threading_clip_num = int(filenames_num/threading_num)
    # 将视频名称序列分成 threading_clip_num 个一组的列表
    filenames_groups = [filenames[mnx:mnx+threading_clip_num] for mnx in range(0, filenames_num, threading_clip_num)]
    all_group_num = len(filenames_groups)
    logger.info(f"{plugins_name} 启动 {all_group_num} 个线程执行剪辑任务，每 5 秒打印一次进度")
    threads = []  
    for group_num, filenames_group in enumerate(filenames_groups):
        # group_num 从0开始递增
        group_now = f"{group_num+1}/{all_group_num}"
        logger.warning(f"{plugins_name}开始剪辑第 {group_now} 个分组")
        # 多线程
        thread = threading.Thread(target=thread_audio_clip, args=(filenames_group, input_dir, cliped_folder, audio_start, audio_end, clip_configs, authors, year, reader, series, summary, album, art_album, group_now, use_filename, subject,fill_num))
        thread.start()
        threads.append(thread)
        time.sleep(1)
    # 等待所有线程执行完毕
    for t in threads:
        t.join()
    logger.info(f"{plugins_name}所有 {all_group_num} 个分组已全部剪辑完成")

    # try:
    #     if os.path.normcase(os.path.abspath(input_dir)) != os.path.normcase(os.path.abspath(output_dir)):
    #         if xmly_dl:
    #             os.makedirs(os.path.join(output_dir, series), exist_ok=True)  # 确保 /Media/有声书/书名 文件夹存在，若不存在则新建
    #             merge_folders(cliped_folder_dir,os.path.join(output_dir, series))
    #         else:
    #             os.makedirs(output_dir, exist_ok=True)
    #             # 将 cliped_folder_dir 目录移动到 output_dir 下面
    #             shutil.move(cliped_folder_dir, output_dir)
    # except Exception as e:
    #     logger.error(f"{plugins_name}移动到 [{output_dir}] 失败，原因：{e}")
    #     return False
    try:
        if os.path.normcase(os.path.abspath(input_dir)) != os.path.normcase(os.path.abspath(output_dir)):
            if xmly_dl:
                author_text = f" - {authors}" if authors else ' - 未知作者'
                reader_text = f" - {reader}" if reader else ' - 未知演播者'
                book_dir_name = f"{series}{author_text}{reader_text}"

                os.makedirs(os.path.join(output_dir, book_dir_name), exist_ok=True)  # 确保 /Media/有声书/书名 文件夹存在，若不存在则新建
                try:
                    merge_folders(cliped_folder_dir, os.path.join(output_dir, book_dir_name))
                except Exception as e:
                    logger.warning(f"{plugins_name}硬链接到 [{output_dir}] 失败,将尝试复制过去，以覆盖的方式运行，具体原因：{e}")
                    merge_folders_copy_only(cliped_folder_dir, os.path.join(output_dir, book_dir_name))
            else:
                try:
                    # 将 cliped_folder_dir 目录移动到 output_dir 下面
                    os.makedirs(output_dir, exist_ok=True)
                    shutil.move(cliped_folder_dir, output_dir)
                except Exception as e:
                    logger.warning(f"{plugins_name}移动到 [{output_dir}] 失败,将尝试复制再删除原文件夹，以覆盖的方式运行，具体原因：{e}")
                    move_dir_with_copy_del(cliped_folder_dir, os.path.join(output_dir, os.path.basename(cliped_folder_dir)))
    except Exception as e:
        logger.error(f"{plugins_name}移动到 [{output_dir}] 失败，原因：{e}")
        return False


    try:
        cover_image_path = os.path.join(output_dir, cliped_folder,'cover.jpg')
        cover_image_path_hlink = f"{dst_base_path}/{series}_cover.jpg"
        light_link(cover_image_path,cover_image_path_hlink)
        if os.path.exists(cover_image_path_hlink):
            cover_image_url = f'{mbot_url}/static/podcast/audio/{series}_cover.jpg'
            # cover_image_url = f'{mbot_url}/plugins/podcast/{series}_cover.jpg'
            cover_image_url = url_encode(cover_image_url)
        else:
            cover_image_url = ''
        logger.info(f'{plugins_name}已剪辑完成')
        msg_title = f'{series} - 剪辑完成' if series else '音频剪辑完成'
        msg_digest = f'{input_dir} 文件夹内音频已剪辑完成\n存放至 {output_dir}/{cliped_folder}' 
    except Exception as e:
        logger.error(f"{plugins_name}构造消息参数出现错误，原因：{e}")
        return False
    if not xmly_dl:
        push_msg_to_mbot(msg_title, msg_digest,cover_image_url)
    return True

# 添加元数据
def add_tag(file_path, authors, year, reader, series, summary, album, art_album, subfolder, use_filename, subject, filename_text):
    """
    mp3、flac格式: 自定义标签 MVNM 为系列, 标签键: MVNM,  标签类型: 普通文本,  标签值: 系列文本
    m4a格式: 自定义标签 ----:com.apple.iTunes:series 为系列, 标签键: ----:com.apple.iTunes:series,  标签类型: 普通文本,  标签值: 系列文本
    """
    org_album = ''
    audio = mutagen.File(file_path)
    # 获取文件的扩展名
    ext = os.path.splitext(file_path)[1].lower()
    # 获取路径中最后一个文件夹的名称
    folder_name = os.path.basename(os.path.dirname(file_path))
    # 音轨序号
    if filename_text:
        trck_num = extract_number(filename_text)
    if ext == '.mp3':
        # new_TCON_frame = mutagen.id3.TCON(encoding=3, text=['题材'])
        # new_TRCK_frame = mutagen.id3.TRCK(encoding=3, text=['音轨编号'])
        # new_TIT2_frame = mutagen.id3.TIT2(encoding=3, text=['新标题'])
        # new_TPE2_frame = mutagen.id3.TPE2(encoding=3, text=['专辑艺术家'])

        ######################################################################
        # 读取原音频标题
        # if 'TIT2' in audio.tags:
        #     org_title = audio.tags['TIT2'].text[0]
        auto = False
        if auto:
            # 读取原音频专辑-----该值将作为艺术家的值
            if 'TALB' in audio.tags:
                org_album = audio.tags['TALB'].text[0]
            if org_album:
                authors = org_album or authors
            else:
                authors = get_book_name(folder_name) or authors
        ######################################################################
        # 题材
        if subject:
            new_TCON_frame = mutagen.id3.TCON(encoding=3, text=[subject])
            audio.tags.setall('TCON', [new_TCON_frame])
        # 音频序号
        if trck_num:
            trck_num = int(trck_num)
            new_TRCK_frame = mutagen.id3.TRCK(encoding=3, text=[trck_num])
            audio.tags.setall('TRCK', [new_TRCK_frame])
        # 使用文件名作为元数据标题
        if use_filename:
            new_TIT2_frame = mutagen.id3.TIT2(encoding=3, text=[filename_text])
            audio.tags.setall('TIT2', [new_TIT2_frame])
        if reader:
            #  创建一个新的TXXX标签帧对象, 用于存储 演播者, 发布年份
            new_TXXX_nrt_frame = mutagen.id3.TXXX(encoding=3, desc='©nrt', text=[reader])
            new_TCOM_frame = mutagen.id3.TCOM(encoding=3, text=[reader])
            # audio.tags.setall('TXXX', [new_TXXX_nrt_frame])
            audio.tags.add(new_TXXX_nrt_frame)
            audio.tags.add(new_TCOM_frame)
        if year:
            new_TDRC_frame = mutagen.id3.TDRC(encoding=3, text=[year])
            audio.tags.setall('TDRC', [new_TDRC_frame])
        # 艺术家
        if authors:
            new_TPE1_frame = mutagen.id3.TPE1(encoding=3, text=[authors])
            audio.tags.setall('TPE1', [new_TPE1_frame])
        if series:
            new_TXXX_mvn_frame = mutagen.id3.TXXX(encoding=3, desc='©mvn', text=[series])
            new_TXXX_MVNM_frame = mutagen.id3.TXXX(encoding=3, desc='MVNM', text=[series])
            # audio.tags.setall('TXXX', [new_TXXX_mvn_frame])
            audio.tags.add(new_TXXX_mvn_frame)
            audio.tags.add(new_TXXX_MVNM_frame)
        # 简介
        if summary:
            # new_TXXX_summary_frame = mutagen.id3.TXXX(encoding=3, desc='summary', text=[summary])
            new_COMM_frame = mutagen.id3.COMM(encoding=3, lang='chi', desc='简介', text=[summary])
            audio.tags.add(new_COMM_frame)

        if art_album:
            # 专辑艺术家
            new_TPE2_frame = mutagen.id3.TPE2(encoding=3, text=[art_album])
            audio.tags.setall('TALB', [new_TPE2_frame])
        if album:
            # 专辑
            new_TALB_frame = mutagen.id3.TALB(encoding=3, text=[album])
            audio.tags.setall('TALB', [new_TALB_frame])
        elif subfolder:
            # 专辑
            new_TALB_frame = mutagen.id3.TALB(encoding=3, text=[subfolder])
            audio.tags.setall('TALB', [new_TALB_frame])
        # audio.tags.add(new_TXXX_nrt_frame)
        # audio.tags.add(new_TXXX_mvn_frame)
        audio.save()
    if ext == '.m4a':
        """
        audio.tags['©nam'] = '标题'
        audio.tags['©gen'] = '题材'
        audio.tags['trkn'] = '音频序号'

        读取原音频标签
        org_album = audio.tags['©alb']

        """
        # 题材
        if subject:
            audio.tags['©gen'] = subject
        # 音频序号
        if trck_num:
            audio.tags['trkn'] = [(int(trck_num), 0)]
        # 使用文件名作为元数据标题
        if use_filename:
            audio.tags['©nam'] = filename_text
        # 系列名称 自定义标签
        if series:
            audio.tags['©mvn'] = series
            audio.tags['MVNM'] = series
            # 设置series标签（系列）
            audio['----:com.apple.iTunes:series'] = mutagen.mp4.MP4FreeForm(series.encode())
        # 简介
        if summary:
            # audio.tags['summ'] = summary
            audio.tags['©cmt'] = summary
        # 专辑名称 标签
        if album:
            audio.tags['©alb'] = album
        elif subfolder:
            audio.tags['©alb'] = subfolder
        # 演播者 自定义标签
        if reader:
            audio.tags['©nrt'] = reader
            audio.tags['©wrt'] = reader
        # 艺术家 标签
        if authors:
            audio.tags['©ART'] = authors
        # 专辑艺术家
        if art_album:
            audio.tags['aART'] = art_album
        # 专辑艺术家 标签
        # audio.tags['aART'] = '专辑艺术家'
        # 作曲家 标签
        # audio.tags['©wrt'] = '作曲家'
        # 发布年份 标签
        if year:
            audio.tags['©day'] = year
        # 保存修改后的标签
        audio.save()
    if ext == '.flac':
        """
        audio['title'] = "新标题"
        audio['artist'] = "新作者"
        audio['composer'] = "演播者"
        audio['mvnm'] = "系列"
        audio['date'] = "2018"
        audio['album'] = "新专辑"
        audio['genre'] = "题材"
        audio['tracknumber'] = "音频序号"
        
        读取原音频标签
        org_album = audio['album']

        """
        # 题材
        if subject:
            audio['genre'] = subject
        # 音频序号
        if trck_num:
            audio['tracknumber'] = str(trck_num)
        # 使用文件名作为元数据标题
        if use_filename:
            audio['title'] = filename_text
        # 系列名称 自定义标签
        if series:
            audio['mvnm'] = series
        # 简介    
        if summary:
            # audio['summary'] = summary
            audio['comment'] = summary
        # 专辑名称 标签
        if album:
            audio['album'] = album
        elif subfolder:
            audio['album'] = subfolder
        # 演播者 自定义标签
        if reader:
            audio['composer'] = reader
        # 艺术家 标签
        if authors:
            audio['artist'] = authors
        if art_album:
            audio['albumartist'] = art_album
        # 发布年份 标签
        if year:
            audio['date'] = year
        # 保存修改后的标签
        audio.save()

# 线程任务文件分配到文件夹中
def thread_move_to_dir(dir_path, filename, authors, year, reader, series, summary, album, art_album, use_filename, subject,fill_num):
    src_file_path = os.path.join(dir_path, filename)
    for i in range(3):
        try:
            # 只处理文件, 跳过文件夹
            if os.path.isfile(src_file_path):
                file_path = src_file_path
                subfolder,filename_text = match_subfolder(filename,series,fill_num)
                subfolder = album or subfolder
                # 添加tag
                add_tag(file_path, authors, year, reader, series, summary, album, art_album, subfolder, use_filename, subject, filename_text)
                if subfolder:    
                    # 创建子文件夹, 如果不存在
                    subfolder_path = os.path.join(dir_path, subfolder)
                    dst_file_path = os.path.join(subfolder_path, filename)
                    if not os.path.exists(subfolder_path):
                        os.makedirs(subfolder_path)
                    # 移动文件到子文件夹
                    # os.rename(os.path.join(dir_path, filename), os.path.join(subfolder_path, filename))
                    if os.path.exists(dst_file_path):
                        os.remove(dst_file_path)  # 先删除目标文件
                    shutil.move(src_file_path, dst_file_path)
                    if i>0:
                        logger.info(f"{plugins_name}{i+1}/3 次移动 ['{src_file_path}'] -> ['{dst_file_path}'] 成功。")
                    break
        except Exception as e:
            if os.path.isfile(src_file_path):
                subfolder,filename_text = match_subfolder(filename,series,fill_num)
                subfolder = album or subfolder
                if subfolder: 
                    subfolder_path = os.path.join(dir_path, subfolder)
                    dst_file_path = os.path.join(subfolder_path, filename)
                    logger.error(f"{plugins_name}{i+1}/3 次移动 ['{src_file_path}'] -> ['{dst_file_path}'] 失败，原因：{e}")
            else:
                logger.error(f"{plugins_name}{i+1}/3 次移动 ['{filename}'] 失败，原因：{e}")
            time.sleep(3)
            continue

# 文件分配到文件夹中
def move_to_dir(output_dir, authors, year, reader, series, summary, album, art_album, clip_configs, use_filename, subject):
    dir_path = output_dir
    fill_num = 3
    # 如果目录不存在, 则创建
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    # 遍历目录中的所有文件
    for filename in os.listdir(dir_path):
        thread_move_to_dir(dir_path, filename, authors, year, reader, series, summary, album, art_album, use_filename, subject,fill_num)
    if clip_configs != 'clip_and_move':
        logger.info(f'{plugins_name}添加元数据并分配到子文件夹完成')

def diy_abs(folder_path, series, authors, reader, year):
    # 处理当前文件夹中的 metadata.abs 文件
    metadata_path = os.path.join(folder_path, 'metadata.abs')
    if os.path.exists(metadata_path):
        try:
            edit_abs(metadata_path, None, series, authors, reader, year)
        except Exception as e:
            logger.error(f"{plugins_name}处理 ['{folder_path}'] 文件夹中的 metadata.abs 文件出错了: {e}")
    # 遍历所有子文件夹
    for subdir in os.listdir(folder_path):
        subdir_path = os.path.join(folder_path, subdir)
        # 只处理子文件夹, 忽略其他文件
        if os.path.isdir(subdir_path):
            metadata_path = os.path.join(subdir_path, 'metadata.abs')
            if os.path.exists(metadata_path):
                try:
                    edit_abs(metadata_path, subdir, series, authors, reader, year)
                except Exception as e:
                    logger.error(f"{plugins_name}处理 ['{subdir_path}'] 文件夹中的 metadata.abs 文件出错了: {e}")
                    continue
    logger.info(f'{plugins_name}DIY 元数据完成（修改为 Audiobookshelf 能识别的元数据）')

def edit_abs(metadata_path, subdir, series, authors, reader, year):
            # metadata_path = '/a/b/metadata.abs' 这样的完整路径
            skip_chapter = False
            # 读取metadata.abs文件并修改其中的内容
            with open(metadata_path, 'r') as f:
                lines = f.readlines()
                for i in range(len(lines)):
                    if lines[i].startswith('[CHAPTER]'):
                        # 碰到 [CHAPTER] 标记时设置跳过标记
                        skip_chapter = True
                    elif skip_chapter:
                        # 如果处于跳过状态, 直接跳过该行
                        continue
                    elif lines[i].startswith('title=') and subdir:
                        # 修改 title 的值为当前子文件夹的名称,这里的title体现到音频元数据中为专辑名称
                        lines[i] = f'title={subdir}\n'
                    elif lines[i].startswith('series=') and series:
                        # 修改 series 的值为指定的变量值
                        lines[i] = f'series={series}\n'
                    elif lines[i].startswith('authors=') and authors:
                        # 修改 authors 的值为指定的变量值
                        lines[i] = f'authors={authors}\n'
                    elif lines[i].startswith('reader=') and reader:
                        # 修改 reader 的值为指定的变量值
                        lines[i] = f'reader={reader}\n'
                    elif lines[i].startswith('publishedYear=') and year:
                        # 修改 year 的值为指定的变量值
                        lines[i] = f'publishedYear={year}\n'
                    elif lines[i].startswith('[CHAPTER]'):
                        # 遇到下一个 [CHAPTER] 标记时取消跳过标记
                        skip_chapter = False
            # 将修改后的内容写回metadata.abs文件中
            with open(metadata_path, 'w') as f:
                f.writelines(lines)

def move_out(output_dir):
    # 遍历文件夹/date/audo下的所有子文件夹
    for root, dirs, files in os.walk(output_dir):
        # 遍历当前子文件夹中的所有文件
        for file in files:
            # 如果文件是音频文件, 则移动到/date/audo目录下
            if file.endswith(('.mp3', '.wav', '.flac', 'm4a')):
                # 构建源文件和目标文件的路径
                src_path = os.path.join(root, file)
                dst_path = os.path.join(output_dir, file)
                # 移动文件
                shutil.move(src_path, dst_path)
    logger.info(f'{plugins_name}音频已从子文件夹全部移到 {output_dir}')

def match_subfolder(filename,series,fill_num):
    # 处理文件名规范为 0236 xxxx 或者 第0236集 格式
    filename_text = sortout_filename(filename,series,fill_num)
    subfolder = ''
    # 从文件名中获取数字
    match = re.search(r'(\d+)', filename_text)
    if match:
        number = int(match.group(1))
        # 设置number的最小值为1
        number = max(number, 1)
        # 分配子文件夹
        subfolder = str((number - 1) // 100 * 100 + 1) + '-' + str((number - 1) // 100 * 100 + 100)
    else:
        subfolder = '1-100'
    return subfolder,filename_text

# 处理output_dir文件夹及其子文件夹下的文件
def all_add_tag(output_dir, authors, year, reader, series, summary, album, art_album,use_filename,subject,diy_cover,cut,audio_start,audio_end):
    # 遍历目录中的所有文件和子文件夹
    files,fill_num,audio_num = get_audio_files(output_dir)
    i=0
    for file_path in files:
        filename = os.path.basename(file_path)
        # album 变量有值时将其赋给 subfolder 变量，否则将 subfolder 变量的值保持不变
        subfolder,filename_text = match_subfolder(filename,series,fill_num)
        subfolder = album or subfolder
        # 处理文件, 跳过文件夹
        # file_path = os.path.join(root, filename)
        if datetime.now().second % 10 == 0 or i==0:
            logger.info(f"{plugins_name}开始处理: {file_path}")
        if cut:
            file_name, file_extension = os.path.splitext(file_path)
            file_path_tmp = f"{file_name}_tmp{file_extension}"
            audio_cut(file_path,file_path_tmp,audio_start,audio_end)
            os.remove(file_path)
            os.rename(file_path_tmp, file_path)
        add_tag(file_path, authors, year, reader, series, summary, album, art_album, subfolder, use_filename, subject, filename_text)
        if diy_cover:
            cover_art_path = os.path.join(output_dir, 'cover.jpg')
            add_cover(file_path,cover_art_path)
        i=i+1
    logger.info(f'{plugins_name}DIY 元数据完成')

def push_msg_to_mbot(msg_title, msg_digest,cover_image_url,link_url=''):
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
        logger.info(f'{plugins_name}已推送消息')
        return
    except Exception as e:
        logger.error(f'{plugins_name}推送消息异常, 原因: {e}')