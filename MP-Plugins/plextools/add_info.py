import requests
from PIL import Image, ImageDraw, ImageFilter,ImageFont,ImageEnhance
from plexapi.server import PlexServer
import xml.etree.ElementTree as ET
import os
import time
import logging
import urllib3
from urllib3.exceptions import MaxRetryError, ConnectionError, TimeoutError


logger = logging.getLogger(__name__)
plugins_name = '「PLEX 工具箱」'
base_path = '.overlays'
poster_backup_path = '/config/temp/poster_backup'



    
def create_backup_note(directory):
    try:
        if not os.path.exists(directory): os.makedirs(directory)
        logger.info("新建海报备份文件夹成功")

        file_path = os.path.join(directory, "海报备份文件夹_此文件夹中的内容不可删除.txt")
        if not os.path.exists(file_path):
            with open(file_path, 'w') as file:
                file.write("海报备份文件夹_此文件夹中的内容不可删除\n如果已经删除了，需要手动重新设置为未处理过的海报再次运行 plex_tools 插件方可正常使用")
    except Exception as e:
        logger.error(f"{plugins_name}检查备份说明失败，原因：{e}")
create_backup_note(poster_backup_path)

def add_config(config):
    global plex_url, plex_token
    plex_url = config.get('plex_url','')
    plex_token = config.get('plex_token','')

def re_get_poster(media):
    try:
        posters = media.posters()
        if posters:
            s_poster = False
            for p in posters:
                if p.selected:
                    s_poster = True
                    break
            if not s_poster:
                poster_url = f"{plex_url}{posters[0].key}&X-Plex-Token={plex_token}"
                return poster_url
    except Exception as e:
        logger.error(f"{plugins_name}获取海报列表失败，原因：{e}")

def save_img(media,img_url,title,img_path,img_dir,force_add):
    overlay_flag = False
    os.makedirs(img_dir, exist_ok=True)
    retries = 3
    retry_delay = 3
    for i in range(retries):
        try:
            http = urllib3.PoolManager()
            response = http.request('GET', img_url)
            if response.status == 404:
                logger.error(f'「{title}」保存 {img_url} 到本地失败，跳过处理。可能这个媒体没有刮削出封面，你需要手动设置一下封面！')
                break

            with open(f"{img_dir}/tmp.jpg", "wb") as f:
                f.write(response.data)

            # 读取图片信息，EXIF标签是否是overlay
            poster = Image.open(f"{img_dir}/tmp.jpg")
            exif_tags = poster.getexif()
            if 0x04bc in exif_tags and exif_tags[0x04bc] == "overlay":
                overlay_flag = True
            if not overlay_flag or force_add:
                with open(img_path, "wb") as f:
                    f.write(response.data)
                logger.info(f"{title} 的海报/背景已存入{img_path}")
            break
        except Exception as e:
            logger.error(f'「{title}」保存 {img_url} 到本地 {i+1}/{retries} 次请求异常，原因：{e}')
            img_url = re_get_poster(media)
            continue
    if not img_url:
        img_path = ''
    return img_path,overlay_flag

# 大小单位转换，输入Bytes
def convert_bytes_to_gbm(bytes_value):
    gb = bytes_value / (1024 ** 3)  # 转换为GB
    if gb >= 1:
        return f"{gb:.2f}GB"
    else:
        mb = bytes_value / (1024 ** 2)  # 转换为MB
        return f"{mb:.2f}MB"

def convert_milliseconds(milliseconds):
    milliseconds = int(milliseconds)
    minutes = milliseconds // 60000  # 毫秒转分钟
    if minutes >= 60:
        hours = minutes // 60
        minutes %= 60
        if minutes > 0:
            return f"{hours}小时 {minutes}分钟"
        else:
            return f"{hours}小时"
    else:
        return f"{minutes}分钟"

def get_display_title(key):
    # plexserver = PlexServer(plex_url, plex_token)
    # plex_url = plexserver.url('')
    # plex_token = plexserver._token
    url = plex_url + key + '?X-Plex-Token=' + plex_token
    response = requests.get(url)
    if response.status_code == 200:
        # 解析XML
        root = ET.fromstring(response.text)
        """
        streamType="1": 视频流 (Video Stream)
        streamType="2": 音频流 (Audio Stream)
        streamType="3": 字幕流 (Subtitle Stream)
        streamType="4": 章节流 (Chapter Stream)
        """
        # 使用XPath定位第一个streamType="1"的Stream元素
        stream_element = root.find('.//Video/Media/Part/Stream[@streamType="1"]')
        # 使用XPath定位所有的streamType="1"的Stream元素
        # stream_elements = root.findall('.//Video/Media/Part/Stream[@streamType="1"]')
        if stream_element is not None:
            display_title = stream_element.get('displayTitle')
            if display_title:
                return display_title
    return ''

