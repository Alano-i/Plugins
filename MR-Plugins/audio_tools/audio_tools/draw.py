
from PIL import Image, ImageDraw, ImageFilter,ImageFont,ImageEnhance
import logging
logger = logging.getLogger(__name__)

plugins_name = '「有声书工具箱」'
plugins_path = '/data/plugins/audio_tools'

# 为图片添加内描边
def add_inner_border(image, border_width=2, border_color=(255, 255, 255, 128)):
    # 创建一个与图像相同尺寸的图像，初始为完全透明
    border_image = Image.new('RGBA', image.size, (0, 0, 0, 0))
    # 绘制内描边
    draw = ImageDraw.Draw(border_image)
    for i in range(border_width):
        draw.rectangle(
            (i, i, image.width - i - 1, image.height - i - 1),
            outline=border_color
        )
    # 使用 alpha_composite 合并内描边
    image_with_border = Image.alpha_composite(image, border_image)
    return image_with_border

def draw_cover(img_path,out_path,title,author,reader):
    try:
        font_path = f'{plugins_path}/notify_cover/ys.ttf'
        font_text_path = f'{plugins_path}/notify_cover/lh.ttf'
        reader_flag_path = f'{plugins_path}/notify_cover/reader_flag.png'
        
        author = f'{author} 著' if author else author
        width = 1500
        height = 640
        reader_flag_png = Image.open(reader_flag_path).convert("RGBA")
        original_cover = Image.open(img_path).convert("RGBA")
        black_fg = Image.new("RGBA", (width, height), (0, 0, 0, 80))
        new_cover = Image.new("RGBA", (width, height), (0, 0, 0, 255))
        cover_small = original_cover.resize((558, 558), Image.BICUBIC)

        # 调用函数添加3px内描边,颜色(255, 255, 255, 40)
        cover_small = add_inner_border(cover_small,3,(255, 255, 255, 40))

        cover_jpg = original_cover.resize((width, height), Image.BICUBIC)
        cover_jpg = cover_jpg.filter(ImageFilter.GaussianBlur(radius=180))
        new_cover.paste(cover_jpg, (0, 0))
        new_cover = Image.alpha_composite(new_cover, black_fg)
        new_cover.paste(cover_small, (41, 41))

        title_font_num = 85 if len(title)>14 else 105

        font_title = ImageFont.truetype(f"{font_path}", title_font_num)
        font_author = ImageFont.truetype(f"{font_text_path}", 55)
        font_reader = ImageFont.truetype(f"{font_text_path}", 55)

        draw = ImageDraw.Draw(new_cover)
        font_reader_width = int(draw.textlength(reader, font_reader))

        # 文本高度
        if len(title) > 7:
            if len(title) <= 14:
                title = title[:7] + '\n' + title[7:]
                title_height = 200
            else:
                title = title[:9] + '\n' + title[9:]
                title_height = 170
        else:
            # title = title[:7] + '\n' + title[7:]
            title_height = 100

        # 作者和演播者文字高度
        txt_height = 60
        # 文字行间距
        space = 46

        sum_txt_height = title_height + space + txt_height + space + txt_height

        # 垂直中心线坐标y
        center_y = height/2
        title_y = int(center_y - sum_txt_height/2) - 4
        title_x = 675

        draw.text((title_x, title_y), title, fill=(255,255,255,255),font=font_title)
        draw.text((title_x + 5, title_y+title_height+space), author, fill=(255,255,255,255),font=font_author)
        draw.text((title_x + 5, title_y+title_height+space+txt_height+space), reader, fill=(255,255,255,255),font=font_reader)

        # 将一个png叠放到图片上
        # 创建一个与背景相同尺寸的临时图像，确保它也是RGBA模式
        temp_image = Image.new('RGBA', (width, height))
        # 将圆角矩形放在(100, 150)坐标处
        temp_image.paste(reader_flag_png, (title_x+10+font_reader_width+8, title_y+title_height+space+txt_height+space+5))
        new_cover = Image.alpha_composite(new_cover, temp_image)

        new_cover = new_cover.convert("RGB")
        new_cover.save(out_path, quality=100)
    except Exception as e:
        logger.error(f"{plugins_name}制作通知封面图片出错，原因：{e}")
