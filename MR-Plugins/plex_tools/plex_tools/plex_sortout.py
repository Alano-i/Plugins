import logging
import sys
from moviebotapi.core.models import MediaType
from mbot.openapi import mbot_api
import pypinyin
import re
import time
import threading
# import feedparser
from lxml import etree
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import random
from urllib3.exceptions import ConnectTimeoutError
from mbot.openapi import media_server_manager
from plexapi.server import PlexServer
from .add_info import add_info_one, get_episode,create_backup_note

server = mbot_api
RECOVER = 1
ENABLE_LOG = 1
logger = logging.getLogger(__name__)
plugins_name = '「PLEX 工具箱」'
poster_backup_path = '/data/poster_backup'

IMDBTop250 = ['tt0111161', 'tt0068646', 'tt0468569', 'tt0071562', 'tt0050083', 'tt0108052', 'tt0167260', 'tt0110912', 'tt0120737', 'tt0060196', 'tt0109830', 'tt0137523', 'tt0167261', 'tt1375666', 'tt0080684', 'tt0133093', 'tt0099685', 'tt0073486', 'tt0114369', 'tt0047478', 'tt0038650', 'tt0102926', 'tt0120815', 'tt0317248', 'tt0816692', 'tt0118799', 'tt0120689', 'tt0076759', 'tt0103064', 'tt0088763', 'tt0245429', 'tt0253474', 'tt0054215', 'tt6751668', 'tt0110413', 'tt0110357', 'tt0172495', 'tt0120586', 'tt0407887', 'tt0482571', 'tt2582802', 'tt0114814', 'tt0034583', 'tt0095327', 'tt0056058', 'tt1675434', 'tt0027977', 'tt0064116', 'tt0095765', 'tt0047396', 'tt0078748', 'tt0021749', 'tt0078788', 'tt0209144', 'tt1853728', 'tt0082971', 'tt0910970', 'tt0405094', 'tt0043014', 'tt0050825', 'tt0081505', 'tt0032553', 'tt4154756', 'tt0051201', 'tt0090605', 'tt4633694', 'tt0169547', 'tt0057012', 'tt1345836', 'tt0364569', 'tt0361748', 'tt0086879', 'tt2380307', 'tt0114709', 'tt7286456', 'tt0112573', 'tt0082096', 'tt4154796', 'tt0119698', 'tt0087843', 'tt0119217', 'tt5311514', 'tt0045152', 'tt1187043', 'tt0180093', 'tt0057565', 'tt0435761', 'tt8267604', 'tt0086190', 'tt0338013', 'tt0062622', 'tt0091251', 'tt0105236', 'tt2106476', 'tt0033467', 'tt0022100', 'tt0056172', 'tt0053125', 'tt0044741', 'tt0052357', 'tt0053604', 'tt0211915', 'tt0066921', 'tt0036775', 'tt0093058', 'tt0086250', 'tt8503618', 'tt1255953', 'tt0113277', 'tt0056592', 'tt1049413', 'tt0070735', 'tt1832382', 'tt0017136', 'tt0075314', 'tt0119488', 'tt0095016', 'tt0208092', 'tt0097576', 'tt1745960', 'tt0040522', 'tt0986264', 'tt8579674', 'tt0363163', 'tt5074352', 'tt0059578', 'tt0372784', 'tt0012349', 'tt0053291', 'tt10272386', 'tt0042192', 'tt0993846', 'tt6966692', 'tt0055031', 'tt0089881', 'tt0112641', 'tt0120382', 'tt0469494', 'tt0457430', 'tt0105695', 'tt0167404', 'tt1130884', 'tt0268978', 'tt0107290', 'tt0055630', 'tt0040897', 'tt0071853', 'tt0477348', 'tt0057115', 'tt0266697', 'tt0042876', 'tt10872600', 'tt0084787', 'tt0266543', 'tt0080678', 'tt0071315', 'tt0081398', 'tt0434409', 'tt0031381', 'tt0120735', 'tt0046912', 'tt2096673', 'tt1305806', 'tt0347149', 'tt5027774', 'tt0117951', 'tt0050212', 'tt1392214', 'tt1291584', 'tt0116282', 'tt1205489', 'tt0096283', 'tt0264464', 'tt0405159', 'tt0118849', 'tt0083658', 'tt0015864', 'tt4729430', 'tt0112471', 'tt1201607', 'tt2024544', 'tt0047296', 'tt0052618', 'tt2278388', 'tt2267998', 'tt0050986', 'tt0017925', 'tt0072684', 'tt0107207', 'tt0041959', 'tt0077416', 'tt2119532', 'tt0046268', 'tt0353969', 'tt0015324', 'tt3011894', 'tt0031679', 'tt1392190', 'tt0978762', 'tt0050976', 'tt0892769', 'tt0198781', 'tt0073195', 'tt0097165', 'tt3170832', 'tt0118715', 'tt0046438', 'tt0019254', 'tt1950186', 'tt0395169', 'tt0075148', 'tt0091763', 'tt0382932', 'tt1895587', 'tt3315342', 'tt0088247', 'tt0092005', 'tt1979320', 'tt0074958', 'tt0381681', 'tt0758758', 'tt0032138', 'tt0036868', 'tt0107048', 'tt0070047', 'tt0048473', 'tt0317705', 'tt0035446', 'tt0113247', 'tt0325980', 'tt15097216', 'tt0032551', 'tt0058946', 'tt1028532', 'tt0476735', 'tt0245712', 'tt0032976', 'tt0061512', 'tt4016934', 'tt0053198', 'tt0059742', 'tt0025316', 'tt0060827', 'tt0079470', 'tt0129167', 'tt1454029', 'tt0071411', 'tt0103639', 'tt0099348', 'tt0083987']
DouBanTop250 = [278, 10997, 13, 597, 101, 637, 129, 424, 27205, 157336, 37165, 28178, 10376, 20453, 5528, 10681, 10775, 269149, 37257, 21835, 81481, 238, 1402, 77338, 43949, 8392, 746, 354912, 31439, 155, 671, 122, 770, 532753, 255709, 14160, 389, 517814, 360814, 4935, 25838, 87827, 51533, 640, 365045, 423, 13345, 10515, 121, 9475, 11216, 804, 490132, 207, 47759, 120, 603, 240, 8587, 242452, 10451, 550, 453, 4922, 14574, 582, 47002, 100, 10867, 15121, 411088, 19995, 857, 510, 21334, 12445, 274, 11324, 120467, 1124, 1954, 23128, 9470, 489, 311, 680, 673, 3082, 18329, 74308, 53168, 2832, 807, 11423, 4977, 22, 672, 152578, 31512, 158445, 25538, 37703, 398818, 142, 162, 197, 16804, 76, 745, 11104, 49026, 128, 177572, 4291, 80, 194, 37185, 161285, 294682, 9559, 51739, 2517, 210577, 30421, 336026, 37797, 1100466, 122906, 594, 10191, 242, 92321, 348678, 10494, 585, 674, 10193, 4348, 396535, 24238, 20352, 165213, 68718, 54186, 587, 74037, 55157, 77117, 333339, 9261, 10950, 205596, 209764, 324786, 843, 55156, 346, 150540, 526431, 4588, 605, 539, 372058, 176, 359940, 152532, 49519, 292362, 205, 598, 2503, 11471, 81, 315846, 47423, 132344, 497, 77, 39693, 31743, 265195, 45380, 872, 505192, 244786, 82690, 295279, 62, 12405, 475557, 425, 11647, 26466, 40751, 508, 508442, 15804, 89825, 7350, 16859, 13398, 44214, 475149, 16074, 901, 380, 45612, 11036, 334541, 57627, 644, 8290, 424694, 39915, 12477, 280, 548, 76341, 40213, 782, 406997, 16869, 12429, 473267, 220289, 1541, 604, 1372, 525832, 313369, 695932, 25050, 1830, 43824, 286217, 2502, 33320, 12444, 122973, 4476, 9345, 18311, 2501, 8055, 198277, 1427, 36970, 14069, 675, 7508]