def adjust_brightness(rgba_image, threshold=88):

    # 转换为RGB模式
    rgb_image = rgba_image.convert("RGB")
    width, height = rgb_image.size

    # 截取图片底部190像素
    rgb_bottom_region = rgb_image.crop((0, height - 190, width, height))


    # 创建一个新的空白图像，用于保存调整后的结果
    adjusted_image = Image.new("RGB", (width, height))

    for x in range(width):
        for y in range(height - 190, height):
            # 获取底部像素点的RGB值
            r, g, b = rgb_bottom_region.getpixel((x, y - (height - 190)))

            # 计算亮度（按Luminance公式）
            luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

            # 如果亮度高于阈值，则将亮度设置为80，否则保持不变
            if luminance > threshold:
                r, g, b = int(r * threshold / luminance), int(g * threshold / luminance), int(b * threshold / luminance)

            # 将调整后的像素点保存到底部区域的副本中
            rgb_bottom_region.putpixel((x, y - (height - 190)), (r, g, b))

    # 将调整后的底部区域放回原始图像的底部位置
    adjusted_image = Image.new("RGB", (width, height))
    adjusted_image.paste(rgb_image, (0, 0))
    adjusted_image.paste(rgb_bottom_region, (0, height - 190))

    adjusted_image = adjusted_image.convert("RGBA")
    return adjusted_image

def resize_and_fill_canvas(poster_path, poster_width, poster_height):
    # 打开图片
    original_image = Image.open(poster_path)
    # 获取图片和画布的宽高
    img_width, img_height = original_image.size
    poster_ratio = poster_width / poster_height
    img_ratio = img_width / img_height
    # 计算缩放后的宽高
    if img_ratio >= poster_ratio:
        # 以高度为准进行缩放
        new_width = int(poster_height * img_ratio)
        new_height = poster_height
    else:
        # 以宽度为准进行缩放
        new_width = poster_width
        new_height = int(poster_width / img_ratio)
    # 等比缩放图片
    resized_image = original_image.resize((new_width, new_height), Image.BICUBIC)
    # 创建新的画布
    canvas = Image.new('RGBA', (poster_width, poster_height), (255, 255, 255, 0))
    # 将图片居中放置在画布上
    x_offset = (poster_width - new_width) // 2
    y_offset = (poster_height - new_height) // 2
    canvas.paste(resized_image, (x_offset, y_offset))
    return canvas

def new_poster(media_type,resolution,rdynamic_range,duration,rating,poster_path,title):
    media_type_org = media_type
    if media_type in ['show','episode','season']: media_type = 'show'
    if media_type in ['show_p','season_p']: duration = ''
    if media_type in ['movie','show_p','season_p']: media_type = 'movie'
    outline_a = 32
    rating = str(rating)
    if rating == '10.0': rating = '10'
    if media_type == 'movie':
        poster_width = 1000
        poster_height = 1500
        scale = 1215/1000
        if resolution == '1080P' and media_type_org not in ['show_p','season_p'] and '小时' in duration and '分钟' in duration:
            scale = 1192/1000
            duration = duration.replace(' ','')
        if rdynamic_range =='DV' and media_type_org not in ['show_p','season_p'] and '小时' in duration and '分钟' in duration:
            scale = 1180/1000
            duration = duration.replace(' ','')
        if media_type_org in ['show_p','season_p']:
            scale = 1198/1000
    elif media_type == 'show':
        poster_width = 1000
        poster_height = 563
        scale = 700/1000
    img_path = f'{base_path}/img/empty'
    # 将原海报等比缩放后铺满画布
    resized_image = resize_and_fill_canvas(poster_path, poster_width, poster_height)

    # 创建一个与海报相同尺寸的新图像(RGBA)
    new_image = Image.new("RGBA", (poster_width, poster_height), (0, 0, 0, 255))
    new_image.paste(resized_image, (0, 0))
    # 将改变大小后的海报高斯模糊
    blurred_image = new_image.filter(ImageFilter.GaussianBlur(radius=77))

    radius = int(20 * scale)  # 圆角矩形的半径
    if media_type == 'movie':
        x = int(22 * scale)-4  # 距离左侧边缘的距离
    elif media_type == 'show':
        x = int(22 * scale)
    bottom = int(28 * scale)
    bar_height = int(110 * scale)
    y = poster_height - bottom - bar_height  # 距离底部的距离
    right = poster_width - x  # 距离右侧边缘的距离
    y0 = int(22 * scale)
    
    # 获取底部的区域一个小区域
    bottom_region = new_image.crop((0, y - 2, poster_width, poster_height))
    # 计算底部区域的亮度
    brightness = sum(bottom_region.convert("L").getdata()) / ((bar_height + 2 + bottom) * poster_width)
    brightness = int(brightness)
    # logger.info(f'此海报亮度：{brightness}')

    if media_type == 'movie':
        overlay_alpha = 165
        if brightness < 60:
            overlay_alpha = 145
    elif media_type == 'show':
        overlay_alpha = 140
        if brightness < 60:
            overlay_alpha = 135
    # node = 35
    node = 80
    out_line_node = 80
    max_a = 30
    min_a = 0
    if brightness > node:
        if brightness < out_line_node:
            outline_middle = max_a
        else:
            outline_middle = 0
        outline_a = 0 if media_type == 'show' else outline_middle

        # 黑色背景
        contrast_factor = 1.65  # 色阶增强因子，大于1增强，小于1减弱
        # 将高斯模糊后的海报上叠加黑色透明层
        overlay_layer = Image.new("RGBA", (poster_width, poster_height), (0, 0, 0, overlay_alpha))
        poster_image = Image.alpha_composite(blurred_image, overlay_layer)

    else:
        outline_a = 0
        # 白色背景
        overlay_a_black = 0
        if media_type == 'movie':
            overlay_a = 50
            if brightness < 19:
                overlay_a = 62
            if brightness > 30:
                overlay_a_black = 40
            if brightness > 35:
                overlay_a_black = 50
        if media_type == 'show':
            overlay_a = 36
            if brightness < 19:
                overlay_a = 42
            if brightness > 35:
                overlay_a_black = 30
        
        overlay_layer = Image.new("RGBA", (poster_width, poster_height), (255, 255, 255, overlay_a))
        # 使用叠加模式混合两个图像
        # poster_image = Image.blend(blurred_image, overlay_layer,0.19)
        poster_image = Image.alpha_composite(blurred_image, overlay_layer)
        overlay_layer_black = Image.new("RGBA", (poster_width, poster_height), (0, 0, 0, overlay_a_black))
        poster_image = Image.alpha_composite(poster_image, overlay_layer_black)
        # poster_image.paste(overlay_layer_black, (0, 0))
        contrast_factor = 1.3  # 色阶增强因子，大于1增强，小于1减弱
    
    try:
        # 实现黑色透明层与海报图像混合模式：正片叠底效果
        # 获取图像像素数据
        pixels = poster_image.load()
        # 迭代每个像素并应用正片叠底混合模式
        for y0 in range(poster_image.height):
            for x0 in range(poster_image.width):
                r, g, b, a = pixels[x0, y0]
                pixels[x0, y0] = (r * a // 255, g * a // 255, b * a // 255, a)
        if brightness < 36:
            poster_image = adjust_brightness(poster_image)
        # 饱和度
        enhancer = ImageEnhance.Color(poster_image)
        if media_type == 'movie':
            saturation_factor = 1.8  # 饱和度增强因子，大于1增强，小于1减弱
        elif media_type == 'show':
            saturation_factor = 1.5
        enhanced_image = enhancer.enhance(saturation_factor)
        # 色阶（对比度）
        enhancer = ImageEnhance.Contrast(enhanced_image)
        # contrast_factor = 1.3  # 色阶增强因子，大于1增强，小于1减弱
        poster_image = enhancer.enhance(contrast_factor)
    except Exception as e:
        logger.error(f'{plugins_name}调整色阶、饱和度、混合模式时发生错误，原因：{e}')
    # 创建海报层图像
    poster = Image.new("RGBA", (poster_width, poster_height))
    # 创建一个与海报相同尺寸的遮罩图像
    mask = Image.new("L", (poster_width, poster_height))
    # 在遮罩图像上绘制圆角矩形
    draw = ImageDraw.Draw(mask)

    draw.rounded_rectangle([(x, y), (right, y + bar_height)], radius, fill=255)
    # 创建一个与海报相同尺寸的遮罩图像
    outline = Image.new("RGBA", (poster_width, poster_height))
    # 在遮罩图像上绘制圆角矩形
    draw = ImageDraw.Draw(outline)

    if media_type == 'movie':
        draw.rounded_rectangle([(x-2, y-2), (right+2, y + bar_height+2)], radius+2, fill=(255,255,255,outline_a))
    elif media_type == 'show':
        draw.rounded_rectangle([(x-1, y-1), (right+1, y + bar_height+1)], radius+1, fill=(255,255,255,outline_a))

    # 在新图像上叠加原始海报
    poster.paste(resized_image, (0, 0))
    # 将描边层和海报层叠加
    poster = Image.alpha_composite(poster, outline)
    # 将高斯模糊后的海报叠加到新海报，并将遮罩应用于模糊图像
    poster.paste(poster_image, (0, 0), mask=mask)
    png_height = int(62 * scale)
    # 分辨率
    resolution_png = Image.open(f"{img_path}/{resolution}.png").convert("RGBA")
    resolution_png = resolution_png.resize((int(png_height*resolution_png.width/resolution_png.height), png_height), Image.LANCZOS)
    # 创建一个与海报图像相同尺寸的图像
    resolution_image = Image.new("RGBA", (poster_width, poster_height))
    x_resolution = int(x+22 * scale)
    y_resolution = int(y+bar_height/2 - resolution_png.height/2)
    resolution_image.paste(resolution_png, (x_resolution, y_resolution))
    poster = Image.alpha_composite(poster, resolution_image)
    # 动态范围
    x_rdynamic_range = int(x_resolution + resolution_png.width + 20 * scale)
    rdynamic_range_png = Image.open(f"{img_path}/{rdynamic_range}.png").convert("RGBA")
    rdynamic_range_png = rdynamic_range_png.resize((int(png_height*rdynamic_range_png.width/rdynamic_range_png.height), png_height), Image.LANCZOS)
    # 创建一个与海报图像相同尺寸的图像
    rdynamic_range_image = Image.new("RGBA", (poster_width, poster_height))
    rdynamic_range_image.paste(rdynamic_range_png, (x_rdynamic_range, y_resolution))
    poster = Image.alpha_composite(poster, rdynamic_range_image)
    # 时长
    font_path = f'{base_path}/font/fzlth.ttf'
    font_path_n = f'{base_path}/font/ALIBABA_Bold.otf'
    draw = ImageDraw.Draw(poster)
    if rdynamic_range =='DV' and media_type == 'movie':
        font_r = ImageFont.truetype(f"{font_path}", int(51 * scale))
    else:
        font_r = ImageFont.truetype(f"{font_path}", int(54 * scale))
    font_n = ImageFont.truetype(f"{font_path_n}", int(75 * scale))
    # text_width, text_height = draw.textsize(duration, font=font_r)
    text_width = int(draw.textlength(duration, font_r))
    text_height = 52 * scale
    # text_width0, text_height0 = draw.textsize(rating, font=font_n)
    text_width0 = int(draw.textlength(rating, font_n))
    text_height0 = 52 * scale

    y_duration = int(y+bar_height/2 - text_height/2)
    if media_type == 'movie':
        x_duration = int(x_resolution + resolution_png.width + 20 * scale + rdynamic_range_png.width + 22 * scale)
    elif media_type == 'show':
        x_duration = int(x_resolution + resolution_png.width + 20 * scale + rdynamic_range_png.width + 30 * scale)

    y_n = int(y+bar_height/2 - text_height0/2)
    if media_type == 'movie':
        draw.text((x_duration, y_duration-3 * scale), duration, fill=(255,255,255,255),font=font_r)
        if rdynamic_range =='DV':
            draw.text((right-26 * scale-text_width0, y_n-23 * scale), rating, fill=(255,155,21,255),font=font_n)
        else:
            draw.text((right-30 * scale-text_width0, y_n-23 * scale), rating, fill=(255,155,21,255),font=font_n)

    elif media_type == 'show':
        draw.text((x_duration, y_duration-5 * scale+1), duration, fill=(255,255,255,255),font=font_r)
        draw.text((right-30 * scale-text_width0, y_n-23 * scale+2), rating, fill=(255,155,21,255),font=font_n)

    poster = poster.convert("RGB")
    # out_path = f"{base_path}/done/{os.path.basename(poster_path)}"
    out_path = f"{poster_backup_path}/tmp.jpg"
    # poster.save(out_path, quality=97)
    # 添加自定义的EXIF标签
    exif_tags = poster.getexif()
    exif_tags[0x04bc] = "overlay"
    # 保存图像并将EXIF标签写入
    poster.save(out_path, quality=99, exif=exif_tags)
    # 读取图片信息，EXIF标签是否是overlay
    # posterddd = Image.open(out_path)
    # exif_tags = posterddd.getexif()
    # if 0x04bc in exif_tags and exif_tags[0x04bc] == "overlay":
    #     overlay_flag = True
    return out_path

def get_local_info(media,media_title=''):
    # 文件名
    try:
        file_name = os.path.basename(media.locations[0])
        # file_name = os.path.basename(media.media[0].parts[0].file)  # 此行也可获取文件名
    except Exception as e:
        file_name = ''
    # 时长
    try:
        duration = convert_milliseconds(media.duration)
    except Exception as e:
        duration = ''
    # 大小
    try:
        size = convert_bytes_to_gbm(media.media[0].parts[0].size)
    except Exception as e:
        size = ''
    # bitrate
    try:
        bitrate = f"{round(media.media[0].bitrate / 1000, 1)}Mbps"
    except Exception as e:
        bitrate = ''
    # 分辨率
    try:
        videoResolution = media.media[0].videoResolution.lower() #480 720 1080 4k
        videoResolution = videoResolution if videoResolution == '4k' else f"{videoResolution}P"
        videoResolution = videoResolution.upper()
    except Exception as e:
        videoResolution = ''

    # 如果没有获取到分辨率
    if not videoResolution:
        logger.error(f"{plugins_name} 没有获取到 ['{media_title}'] 的分辨率，请检查 PLEX 对该影片是否已分析完成。")
    # 动态范围
    try:
        
        key = media.key # /library/metadata/33653
        # display_title = get_display_title(key).lower()
        media.reload()
        streams = media.media[0].parts[0].streams
        display_title = streams[0].displayTitle.lower(), #'4K DoVi (HEVC Main 10) 4K HDR10 (HEVC Main 10) 1080p (H.264)
        if 'dovi' in display_title or 'dov' in display_title or 'dv' in display_title:
            display_title = 'DV'
        elif 'hdr' in display_title:
            display_title = 'HDR'
        else:
            display_title = 'SDR'
    except Exception as e:
        logger.error(f"{plugins_name} 没有获取到 ['{media_title}'] 的动态范围，请检查 PLEX 对该影片是否已分析完成。错误：{e}")
        display_title = ''
    return file_name,duration,size,bitrate,videoResolution,display_title

def get_episode(media,media_type,lib_name,force_add,restore,show_log):
    if media_type =='season':
        rating_key = media.parentRatingKey
        plexserver = PlexServer(plex_url, plex_token)
        show = plexserver.fetchItem(int(rating_key))
        show_year = show.year   
        rating = show.audienceRating or ''
        add_info_one(media,'season_p','',lib_name,force_add,1,rating,show_year,restore,show_log)
    if media_type =='show':
        show_year = media.year
        try:
            rating = media.audienceRating
        except Exception as e:
            rating = ''

        add_info_one(media,'show_p','',lib_name,force_add,1,rating,show_year,restore,show_log)
        # 获取季节列表
        seasons = media.seasons()
        for season in seasons:
            add_info_one(season,'season_p','',lib_name,force_add,1,rating,show_year,restore,show_log)

    for episode in media.episodes():
        add_info_one(episode,'episode','',lib_name,force_add,1,rating,show_year,restore,show_log)

def add_info_one(media,media_type,media_n,lib_name,force_add,i,rating,show_year,restore,show_log):
    media_title = ''
    media_s = media
    poster_url = ''
    for v in range(3):
        try:
            if media_type == 'movie':
                rating = media.audienceRating
                media_title = f"{media.title} ({media.year})"
                poster_url = media.posterUrl
            if media_type == 'episode':
                if not rating or not show_year:
                    rating_key = media.grandparentRatingKey
                    plexserver = PlexServer(plex_url, plex_token) 
                    show = plexserver.fetchItem(int(rating_key))
                    show_year = show.year
                    rating = show.audienceRating or ''
                poster_url = media.posterUrl
                e = str(media.episodeNumber).zfill(2)
                s = str(media.parentIndex).zfill(2)
                t = media.grandparentTitle
                media_title = f"{t} {show_year} S{s}E{e}"

            if media_type == 'show_p':
                poster_url = media.posterUrl
                t = media.title
                media_title = f"{t} {show_year}"
            if media_type == 'season_p':
                poster_url = media.posterUrl
                t = media.parentTitle
                s = str(media.seasonNumber).zfill(2)
                media_title = f"{t} {show_year} S{s}"
                if not media.posters():
                    poster_url = ''

            if not lib_name:
                lib_name = media.librarySectionTitle or ''
            media_title = media_title or '未知' 
            if show_log:
                if media_n:
                    logger.info(f"{plugins_name}开始处理 {i}/{media_n} ['{media_title}']")
                else:
                    logger.info(f"{plugins_name}开始处理 ['{media_title}']")
            
            if poster_url:

                img_dir = f"{poster_backup_path}/{lib_name}"
                img_path = os.path.join(img_dir, f"{media_title}.jpg")
                if restore:
                    media.uploadPoster(filepath=img_path)
                    break

                poster_path,overlay_flag = save_img(media,poster_url,media_title,img_path,img_dir,force_add)
                # 上传海报
                if not overlay_flag or force_add:

                    if media_type in ['show_p','season_p']:
                        # media_s = media
                        medias = media.episodes()
                        medias.sort(key=lambda media: media.addedAt, reverse=True)  # 最新的排在最前面
                        media = medias[0]

                    file_name,duration,size,bitrate,videoResolution,display_title = get_local_info(media,media_title)
                    if poster_path:
                        out_path = new_poster(media_type,videoResolution,display_title,duration,rating,poster_path,media_title)

                        if media_type in ['show_p','season_p']:
                            media = media_s

                        media.uploadPoster(filepath=out_path)
                        if show_log:
                            logger.info(f"{plugins_name} ['{media_title}'] 的海报已上传")
                else:
                    if show_log: logger.warning(f"['{media_title}'] 已经处理过了，跳过")
            break
        except Exception as e:
            media = media_s
            media_title = media_title or '未知'
            logger.error(f"{plugins_name}第 {v+1}/3 次处理 ['{media_title}'] 时失败，原因：{e}")
            time.sleep(3)

def add_info_to_posters(library,lib_name,force_add,restore,show_log,only_show):
    lib_type = library.type
    if lib_type == 'show':
        shows = library.all()
        if shows:
            for show in shows:
                show_year = show.year
                try:
                    rating = show.audienceRating
                except Exception as e:
                    rating = ''

                add_info_one(show,'show_p','',lib_name,force_add,1,rating,show_year,restore,show_log)
                # 获取季节列表
                seasons = show.seasons()
                for season in seasons:
                    add_info_one(season,'season_p','',lib_name,force_add,1,rating,show_year,restore,show_log)

                if not only_show:
                    i=1
                    for episode in show.episodes():
                        add_info_one(episode,'episode','',lib_name,force_add,i,rating,show_year,restore,show_log)
                        i=i+1
                # return
            logger.info(f"{plugins_name}媒体库 ['{lib_name}'] 中的剧集海报添加媒体信息完成")
        else:
            logger.info(f"{plugins_name}媒体库 ['{lib_name}'] 中没有剧集，不需要处理")
    elif lib_type == 'movie':
        movies = library.all()
        if movies:
            movies_n = len(movies)
            i=1
            for movie in movies:
                # if i>4:
                #     return
                add_info_one(movie,'movie',movies_n,lib_name,force_add,i,'','',restore,show_log)
                i=i+1
            logger.info(f"{plugins_name}媒体库 ['{lib_name}'] 中的电影海报添加媒体信息完成")
        else:
            logger.info(f"{plugins_name}媒体库 ['{lib_name}'] 中没有电影，不需要处理")

class PlexAddInfo:
    def __init__(self,bk_path) -> None:
        self.bk_path=bk_path
        global poster_backup_path 
        poster_backup_path= bk_path
    def add_info_to_posters_main(self,libraries,force_add,restore,show_log,only_show,plex_server):
        current_path = os.getcwd()
        logger.info(f"{plugins_name}当前工作路径："+current_path)
        global base_path
        base_path=current_path+'/app/plugins/plextools/overlays'
        create_backup_note(poster_backup_path)
        try:
            plexserver = plex_server
        except Exception as e:
            logger.error(f"{plugins_name}连接 Plex 服务器失败,原因：{e}")
        try:
            for lib in libraries:
                name=libraries[lib][2]
                library = plexserver.library.section(name)
                add_info_to_posters(library,name,force_add,restore,show_log,only_show)
        except Exception as e:
            logger.error(f"{plugins_name}海报添加信息出现错误! 原因：{e}")