# DouBanTop250 = [{'title': '肖申克的救赎', 'year': 1994}, {'title': '霸王别姬', 'year': 1993}, {'title': '阿甘正传', 'year': 1994}, {'title': '泰坦尼克号', 'year': 1997}, {'title': '这个杀手不太冷', 'year': 1994}, {'title': '美丽人生', 'year': 1997}, {'title': '千与千寻', 'year': 2001}, {'title': '辛德勒的名单', 'year': 1993}, {'title': '盗梦空间', 'year': 2010}, {'title': '星际穿越', 'year': 2014}, {'title': '楚门的世界', 'year': 1998}, {'title': '忠犬八公的故事', 'year': 2009}, {'title': '海上钢琴师', 'year': 1998}, {'title': '三傻大闹宝莱坞', 'year': 2009}, {'title': '放牛班的春天', 'year': 2004}, {'title': '机器人总动员', 'year': 2008}, {'title': '无间道', 'year': 2002}, {'title': '疯狂动物城', 'year': 2016}, {'title': '控方证人', 'year': 1957}, {'title': '大话西游之大圣娶亲', 'year': 1995}, {'title': '熔炉', 'year': 2011}, {'title': '教父', 'year': 1972}, {'title': '当幸福来敲门', 'year': 2006}, {'title': '触不可及', 'year': 2011}, {'title': '怦然心动', 'year': 2010}, {'title': '龙猫', 'year': 1988}, {'title': '末代皇帝', 'year': 1987}, {'title': '寻梦环游记', 'year': 2017}, {'title': '活着', 'year': 1994}, {'title': '蝙蝠侠：黑暗骑士', 'year': 2008}, {'title': '哈利·波特与魔法石', 'year': 2001}, {'title': '指环王3：王者无敌', 'year': 2003}, {'title': '乱世佳人', 'year': 1939}, {'title': '我不是药神', 'year': 2018}, {'title': '素媛', 'year': 2013}, {'title': '飞屋环游记', 'year': 2009}, {'title': '十二怒汉', 'year': 1957}, {'title': '何以为家', 'year': 2018}, {'title': '摔跤吧！爸爸', 'year': 2016}, {'title': '哈尔的移动城堡', 'year': 2004}, {'title': '鬼子来了', 'year': 2000}, {'title': '少年派的奇幻漂流', 'year': 2012}, {'title': '让子弹飞', 'year': 2010}, {'title': '猫鼠游戏', 'year': 2002}, {'title': '海蒂和爷爷', 'year': 2015}, {'title': '钢琴家', 'year': 2002}, {'title': '大话西游之月光宝盒', 'year': 1995}, {'title': '天空之城', 'year': 1986}, {'title': '指环王2：双塔奇兵', 'year': 2002}, {'title': '闻香识女人', 'year': 1992}, {'title': '天堂电影院', 'year': 1988}, {'title': '罗马假日', 'year': 1953}, {'title': '绿皮书', 'year': 2018}, {'title': '死亡诗社', 'year': 1989}, {'title': '大闹天宫', 'year': 1961}, {'title': '指环王1：护戒使者', 'year': 2001}, {'title': '黑客帝国', 'year': 1999}, {'title': '教父2', 'year': 1974}, {'title': '狮子王', 'year': 1994}, {'title': '辩护人', 'year': 2013}, {'title': '饮食男女', 'year': 1994}, {'title': '搏击俱乐部', 'year': 1999}, {'title': '美丽心灵', 'year': 2001}, {'title': '本杰明·巴顿奇事', 'year': 2008}, {'title': '穿条纹睡衣的男孩', 'year': 2008}, {'title': '窃听风暴', 'year': 2006}, {'title': '情书', 'year': 1995}, {'title': '两杆大烟枪', 'year': 1998}, {'title': '西西里的美丽传说', 'year': 2000}, {'title': '音乐之声', 'year': 1965}, {'title': '看不见的客人', 'year': 2016}, {'title': '阿凡达', 'year': 2009}, {'title': '拯救大兵瑞恩', 'year': 1998}, {'title': '飞越疯人院', 'year': 1975}, {'title': '小鞋子', 'year': 1997}, {'title': '哈利·波特与死亡圣器(下)', 'year': 2011}, {'title': '沉默的羔羊', 'year': 1991}, {'title': '禁闭岛', 'year': 2010}, {'title': '布达佩斯大饭店', 'year': 2014}, {'title': '致命魔术', 'year': 2006}, {'title': '蝴蝶效应', 'year': 2004}, {'title': '海豚湾', 'year': 2009}, {'title': '功夫', 'year': 2004}, {'title': '心灵捕手', 'year': 1997}, {'title': '美国往事', 'year': 1984}, {'title': '低俗小说', 'year': 1994}, {'title': '哈利·波特与阿兹卡班的囚徒', 'year': 2004}, {'title': '摩登时代', 'year': 1936}, {'title': '春光乍泄', 'year': 1997}, {'title': '超脱', 'year': 2011}, {'title': '喜剧之王', 'year': 1999}, {'title': '致命ID', 'year': 2003}, {'title': '七宗罪', 'year': 1995}, {'title': '杀人回忆', 'year': 2003}, {'title': '红辣椒', 'year': 2006}, {'title': '加勒比海盗', 'year': 2003}, {'title': '哈利·波特与密室', 'year': 2002}, {'title': '狩猎', 'year': 2012}, {'title': '被嫌弃的松子的一生', 'year': 2006}, {'title': '7号房的礼物', 'year': 2013}, {'title': '一一', 'year': 2000}, {'title': '唐伯虎点秋香', 'year': 1993}, {'title': '请以你的名字呼唤我', 'year': 2017}, {'title': '断背山', 'year': 2005}, {'title': '剪刀手爱德华', 'year': 1990}, {'title': '勇敢的心', 'year': 1995}, {'title': '入殓师', 'year': 2008}, {'title': '爱在黎明破晓前', 'year': 1995}, {'title': '第六感', 'year': 1999}, {'title': '重庆森林', 'year': 1994}, {'title': '蝙蝠侠：黑暗骑士崛起', 'year': 2012}, {'title': '幽灵公主', 'year': 1997}, {'title': '超能陆战队', 'year': 2014}, {'title': '菊次郎的夏天', 'year': 1999}, {'title': '爱在日落黄昏时', 'year': 2004}, {'title': '天使爱美丽', 'year': 2001}, {'title': '甜蜜蜜', 'year': 1996}, {'title': '阳光灿烂的日子', 'year': 1994}, {'title': '小森林 夏秋篇', 'year': 2014}, {'title': '完美的世界', 'year': 1993}, {'title': '借东西的小人阿莉埃蒂', 'year': 2010}, {'title': '无人知晓', 'year': 2004}, {'title': '消失的爱人', 'year': 2014}, {'title': '倩女幽魂', 'year': 1987}, {'title': '小森林 冬春篇', 'year': 2015}, {'title': '侧耳倾听', 'year': 1995}, {'title': '寄生虫', 'year': 2019}, {'title': '时空恋旅人', 'year': 2013}, {'title': '幸福终点站', 'year': 2004}, {'title': '驯龙高手', 'year': 2010}, {'title': '教父3', 'year': 1990}, {'title': '萤火之森', 'year': 2011}, {'title': '一个叫欧维的男人决定去死', 'year': 2015}, {'title': '未麻的部屋', 'year': 1997}, {'title': '怪兽电力公司', 'year': 2001}, {'title': '哈利·波特与火焰杯', 'year': 2005}, {'title': '玩具总动员3', 'year': 2010}, {'title': '傲慢与偏见', 'year': 2005}, {'title': '釜山行', 'year': 2016}, {'title': '玛丽和马克思', 'year': 2009}, {'title': '神偷奶爸', 'year': 2010}, {'title': '新世界', 'year': 2013}, {'title': '被解救的姜戈', 'year': 2012}, {'title': '告白', 'year': 2010}, {'title': '大鱼', 'year': 2003}, {'title': '哪吒闹海', 'year': 1979}, {'title': '射雕英雄传之东成西就', 'year': 1993}, {'title': '阳光姐妹淘', 'year': 2011}, {'title': '头号玩家', 'year': 2018}, {'title': '喜宴', 'year': 1993}, {'title': '我是山姆', 'year': 2001}, {'title': '模仿游戏', 'year': 2014}, {'title': '恐怖直播', 'year': 2013}, {'title': '血战钢锯岭', 'year': 2016}, {'title': '花样年华', 'year': 2000}, {'title': '九品芝麻官', 'year': 1994}, {'title': '七武士', 'year': 1954}, {'title': '头脑特工队', 'year': 2015}, {'title': '茶馆', 'year': 1982}, {'title': '色，戒', 'year': 2007}, {'title': '黑客帝国3：矩阵革命', 'year': 2003}, {'title': '惊魂记', 'year': 1960}, {'title': '你的名字。', 'year': 2016}, {'title': '电锯惊魂', 'year': 2004}, {'title': '三块广告牌', 'year': 2017}, {'title': '达拉斯买家俱乐部', 'year': 2013}, {'title': '疯狂原始人', 'year': 2013}, {'title': '心迷宫', 'year': 2014}, {'title': '卢旺达饭店', 'year': 2004}, {'title': '上帝之城', 'year': 2002}, {'title': '谍影重重3', 'year': 2007}, {'title': '英雄本色', 'year': 1986}, {'title': '风之谷', 'year': 1984}, {'title': '海街日记', 'year': 2015}, {'title': '纵横四海', 'year': 1991}, {'title': '爱在午夜降临前', 'year': 2013}, {'title': '绿里奇迹', 'year': 1999}, {'title': '记忆碎片', 'year': 2000}, {'title': '岁月神偷', 'year': 2010}, {'title': '忠犬八公物语', 'year': 1987}, {'title': '荒蛮故事', 'year': 2014}, {'title': '疯狂的石头', 'year': 2006}, {'title': '雨中曲', 'year': 1952}, {'title': '小偷家族', 'year': 2018}, {'title': '爆裂鼓手', 'year': 2014}, {'title': '无敌破坏王', 'year': 2012}, {'title': '背靠背，脸对脸', 'year': 1994}, {'title': '2001太空漫游', 'year': 1968}, {'title': '贫民窟的百万富翁', 'year': 2008}, {'title': '小丑', 'year': 2019}, {'title': '冰川时代', 'year': 2002}, {'title': '无间道2', 'year': 2003}, {'title': '恐怖游轮', 'year': 2009}, {'title': '东邪西毒', 'year': 1994}, {'title': '真爱至上', 'year': 2003}, {'title': '心灵奇旅', 'year': 2020}, {'title': '牯岭街少年杀人事件', 'year': 1991}, {'title': '你看起来好像很好吃', 'year': 2010}, {'title': '遗愿清单', 'year': 2007}, {'title': '魔女宅急便', 'year': 1989}, {'title': '东京教父', 'year': 2003}, {'title': '黑天鹅', 'year': 2010}, {'title': '大佛普拉斯', 'year': 2017}, {'title': '可可西里', 'year': 2004}, {'title': '城市之光', 'year': 1931}, {'title': '雨人', 'year': 1988}, {'title': '源代码', 'year': 2011}, {'title': '恋恋笔记本', 'year': 2004}, {'title': '海边的曼彻斯特', 'year': 2016}, {'title': '初恋这件小事', 'year': 2010}, {'title': '人工智能', 'year': 2001}, {'title': '虎口脱险', 'year': 1966}, {'title': '波西米亚狂想曲', 'year': 2018}, {'title': '青蛇', 'year': 1993}, {'title': '萤火虫之墓', 'year': 1988}, {'title': '终结者2：审判日', 'year': 1991}, {'title': '罗生门', 'year': 1950}, {'title': '疯狂的麦克斯4：狂暴之路', 'year': 2015}, {'title': '新龙门客栈', 'year': 1992}, {'title': '千钧一发', 'year': 1997}, {'title': '奇迹男孩', 'year': 2017}, {'title': '无耻混蛋', 'year': 2009}, {'title': '崖上的波妞', 'year': 2008}, {'title': '二十二', 'year': 2015}, {'title': '彗星来的那一夜', 'year': 2013}, {'title': '末路狂花', 'year': 1991}, {'title': '黑客帝国2：重装上阵', 'year': 2003}, {'title': '血钻', 'year': 2006}, {'title': '房间', 'year': 2015}, {'title': '爱乐之城', 'year': 2016}, {'title': '花束般的恋爱', 'year': 2021}, {'title': '步履不停', 'year': 2008}, {'title': '战争之王', 'year': 2005}, {'title': '魂断蓝桥', 'year': 1940}, {'title': '火星救援', 'year': 2015}, {'title': '谍影重重2', 'year': 2004}, {'title': '千年女优', 'year': 2001}, {'title': '哈利·波特与死亡圣器(上)', 'year': 2010}, {'title': '芙蓉镇', 'year': 1987}, {'title': '燃情岁月', 'year': 1994}, {'title': '弱点', 'year': 2009}, {'title': '阿飞正传', 'year': 1990}, {'title': '谍影重重', 'year': 2002}, {'title': '朗读者', 'year': 2008}, {'title': '再次出发之纽约遇见你', 'year': 2013}, {'title': '香水', 'year': 2006}, {'title': '海洋', 'year': 2009}, {'title': '穿越时空的少女', 'year': 2006}, {'title': '哈利·波特与凤凰社', 'year': 2007}, {'title': '地球上的星星', 'year': 2007}]
# IMDBTop250 = ['肖申克的救赎', '教父', '教父2', '蝙蝠侠：黑暗骑士', '十二怒汉', '辛德勒的名单', '指环王3：国王归来', '低俗小说', '黄金三镖客', '指环王1：魔戒现身', '搏击俱乐部', '阿甘正传', '盗梦空间', '指环王2：双塔奇兵', '星球大战2：帝国反击战', '黑客帝国', '好家伙', '飞越疯人院', '七武士', '七宗罪', '美丽人生', '上帝之城', '沉默的羔羊', '生活多美好', '星球大战', '拯救大兵瑞恩', '绿里奇迹', '千与千寻', '星际穿越', '寄生虫', '这个杀手不太冷', '切腹', '非常嫌疑犯', '狮子王', '钢琴家', '回到未来', '终结者2', '美国X档案', '摩登时代', '角斗士', '惊魂记', '无间行者', '城市之光', '触不可及', '爆裂鼓手', '萤火虫之墓', '致命魔术', '西部往事', '卡萨布兰卡', '天堂电影院', '后窗', '异形', '现代启示录', '记忆碎片', '大独裁者', '夺宝奇兵', '被解救的姜戈', '汉密尔顿', '窃听风暴', '光荣之路', '小丑', '机器人总动员', '闪灵', '复仇者联盟3：无限战争', '日落大道', '控方证人', '老男孩', '蜘蛛侠：平行宇宙', '幽灵公主', '奇爱博士', '蝙蝠侠：黑暗骑士崛起', '美国往事', '你的名字', '异形2', '寻梦环游记', '复仇者联盟4：终局之战', '美国美人', '何以为家', '勇敢的心', '从海底出击', '玩具总动员', '三傻大闹宝莱坞', '天国与地狱', '莫扎特传', '无耻混蛋', '星球大战3：绝地归来', '心灵捕手', '地球上的星星', '落水狗', '2001太空漫游', '梦之安魂曲', '迷魂记', 'M就是凶手', '狩猎', '美丽心灵的永恒阳光', '公民凯恩', '摔跤吧！爸爸', '雨中曲', '偷自行车的人', '全金属外壳', '寻子遇仙记', '自己去看', '偷拐抢骗', '西北偏北', '发条橙子', '疤面煞星', '生之欲', '1917', '出租车司机', '焦土之城', '一次别离', '阿拉伯的劳伦斯', '玩具总动员3', '骗中骗', '天使爱美丽', '大都会', '桃色公寓', '黄昏双镖客', '双重赔偿', '杀死一只知更鸟', '飞屋环游记', '夺宝奇兵3', '盗火线', '洛城机密', '虎胆龙威', '绿皮书', '巨蟒与圣杯', '蝙蝠侠：侠影之谜', '用心棒', '罗生门', '帝国的毁灭', '小鞋子', '不可饶恕', '乱', '热情似火', '哈尔的移动城堡', '彗星美人', '赌城风云', '美丽心灵', '华尔街之狼', '大逃亡', '潘神的迷宫', '谜一样的双眼', '血色将至', '两杆大烟枪', '纽伦堡大审判', '龙猫', '愤怒的公牛', '碧血金沙', '电话谋杀案', '三块广告牌', '禁闭岛', '淘金记', '唐人街', '我的父亲，我的儿子', '老无所依', 'V字仇杀队', '头脑特工队', '象人', '怪形', '第七封印', '勇士', '灵异第六感', '猜火车', '侏罗纪公园', '克劳斯：圣诞节的秘密', '楚门的世界', '乱世佳人', '海底总动员', '潜行者', '野草莓', '银翼杀手', '杀死比尔', '杀人回忆', '恶魔', '桂河大桥', '冰血暴', '房间', '荒蛮故事', '老爷车', '第三人', '东京物语', '码头风云', '猎鹿人', '因父之名', '玛丽和马克思', '布达佩斯大饭店', '爱在黎明破晓前', '消失的爱人', '猫鼠游戏', '血战钢锯岭', '快乐的阿南', '囚徒', '假面', '调音师', '福尔摩斯二世', '谋杀绿脚趾', '秋日奏鸣曲', '你逃我也逃', '将军号', '乱世儿女', '驯龙高手', '极速车王', '强盗', '为奴十二年', '史密斯先生到华盛顿', '疯狂的麦克斯4：狂暴之路', '死亡诗社', '百万美元宝贝', '电视台风云', '伴我同行', '哈利·波特与死亡圣器(下)', '宾虚', '忠犬八公的故事', '心灵奇旅', '铁窗喋血', '小姐', '野战排', '金刚狼3：殊死一战', '荒野生存', '极速风流', '恐惧的代价', '万世魔星', '怒火青春', '四百击', '圣女贞德蒙难记', '聚焦', '卢旺达饭店', '爱情是狗娘', '瓦塞浦黑帮', '安德烈·卢布廖夫', '洛奇', '怪兽电力公司', '风之谷', '流浪者之歌', '蝴蝶梦', '爱在日落黄昏时', '芭萨提的颜色', '男人的争斗', '花样年华', '德州巴黎', '一夜风流', '燃烧女子的肖像', '误杀瞒天记', '较量', '声之形', '看不见的客人', '阿尔及尔之战', '帮助', '故土']
# DouBanTop250 = ['肖申克的救赎', '霸王别姬', '阿甘正传', '泰坦尼克号', '这个杀手不太冷', '美丽人生', '千与千寻', '辛德勒的名单', '盗梦空间', '星际穿越', '忠犬八公的故事', '楚门的世界', '海上钢琴师', '三傻大闹宝莱坞', '机器人总动员', '放牛班的春天', '无间道', '疯狂动物城', '大话西游之大圣娶亲', '控方证人', '熔炉', '教父', '当幸福来敲门', '触不可及', '怦然心动', '龙猫', '末代皇帝', '寻梦环游记', '蝙蝠侠：黑暗骑士', '活着', '哈利·波特与魔法石', '指环王3：王者无敌', '乱世佳人', '素媛', '飞屋环游记', '我不是药神', '摔跤吧！爸爸', '何以为家', '十二怒汉', '哈尔的移动城堡', '鬼子来了', '少年派的奇幻漂流', '猫鼠游戏', '让子弹飞', '大话西游之月光宝盒', '天空之城', '钢琴家', '海蒂和爷爷', '指环王2：双塔奇兵', '闻香识女人', '天堂电影院', '罗马假日', '大闹天宫', '指环王1：护戒使者', '黑客帝国', '死亡诗社', '绿皮书', '教父2', '狮子王', '辩护人', '搏击俱乐部', '饮食男女', '美丽心灵', '本杰明·巴顿奇事', '穿条纹睡衣的男孩', '窃听风暴', '情书', '两杆大烟枪', '西西里的美丽传说', '音乐之声', '看不见的客人', '拯救大兵瑞恩', '飞越疯人院', '小鞋子', '阿凡达', '哈利·波特与死亡圣器(下)', '沉默的羔羊', '致命魔术', '禁闭岛', '布达佩斯大饭店', '海豚湾', '蝴蝶效应', '美国往事', '心灵捕手', '低俗小说', '春光乍泄', '摩登时代', '功夫', '喜剧之王', '七宗罪', '哈利·波特与阿兹卡班的囚徒', '超脱', '致命ID', '杀人回忆', '红辣椒', '加勒比海盗', '狩猎', '被嫌弃的松子的一生', '7号房的礼物', '请以你的名字呼唤我', '哈利·波特与密室', '唐伯虎点秋香', '剪刀手爱德华', '一一', '断背山', '勇敢的心', '入殓师', '第六感', '爱在黎明破晓前', '重庆森林', '蝙蝠侠：黑暗骑士崛起', '幽灵公主', '天使爱美丽', '菊次郎的夏天', '小森林 夏秋篇', '阳光灿烂的日子', '超能陆战队', '爱在日落黄昏时', '完美的世界', '无人知晓', '消失的爱人', '甜蜜蜜', '借东西的小人阿莉埃蒂', '倩女幽魂', '小森林 冬春篇', '侧耳倾听', '时空恋旅人', '幸福终点站', '驯龙高手', '萤火之森', '寄生虫', '教父3', '怪兽电力公司', '一个叫欧维的男人决定去死', '玛丽和马克思', '未麻的部屋', '玩具总动员3', '傲慢与偏见', '神偷奶爸', '釜山行', '大鱼', '告白', '被解救的姜戈', '哈利·波特与火焰杯', '阳光姐妹淘', '射雕英雄传之东成西就', '新世界', '哪吒闹海', '我是山姆', '恐怖直播', '头号玩家', '模仿游戏', '血战钢锯岭', '喜宴', '七武士', '花样年华', '头脑特工队', '黑客帝国3：矩阵革命', '九品芝麻官', '电锯惊魂', '三块广告牌', '惊魂记', '你的名字。', '达拉斯买家俱乐部', '卢旺达饭店', '疯狂原始人', '上帝之城', '心迷宫', '谍影重重3', '英雄本色', '风之谷', '色，戒', '纵横四海', '海街日记', '茶馆', '岁月神偷', '记忆碎片', '爱在午夜降临前', '绿里奇迹', '忠犬八公物语', '荒蛮故事', '爆裂鼓手', '小偷家族', '疯狂的石头', '贫民窟的百万富翁', '无敌破坏王', '雨中曲', '东邪西毒', '冰川时代', '真爱至上', '恐怖游轮', '2001太空漫游', '你看起来好像很好吃', '黑天鹅', '无间道2', '魔女宅急便', '牯岭街少年杀人事件', '背靠背，脸对脸', '遗愿清单', '小丑', '雨人', '大佛普拉斯', '可可西里', '恋恋笔记本', '城市之光', '东京教父', '源代码', '初恋这件小事', '萤火虫之墓', '虎口脱险', '人工智能', '海边的曼彻斯特', '心灵奇旅', '罗生门', '青蛇', '波西米亚狂想曲', '终结者2：审判日', '疯狂的麦克斯4：狂暴之路', '新龙门客栈', '奇迹男孩', '二十二', '无耻混蛋', '房间', '千钧一发', '血钻', '崖上的波妞', '彗星来的那一夜', '黑客帝国2：重装上阵', '步履不停', '魂断蓝桥', '战争之王', '爱乐之城', '末路狂花', '谍影重重2', '火星救援', '燃情岁月', '千年女优', '阿飞正传', '花束般的恋爱', '再次出发之纽约遇见你', '谍影重重', '朗读者', '海洋', '香水', '穿越时空的少女', '地球上的星星', '我爱你', '哈利·波特与死亡圣器(上)', '弱点', '完美陌生人']

new_douban_top250_list = server.common.get_cache('top250', 'douban') or []
new_imdb_top250_list = server.common.get_cache('top250', 'imdb') or []

if len(new_imdb_top250_list) == 250:
    if set(IMDBTop250) != set(new_imdb_top250_list):
        IMDBTop250 = new_imdb_top250_list
        logger.info(f"{plugins_name} IMDB TOP250 数据有更新，共 {len(IMDBTop250)} 项")
        logger.info(f"{plugins_name} 最新 IMDB TOP250 数据：{IMDBTop250}")

if len(new_douban_top250_list) == 250:
    if set(DouBanTop250) != set(new_douban_top250_list):
        DouBanTop250 = new_douban_top250_list
        logger.info(f"{plugins_name} 豆瓣 TOP250 数据有更新，共 {len(DouBanTop250)} 项")
        logger.info(f"{plugins_name} 最新豆瓣 TOP250 数据：{DouBanTop250}")

tags = {
    "Action": "动作",
    "Adventure": "冒险",
    "Animation": "动画",
    "Anime": "动画",
    "Mini-Series": "短剧",
    "War & Politics": "政治",
    "Sci-Fi & Fantasy": "科幻",
    "Suspense": "悬疑",
    "Reality": "记录",
    "Comedy": "喜剧",
    "Crime": "犯罪",
    "Documentary": "纪录",
    "Drama": "剧情",
    "Family": "家庭",
    "Awards Show": "颁奖典礼",
    "Fantasy": "奇幻",
    "History": "历史",
    "Horror": "恐怖",
    "Music": "音乐",
    "Adult": "成人",
    "Mystery": "悬疑",
    "Romance": "爱情",
    "Science Fiction": "科幻",
    "Sport": "体育",
    "Thriller": "惊悚",
    "War": "战争",
    "Western": "西部",
    "Biography": "传记",
    "Film-noir": "黑色",
    "Musical": "音乐",
    "Sci-Fi": "科幻",
    "Tv Movie": "电视",
    "Disaster": "灾难",
    "Children": "儿童",
    "Martial Arts": "武术",
    "Talk": "访谈",
    "Short": "短剧",
    "Game Show": "游戏",
    "Food": "美食",
    "Home and Garden": "家居园艺",
    "Travel": "旅行",
    "News": "新闻",
    "Soap": "肥皂剧",
    "Talk Show": "脱口秀",
    "Film-Noir": "黑色",
    "Indie": "独立",
}
max_retry = 10
session = requests.Session()
retry = Retry(connect=max_retry, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

class plex_sortout:
    def __init__(self):
        self.connected = False

    def connect_plex(self):
        try:
            self.plexserver = PlexServer(self.config_plex_url, self.config_plex_token)
            self.connected = True
            logger.info(f"{plugins_name}PLEX 服务器连接成功")
        except Exception as e:
            logger.error(f"{plugins_name}PLEX 服务器守护连接失败，原因：{e}")

    # def setdata(self,plex,mrserver,servertype):
    #     self.plexserver = plex
    #     self.mrserver = mrserver
    #     self.servertype = servertype
    
    def setconfig(self,config):
        self.config = config
        self.config_plex_url = self.config.get('plex_url')
        self.config_plex_token = self.config.get('plex_token')
        # 创建守护线程来连接Plex服务器
        def keep_connection():
            while True:
                if not self.connected:
                    self.connect_plex()
                time.sleep(60)
        connection_thread = threading.Thread(target=keep_connection)
        connection_thread.setDaemon(True)
        connection_thread.start()
        time.sleep(10)
        self.config_Collection = self.config.get('Collection')
        self.config_Poster = self.config.get('Poster')
        self.config_Genres = self.config.get('Genres')
        self.config_SortTitle = self.config.get('SortTitle')
        self.config_Top250 = self.config.get('Top250')
        self.config_SelfGenres = self.config.get('SelfGenres')
        self.config_LIBRARY = self.config.get('LIBRARY')
        self.config_mbot_url = self.config.get('mbot_url')
        self.config_mbot_api_key = self.config.get('mbot_api_key')
        # 开启webhooks开关
        self.plexserver.settings.get('webHooksEnabled').set(True)
        self.plexserver.settings.get('pushNotificationsEnabled').set(True)
        self.plexserver.settings.save()
        # settings_info = self.plexserver.settings
        # all_setting=settings_info._settings
        # ww = self.plexserver.settings.get('webHooksEnabled')
        # ds = self.plexserver.settings.get('pushNotificationsEnabled')
        if self.config_mbot_url and self.config_mbot_api_key:
            webhook_url = f'{self.config_mbot_url}/api/plugins/get_plex_event/webhook?access_key={self.config_mbot_api_key}'
            # 自动设置 webhooks
            account = self.plexserver.myPlexAccount()
            webhooks = account.webhooks()
            if webhook_url not in webhooks:
                webhooks.append(webhook_url)
                account.setWebhooks(webhooks)
                logger.info(f"{plugins_name} 已向 PLEX 服务器添加 Webhook")
            else:
                logger.info(f"{plugins_name} PLEX 服务器 Webhook 列表中已添加此 Webhook 链接：{webhook_url}")
            
    def uniqify(self, seq):
        keys = {}
        for e in seq:
            keys[e] = 1
        return keys.keys()

    def check_contain_chinese(self, check_str):
        for ch in check_str:
            if '\u4e00' <= ch <= '\u9fff':
                return True
        return False

    # chinese to pyinyin
    def chinese2pinyin(self, chinesestr):  
        pyinyin_list = []
        pinyin = pypinyin.pinyin(chinesestr, style=pypinyin.FIRST_LETTER, heteronym=True)
        for i in range(len(pinyin)):
            pyinyin_list.append(str(pinyin[i][0]).upper())
        pyinyin_str = ''.join(pyinyin_list)
        return pyinyin_str

    # 去除标点符号（只留字母、数字、中文)
    def removePunctuation(self, query):
        if query:
            rule = re.compile(u"[^a-zA-Z0-9]")
            query = rule.sub('', query)
        return query
    def judgegenre(self, genres):
        for tag in genres:
            enggenre = tag.tag
            if enggenre in tags.keys():
                return True
        return False

    def updategenre(self, video, spare_flag, genres, add_new):
        englist = []
        chlist = []
        enggenre = ''
        zhQuery = ''
        for tag in genres:
            if spare_flag:
                enggenre = tag
            else:
                enggenre = tag.tag
            if enggenre in tags.keys():
                englist.append(enggenre)
                zhQuery = tags[enggenre]
                chlist.append(zhQuery) 
        if len(englist) > 0:
            video.addGenre(chlist, locked=False)
            video.removeGenre(englist, locked=True)
        else:
            video.addGenre(chlist, locked=True)
        if chlist:
            logger.info(f"「{video.title}」标签翻译整理完成 {chlist}")
        else:
            logger.info(f"「{video.title}」的标签都是中文，不需要翻译")
        if add_new and englist:
            for i in range(3):
                try:
                    video.reload(genres=True)
                    # video.reload()
                    break
                except Exception as e:
                    logger.info(f"「{video.title}」第 {i+1}/3 次与 PLEX 服务器同步翻译项失败，原因：{e}")
                    time.sleep(5)
                    continue
            
    #获取 PLEX 服务器所有媒体库
    def get_library(self):
        libtable = []
        lib = {}
        for section in self.plexserver.library.sections():
            #输出所有媒体库
            logger.info(f'{section.title} {section.key}')
            lib['name']=section.title
            lib['value']=section.title
            libtable.append(lib.copy())
        return libtable
    # def get_library(self):
    #     libtable0 = []
    #     libtable = []
    #     lib = {}
    #     for section in self.plexserver.library.sections():
    #         section_id = str(section.key).zfill(2)
    #         libtable0.append(f"│ {section.title:<6} │ {section_id:^4} │".replace(" ", "\u3000"))
    #         lib['name']=section.title
    #         lib['value']=section.title
    #         libtable.append(lib.copy())
    #     header = "\n┌—————————————┬—————————┐\n│　媒体库　　　　│　　编号　│\n├—————————————┼—————————┤\n"
    #     footer = "└—————————————┴—————————┘"
    #     table = header + "\n".join(libtable0) + "\n" + footer
    #     logger.info(f'{table} ')
    #     return libtable

    def get_video_info(self, video):
        genres_all = []
        locked_info = []
        guids = []
        
        metadata_key = video.key
        metadata_url = f'{self.config_plex_url}{metadata_key}?X-Plex-Token={self.config_plex_token}'
        response = session.request("GET", metadata_url, timeout=60)

        if response.status_code == 200:
            xml_string = response.content
            xml_string = xml_string.decode("utf-8").replace("<?xml version=\"1.0\" encoding=\"utf-8\"?>", "").encode("utf-8")
            root = etree.fromstring(xml_string)

            for genre in root.xpath(".//Genre"):
                genre_tag = genre.get("tag")
                genres_all.append(genre_tag)
        
            for field in root.xpath(".//Field"):
                field_name = field.get("name")
                locked_info.append(field_name)

            for guid in root.xpath(".//Guid"):
                guid_id = guid.get("id")
                guids.append(guid_id)
        else:
            logger.error(f"「{video.title}」获取影片信息失败")
        return locked_info, genres_all, guids

    def get_locked_info(self, video, spare_flag):
        locked_info = []
        genres_all = []
        guids = []
        reconnect_flag = False
        for i in range(max_retry):
            try:
                title = video.title
                if not spare_flag:
                    fields = video.fields
                    for field in fields:
                        locked_info.append(field.name)
                else:
                    locked_info, genres_all, guids = self.get_video_info(video)

                if locked_info:
                    logger.info(f'「{title}」当前元数据锁定情况：{locked_info}')
                else:
                    logger.info(f'「{title}」当前没有锁定任何元数据')
                break
            except ConnectTimeoutError as e:
                logger.error(f"{plugins_name}第 {i+1}/{max_retry} 次获取 ['{title}'] 元数据锁定情况，连接失败等待10秒重连，原因：{e}")
                time.sleep(10)
                self.connected = False
                self.connect_plex()
                reconnect_flag = True
                spare_flag = not spare_flag
                continue
            except Exception as e:
                logger.error(f"{plugins_name}第 {i+1}/{max_retry} 次获取 ['{title}'] 元数据锁定情况失败，原因：{e}")
                time.sleep(2)
                spare_flag = not spare_flag
                continue
        video_info = {
            'locked_info': locked_info,
            'spare_flag': spare_flag,
            'genres_all': genres_all,
            'guids': guids
        }
        return video, video_info
        
    # 解锁海报和背景
    def process_unlock_poster_and_art(self,video):
        reconnect_flag = False
        for i in range(max_retry):
            try:
                title = video.title
                # if reconnect_flag:
                #     video.reload()
                video.unlockArt()
                video.unlockPoster()
                logger.info(f'「{video.title}」海报和背景已经解锁，PLEX 服务器可以自动更新了\n')
                break
            except ConnectTimeoutError as e:
                logger.error(f"{plugins_name}第 {i+1}/{max_retry} 次解锁 ['{title}'] 海报和背景异常，原因：{e}")
                time.sleep(10)
                self.connected = False
                self.connect_plex()
                reconnect_flag = True
                continue
            except Exception as e:
                logger.error(f"{plugins_name}第 {i+1}/{max_retry} 次解锁 ['{title}'] 海报和背景异常，原因：{e}")
                time.sleep(2)
                continue

    # 锁定海报和背景
    def process_lock_poster_and_art(self,video):
        reconnect_flag = False
        for i in range(max_retry):
            try:
                title = video.title
                # if reconnect_flag:
                #     video.reload()
                video.lockArt()
                video.lockPoster()
                logger.info(f'「{video.title}」海报和背景已经锁定，PLEX 服务器不会再自动更新了\n')
                break
            except ConnectTimeoutError as e:
                logger.error(f"{plugins_name}第 {i+1}/{max_retry} 次锁定 ['{title}'] 海报和背景异常，原因：{e}")
                time.sleep(10)
                self.connected = False
                self.connect_plex()
                reconnect_flag = True
                continue
            except Exception as e:
                logger.error(f"{plugins_name}第 {i+1}/{max_retry} 次锁定 ['{title}'] 海报和背景异常，原因：{e}")
                time.sleep(10)
                continue
    # 筛选fanart封面
    def process_fanart(self,video,video_info):
        locked_info = video_info.get('locked_info','')
        reconnect_flag = False
        for i in range(max_retry):
            try:
                title = video.title
                if {'art', 'thumb'}.issubset(field_names for field_names in locked_info):
                    logger.info(f'「{title}」当前海报和背景已经锁定，不做修改！')
                    return
                # TypeDic={
                #     'show':MediaType.TV,
                #     'movie':MediaType.Movie
                # }
                if 'thumb' not in locked_info:
                    posters = video.posters()
                    if len(posters) > 0:
                        has_fanart_poster = False
                        for poster in posters:
                            if poster.provider == 'fanarttv' and poster.selected:
                                logger.info(f'「{title}」当前选择的海报已经是 Fanart 封面，不做修改！')
                                has_fanart_poster = True
                                break
                            elif poster.provider == 'fanarttv':
                                # 设置当前海报为展示海报
                                video.setPoster(poster)
                                logger.info(f'「{title}」Fanart 海报筛选完成,并已锁定，PLEX 服务器不会再自动更新了')
                                has_fanart_poster = True
                                break
                        if not has_fanart_poster:
                            logger.info(f'「{title}」在 Fanart 中没有海报')
                        # 锁定海报元数据
                        video.lockPoster()
                    else:
                        logger.info(f'「{title}」没有海报')
                else:
                    logger.info(f'「{title}」当前选择的海报已经锁定，不做修改！')

                if 'art' not in locked_info:
                    arts = video.arts()
                    # logger.info(f'「{video.title}」arts:{arts}')
                    if len(arts) > 0:
                        has_fanart_art = False
                        for art in arts:
                            if art.provider == 'fanarttv' and art.selected:
                                logger.info(f'「{video.title}」当前选择的背景已经是 Fanart 背景，不做修改！')
                                has_fanart_art = True
                                return
                            elif art.provider == 'fanarttv':
                                # 设置选中当前背景为展示背景
                                video.setArt(art)
                                logger.info(f'「{video.title}」Fanart 背景筛选完成,并已锁定，PLEX 服务器不会再自动更新了')
                                has_fanart_art = True
                                break
                        if not has_fanart_art:
                            logger.info(f'「{video.title}」在 Fanart 中没有背景')
                        # 锁定背景元数据
                        video.lockArt()
                    else:
                        logger.info(f'「{video.title}」没有背景')
                else:
                    logger.info(f'「{title}」当前选择的背景已经锁定，不做修改！')
                break
            except ConnectTimeoutError as e:
                logger.error(f"{plugins_name}第 {i+1}/{max_retry} 次处理 ['{title}'] Fanart 封面筛选异常，连接失败等待10秒重连，原因：{e}")
                time.sleep(10)
                self.connected = False
                self.connect_plex()
                reconnect_flag = True
                continue
            except Exception as e:
                logger.error(f"{plugins_name}第 {i+1}/{max_retry} 次处理 ['{title}'] Fanart 封面筛选异常，原因：{e}")
                time.sleep(10)
                continue
            
    # 排序修改为首字母
    def process_sorttitle(self,video,video_info):
        locked_info = video_info.get('locked_info','')
        reconnect_flag = False
        for i in range(max_retry):
            try:
                title = video.title
                video_titleSort = video.titleSort
                if 'titleSort' not in locked_info:
                    # video.editTags(tag="actor", items=[x.tag for x in video.actors], remove=True)
                    if video_titleSort:  # 判断是否已经有标题
                        con = video_titleSort
                        if (self.check_contain_chinese(con) or RECOVER):
                            SortTitle = self.chinese2pinyin(title)
                            SortTitle = self.removePunctuation(SortTitle)
                            try:
                                video.editSortTitle(SortTitle)
                                logger.info(f"「{title}」排序已修改为首字母 ['{SortTitle}']\n")
                            except Exception as e:
                                logger.error(f"「{title}」首字母排序失败,原因：{e}\n")
                else:
                    logger.info(f"「{title}」排序首字母为 ['{video_titleSort}']已锁定，不需要重新排序\n")
                break
            except ConnectTimeoutError as e:
                logger.error(f"{plugins_name}第 {i+1}/{max_retry} 次处理 ['{title}'] 首字母排序异常，连接失败等待10秒重连，原因：{e}")
                time.sleep(10)
                self.connected = False
                self.connect_plex()
                reconnect_flag = True
                continue
            except Exception as e:
                logger.error(f"{plugins_name}第 {i+1}/{max_retry} 次处理 ['{title}'] 首字母排序异常，原因：{e}")
                time.sleep(2)
                continue

    def add_top250(self,video,video_info):
        spare_flag = video_info.get('spare_flag','')
        genres_all = video_info.get('genres_all','')
        title = video.title
        # 获取 imdb_id, tt22399058,[<Guid:imdb://tt0499549>, <Guid:tmdb://19995>, <Guid:tvdb://165>]
        if spare_flag:
            guids = video_info.get('guids','')
        else:
            guids = video.guids
        imdb_id = ''
        for guid in guids:
            if spare_flag:
                if 'imdb' in guid:
                    imdb_id = guid.replace('imdb://','')
                    break
            else:
                if 'imdb' in guid.id:
                    imdb_id = guid.id.replace('imdb://','')
                    break
        if imdb_id:
            for name in IMDBTop250:
                hastag = False
                if name == imdb_id:
                    if spare_flag:
                        for tag in genres_all:
                            if tag == "IMDB TOP 250":
                                hastag = True
                                break
                    else:
                        for tag in video.genres:
                            if tag.tag == "IMDB TOP 250":
                                hastag = True
                                break
                    if hastag:
                        logger.info(f"「{title}」已有 ['IMDB TOP 250'] 标签，不用再添加")
                        break
                    chlist = []
                    chlist.append("IMDB TOP 250")
                    video.addGenre(chlist, locked=True)
                    logger.info(f"「{title}」已添加 ['IMDB TOP 250'] 标签")
        # 获取影片 tmdb_id, 使用唯一的id进行匹配，防止重名
        tmdb_id = ''
        for guid in guids:
            if spare_flag:
                if 'tmdb' in guid:
                    tmdb_id = guid.replace('tmdb://','')
                    break
            else:
                if 'tmdb' in guid.id:
                    tmdb_id = guid.id.replace('tmdb://','')
                    break
            
        if tmdb_id:
            for name in DouBanTop250:
                hastag = False
                if name == int(tmdb_id):
                    if spare_flag:
                        for tag in genres_all:
                            if tag == "豆瓣TOP 250":
                                hastag = True
                                break
                    else:
                        for tag in video.genres:
                            if tag.tag == "豆瓣TOP 250":
                                hastag = True
                                break
                    if hastag:
                        logger.info(f"「{title}」已有 ['豆瓣TOP 250'] 标签，不用再添加")
                        break
                    chlist = []
                    chlist.append("豆瓣TOP 250")
                    video.addGenre(chlist, locked=True)
                    logger.info(f"「{title}」已添加 ['豆瓣TOP 250'] 标签")

    def process_tag(self,video,video_info,add_new):
        spare_flag = video_info.get('spare_flag',False)
        genres_all = video_info.get('genres_all','')
        reconnect_flag = False
        error_flag = False
        genres = None
        for i in range(max_retry):
            try:
                title = video.title
                # if not reconnect_flag and not error_flag and not spare_flag:
                if not spare_flag:
                    video.reload(genres=True)
                    # video.reload()
                    genres = video.genres
                if (reconnect_flag or error_flag) and spare_flag:
                    video, video_info = self.get_locked_info(video,True)
                    locked_info = video_info.get('locked_info','')
                    spare_flag = video_info.get('spare_flag',True)
                    genres_all = video_info.get('genres_all','')
                selftag=self.config_SelfGenres.split(',')
                for tag in selftag:
                    tags[tag.split(':')[0]]=tag.split(':')[1]
                
                if spare_flag:
                    genres = genres_all
                if genres:
                    self.updategenre(video, spare_flag, genres, add_new)
                else:
                    logger.info(f"「{title}」没有标签，不需要翻译")
                # 只有电影类型才需要添加 TOP250 标签
                if self.config_Top250 and video.type == 'movie':
                    video_info['spare_flag'] = spare_flag
                    video_info['genres_all'] = genres
                    self.add_top250(video, video_info)
                break
            except ConnectTimeoutError as e:
                logger.error(f"{plugins_name}第 {i+1}/{max_retry} 次处理 ['{title}'] 标签翻译异常，连接失败等待10秒重连，原因：{e}")
                time.sleep(10)
                self.connected = False
                self.connect_plex()
                reconnect_flag = True
                error_flag = True
                spare_flag = not spare_flag
                continue
            except Exception as e:
                logger.error(f"{plugins_name}第 {i+1}/{max_retry} 次处理 ['{title}'] 标签翻译异常，原因：{e}")
                spare_flag = not spare_flag
                time.sleep(2)
                error_flag = True
                continue

    def how_long(self, num):
        total_seconds = num * 3.6
        # 计算分钟数和秒数
        minutes, seconds = divmod(total_seconds, 60)
        if minutes == 0:
            # 小于 1 分钟
            how_long = f"{int(seconds)} 秒"
        elif minutes < 60:
            # 1 分钟到 1 小时之间
            how_long = f"{int(minutes)} 分钟"
        else:
            # 大于等于 1 小时
            hours, remaining_minutes = divmod(minutes, 60)
            how_long = f"{int(hours)} 小时 {int(remaining_minutes)} 分钟"
        return how_long

    def thread_process_all(self, videos,is_lock,group_now,spare_flag):
        video_num = len(videos)
        for video,i in zip(videos,range(video_num)):
            video_percent = f"{round(((i+1)/video_num)*100, 1)}%"
            if video_percent == '100.0%':
                logger.info(f"{plugins_name}开始处理 {group_now} 分组第 {i+1} 部影片：['{video.title}']，已完成 100%，这是当前分组需要处理的最后一部影片")
            else:
                now_video_count = int(video_num - i - 1)
                logger.info(f"{plugins_name}开始处理 {group_now} 分组第 {i+1} 部影片：['{video.title}']，已完成 {video_percent}，当前分组剩余 {now_video_count} 部影片需要处理，还需要 {self.how_long(now_video_count)}")
            # 获取元数据锁定情况
            # video, locked_info, spare_flag, genres_all = self.get_locked_info(video)
            video, video_info = self.get_locked_info(video, spare_flag)
            if is_lock == 'run_locked':
                self.process_lock_poster_and_art(video)
            elif is_lock == 'run_unlocked':
                self.process_unlock_poster_and_art(video)
            else:   
                #fanart筛选
                if self.config_Poster:
                    self.process_fanart(video,video_info)
                #标签翻译整理
                if self.config_Genres:
                    self.process_tag(video, video_info, False)
                #首字母排序
                if self.config_SortTitle:
                    self.process_sorttitle(video,video_info)
        result = {
            "run_locked": f"{group_now} 分组锁定海报和背景完成!",
            "run_unlocked": f"{group_now} 分组解锁海报和背景完成!",
            "run_all": f"{group_now} 分组运行整理完成!"
        }
        logger.info(f"{plugins_name}{result[is_lock]}")
        
    # 手动选择媒体库整理
    def process_all(self,library,sortoutNum,is_lock,threading_num,collection_on_config,spare_flag):
        spare_flag_text = '备用方案' if spare_flag else '默认方案'
        collection_on = bool(collection_on_config)
        libtable=library
        # logger.error(f"libtable：{libtable}")
        for i in range(len(libtable)):
            logger.info(f"{plugins_name}现在开始使用 ['{spare_flag_text}'] 处理媒体库 ['{libtable[i]}']")
            # 需要优化
            videos_lib = self.plexserver.library.section(libtable[i])
            # logger.error(f"videos_lib.type:{videos_lib.type}")
            if videos_lib.type == 'photo':
                logger.info(f"「{libtable[i]}」是照片库，跳过整理\n")
                continue
            videos = videos_lib.all()
            # logger.error(f"{plugins_name}未排序前：\n{videos}")
            videos.sort(key=lambda video: video.addedAt, reverse=True)
            # logger.error(f"{plugins_name}排序后：\n{videos}")
            #处理合集
            if self.config_Collection and collection_on:
                collections=videos_lib.collections()
                collections.sort(key=lambda collection: collection.addedAt, reverse=True)
                collections_num = len(collections)
                logger.info(f"{plugins_name}开始处理媒体库 ['{libtable[i]}'] 中所有合集，共 {collections_num} 个合集")
                collection_count = 1
                for collection in collections:
                    collection_percent = f"{round((collection_count/collections_num)*100, 1)}%"
                    if collection_percent == '100.0%':
                        logger.info(f"{plugins_name}开始处理第 {collection_count} 个合集：['{collection.title}']，已完成 100%，这是当前库需要处理的最后一个合集")
                    else:
                        now_collection_count = int(collections_num - collection_count)
                        logger.info(f"{plugins_name}开始处理第 {collection_count} 个合集：['{collection.title}']，已完成 {collection_percent}，当前库剩余 {now_collection_count} 个合集需要处理，还需要 {self.how_long(now_collection_count)}")
                    collection_count = collection_count + 1
                    # 获取元数据锁定情况
                    # collection, locked_info, spare_flag, genres_all = self.get_locked_info(collection)
                    collection, video_info = self.get_locked_info(collection,spare_flag)
                    if is_lock == 'run_locked':
                        self.process_lock_poster_and_art(collection)
                        # logger.info(f"「{collection.title}」手动锁定海报和背景完成!\n")
                    elif is_lock == 'run_unlocked':
                        self.process_unlock_poster_and_art(collection)
                        # logger.info(f"「{collection.title}」手动解锁海报和背景完成!\n")
                    else:
                        if self.config_Poster:
                            self.process_fanart(collection,video_info)
                        # 判断标题排序和标题是否相同,如果是不相同则视为手动修改过，不处理。
                        if collection.titleSort != collection.title and self.config_SortTitle:
                            logger.info(f"「{collection.title}」合集的标题排序为: ['{collection.titleSort}'], 已锁定或手动调整过，不进行翻译替换\n")
                        else:
                            self.process_sorttitle(collection,video_info)

            #处理视频
            video_len=len(videos)
            logger.info(f"「{libtable[i]}」库中共有 {video_len} 部影片")
            if str(sortoutNum).lower() != 'all':
                if str(sortoutNum).isdigit():
                    sortoutNum = int(sortoutNum)
                    video_num = min(sortoutNum, video_len)
                    if sortoutNum > video_len:
                        logger.info(f"「{libtable[i]}」库设置的整理数量为['{sortoutNum}']，但库中只有 {video_len} 部影片，将整理库中所有影片")
                    else:
                        logger.info(f'「{libtable[i]}」库将整理最新的 {video_num} 部影片')
                    # 当 sortoutNum 是单个数字时，取出前 sortoutNum 个视频
                    videos = videos[:int(video_num)]
                elif '-' in sortoutNum:
                    # 当 sortoutNum 是数字范围时，取出指定范围的视频
                    start, end = map(int, sortoutNum.split('-'))
                    if start > end:
                        logger.info(f'{plugins_name}整理范围设置错误，开始位置比结束位置还大，请重新设置')
                        return
                    videos = videos[start-1:end]
                    video_num = end - start -1
                    logger.info(f"「{libtable[i]}」库将整理第 {start} - {end} 部影片")
                    if start > video_len:
                        logger.info(f'「{libtable[i]}」库中的影片数量不足 {start} 部，请重新设置')
                        return
            else:
                logger.info(f"「{libtable[i]}」库设置整理数量为['{sortoutNum}'], 将整理库中所有影片，共 {video_len} 部影片")
                video_num = video_len
                # videos = videos[:video_num]
                
            if threading_num:
                # videos = videos[:video_num]
                # threading_video_num = int(len(videos)/threading_num)
                threading_video_num = int(video_num/threading_num)
                if threading_video_num == 0:
                    threading_video_num = video_num
                # 将视频名称序列分成100个一组的列表
                video_groups = [videos[mnx:mnx+threading_video_num] for mnx in range(0, video_num, threading_video_num)]
                # 为每个分组启动一个新的线程，并将其作为参数传递给sss函数
                all_group_num = len(video_groups)
                group_num = 1
                threads = []
                for video_group in video_groups:
                    group_now = f"{group_num}/{all_group_num}"
                    logger.warning(f"{plugins_name}开始处理第 {group_now} 个分组")
                    # logger.warning(f"{plugins_name}开始处理第 {group_num}/{all_group_num} 个分组:{video_group}")
                    group_num = group_num + 1
                    thread = threading.Thread(target=self.thread_process_all, args=(video_group, is_lock, group_now, spare_flag))
                    thread.start()
                    threads.append(thread)
                    time.sleep(random.randint(7, 12))
                    # time.sleep(8)
                # 等待所有线程执行完毕
                for t in threads:
                    t.join()
                logger.info(f"{plugins_name}所有 {all_group_num} 个分组已全部处理完成")
                
            else:
                for video,i in zip(videos,range(video_num)):
                    video_percent = f"{round(((i+1)/video_num)*100, 1)}%"
                    if video_percent == '100.0%':
                        logger.info(f"{plugins_name}开始处理第 {i+1} 部影片：['{video.title}']，已完成 100%，这是当前库需要处理的最后一部影片")
                    else:
                        now_video_count = int(video_num - i - 1)
                        logger.info(f"{plugins_name}开始处理第 {i+1} 部影片：['{video.title}']，已完成 {video_percent}，当前库剩余 {now_video_count} 部影片需要处理，还需要 {self.how_long(now_video_count)}")
                    # 获取元数据锁定情况
                    # video, locked_info, spare_flag, genres_all = self.get_locked_info(video)
                    video, video_info = self.get_locked_info(video,spare_flag)

                    if is_lock == 'run_locked':
                        self.process_lock_poster_and_art(video)
                        # logger.info(f"「{video.title}」手动锁定海报和背景完成!\n")
                    elif is_lock == 'run_unlocked':
                        self.process_unlock_poster_and_art(video)
                        # logger.info(f"「{video.title}」手动解锁海报和背景完成!\n")
                    else:   
                        # logger.info(f"{plugins_name}video.type ['{video.type}']")
                        #fanart筛选
                        if self.config_Poster:
                            self.process_fanart(video,video_info)
                        #标签翻译整理
                        if self.config_Genres:
                            self.process_tag(video, video_info, False)
                        #首字母排序
                        if self.config_SortTitle:
                            self.process_sorttitle(video,video_info)
                result = {
                    "run_locked": "锁定海报和背景完成!",
                    "run_unlocked": "解锁海报和背景完成!",
                    "run_all": "运行整理完成!"
                }
                logger.info(f"{plugins_name}{result[is_lock]}")

    # 定时整理合集
    def process_collection(self):
        all_collections = []
        all_library = []
        # 指定要获取最近添加项的库
        if str(self.config_LIBRARY).lower() == 'all' or not self.config_LIBRARY:
            all_library = self.plexserver.library.sections()
            for library in all_library:
                if library.type == 'photo': continue
                collections=library.collections()
                all_collections.extend(collections)
                # for collection in collections():
                #         all_collections.append(collection)
            logger.info(f"{plugins_name}未指定需要整理的媒体库或设置为ALL，将整理全库所有合集")
        else:
            library_names = []
            library_names = self.config_LIBRARY.split(',')
            logger.info(f"{plugins_name}指定需要整理的媒体库为：{library_names}")

            # logger.info(f"{plugins_name}将整理指定库中最近添加的 {sortout_num} 个合集")
            for library_name in library_names:
                library = self.plexserver.library.section(library_name)
                if library.type == 'photo': continue
                collections = library.collections()
                all_collections.extend(collections)
        
        all_collections.sort(key=lambda collection: collection.addedAt, reverse=True)

        # 处理合集
        all_collections_count = len(all_collections)
        logger.info(f"{plugins_name}一共需要整理 {all_collections_count} 个合集")
        for collection_count, collection in enumerate(all_collections):
            # if collection: 可通过此判断 是否为空合集（即合集中没有影片，空文件）
            collection_title = collection.title
            collection_percent = f"{round(((collection_count+1)/all_collections_count)*100, 1)}%"
            now_collection_count = int(all_collections_count - collection_count - 1)
            if collection_percent == '100.0%':
                logger.info(f"{plugins_name}开始处理 第 {collection_count+1}/{all_collections_count} 个合集 ['{collection_title}']，已完成 100%，这是最后一个需要处理的合集")
            else:
                logger.info(f"{plugins_name}开始处理 第 {collection_count+1}/{all_collections_count} 个合集 ['{collection_title}']，已完成 {collection_percent}，剩余 {now_collection_count} 个合集需要处理")
            # collection, locked_info, spare_flag, genres_all = self.get_locked_info(collection)
            collection, video_info = self.get_locked_info(collection,False)
            # 判断标题排序和标题是否相同,如果是不相同则视为手动修改过，不处理。
            if self.config_Poster:
                self.process_fanart(collection,video_info)
            if collection.titleSort != collection.title and self.config_SortTitle:
                logger.info(f"「{collection_title}」合集的标题排序为: ['{collection.titleSort}'], 已锁定或手动调整过，不进行翻译替换\n")
            else:
                self.process_sorttitle(collection,video_info)
        logger.info(f"{plugins_name}媒体库合集定时整理完成")

    # 自动整理指定库最近新添加项
    def process_new(self, library_section_title, rating_key, parent_rating_key, grandparent_rating_key, grandparent_title, parent_title, org_title, org_type,add_media_info,add_info_toggle=True):
        sortout_num = 6
        recently_added_collections = []
        wait_text = '随机等待 50-70 秒后，处理新入库'
        media_types = {
            'movie': f"电影：['{org_title}']",
            'episode': f"剧集：['{grandparent_title}']",
            'season': f"剧集：['{parent_title}']",
            'show': f"剧集：['{org_title}']"
        }
        media_type_text = media_types.get(org_type, f"媒体 ['{org_type}']：['{org_title}']")
        logger.info(f"{plugins_name}{wait_text}{media_type_text}")
        video = None
        time.sleep(random.randint(50, 70))

        # 指定要获取最近添加项的库
        if str(self.config_LIBRARY).lower() != 'all' and self.config_LIBRARY:
            library_names = ''
            library_names = self.config_LIBRARY.split(',')
            logger.info(f"{plugins_name}指定需要整理的媒体库为：{library_names}")
            if library_section_title and library_section_title not in library_names:
                logger.info(f"{plugins_name}新入库媒体所属库为：['{library_section_title}']，不属于需要整理的媒体库，跳过整理！")
                return

        for retry_count in range(max_retry):
            try:
                # 通过入库事件传来的媒体唯一 ratingkey 来获取 video 对象，这个对象包含媒体的所有信息
                video = self.plexserver.fetchItem(int(rating_key))
                break
            except Exception as e:
                logger.error(f"{plugins_name} 第 {retry_count+1}/{max_retry} 获取新添加的媒体对象失败，原因：{e}")
                time.sleep(15)
                self.connect_plex()
                continue
        # 整理新入库媒体（由 plex webhook 主动传入）
        if video:
            video_title = ''
            for retry_count in range(max_retry):
                try:
                    video_title = video.title 
                    if video.type == "episode":
                        editvideo = self.plexserver.fetchItem(int(grandparent_rating_key))
                        video_title = editvideo.title
                    elif video.type == "season":
                        editvideo = self.plexserver.fetchItem(int(parent_rating_key))
                        video_title = editvideo.title
                    else:
                        editvideo=video
                    break
                except Exception as e:
                    logger.error(f"{plugins_name} 第 {retry_count+1}/{max_retry} 获取新添加剧集上一级媒体对象失败，原因：{e}")
                    time.sleep(15)
                    self.connect_plex()
                    continue
            
            # 获取元数据锁定情况
            # editvideo, locked_info, spare_flag, genres_all = self.get_locked_info(editvideo)
            editvideo, video_info = self.get_locked_info(editvideo,True)
            # Fanart 精美封面筛选
            if self.config_Poster:
                self.process_fanart(editvideo,video_info)
            # 标签翻译整理
            if self.config_Genres:
                self.process_tag(editvideo, video_info, True)
            # 首字母排序
            if self.config_SortTitle:
                self.process_sorttitle(editvideo,video_info)

            # 整理结束后执行海报添加媒体信息
            if rating_key and add_media_info and add_info_toggle:
                logger.info(f'{plugins_name}开始为新入库{media_type_text} 的海报添加媒体信息')
                force_add = False
                restore = False
                show_log = True
                create_backup_note(poster_backup_path)
                if org_type in ['show','season']:
                    get_episode(video,org_type,library_section_title,force_add,restore,show_log)
                if org_type in ['movie','episode']:
                    add_info_one(video,org_type,'',library_section_title,force_add,'','','',restore,show_log)
            
            logger.info(f"{plugins_name}新入库{media_type_text} 整理完成")
        else:
            logger.error(f"{plugins_name}在 PLEX 服务器中没有找到媒体: {rating_key}")
        
    # 整理指定媒体
    def process_single_video(self, single_videos, spare_flag):
        video = None
        single_videos_names = single_videos.split('\n')
        spare_flag_text = '备用方案' if spare_flag else '默认方案'
        logger.info(f"{plugins_name}开始使用 ['{spare_flag_text}'] 处理 {single_videos_names}")
        
        for single_videos_name in single_videos_names:
            for i in range(max_retry):
                try:
                    search_results = self.plexserver.library.search(single_videos_name)
                    break
                except Exception as e:
                    if i+1 == max_retry:
                        logger.error(f"{plugins_name} 第 {i+1}/{max_retry} 次在 PLEX 中搜索 ['{single_videos_name}'] 失败，原因：{e}，跳过处理")
                    else:
                        logger.error(f"{plugins_name} 第 {i+1}/{max_retry} 次在 PLEX 中搜索 ['{single_videos_name}'] 失败，原因：{e}")
                    ######################
                    self.connected = False
                    time.sleep(10)
                    self.connect_plex()
                    ######################
                    continue
            logger.info(f"{plugins_name}['{single_videos_name}'] 在 PLEX 中共搜索到 {len(search_results)} 条结果：{search_results} ,只处理电影和剧集\n")
            for video in search_results:
                if video.type == 'show' or video.type == 'movie':
                    # 获取元数据锁定情况
                    # editvideo, locked_info, spare_flag, genres_all = self.get_locked_info(video)
                    editvideo, video_info = self.get_locked_info(video,spare_flag)
                    # Fanart 精美封面筛选
                    if self.config_Poster:
                        self.process_fanart(editvideo,video_info)
                    # 标签翻译整理
                    if self.config_Genres:
                        self.process_tag(editvideo, video_info, False)
                    # 首字母排序
                    if self.config_SortTitle:
                        self.process_sorttitle(editvideo,video_info)
            # logger.info(f"{plugins_name} {sortout_num} 手动整理指定电影名称的媒体完成")
