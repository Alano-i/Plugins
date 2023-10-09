from mbot.core.plugins import plugin, PluginCommandContext, PluginCommandResponse, PluginMeta
from . import plex_sortout
from mbot.openapi import mbot_api
from mbot.core.params import ArgSchema, ArgType
from .get_top250 import get_top250, get_lost_top250, get_lost_douban_top250, get_lost_imdb_top250
from .sub_to_mbot import push_sub_main, movie_sub, tv_sub
from .add_info import add_info_to_posters_main
import logging

server = mbot_api
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
plugins_name = '「PLEX 工具箱」'

def get_filter_list():
    return [{'name':x.filter_name, 'value':x.filter_name} for x in server.subscribe.get_filters()]

is_lock_list = [
    {
        "name": "🟢 执行设置中选中的全部操作",
        "value": "run_all"
    },
    {
        "name": "🔒 仅运行【锁定】海报和背景",
        "value": "run_locked"
    },
    {
        "name": "🔓 仅运行【解锁】海报和背景",
        "value": "run_unlocked"
    }
]

state_list = [
    {
        "name": "✅ 开启",
        "value": 'on'
    },
    {
        "name": "📴 关闭",
        "value": 'off'
    }
]

lost_top250_list = [
    {
        "name": "🟢 豆瓣 TOP250",
        "value": 1
    },
    {
        "name": "🟡 IMDB TOP250",
        "value": 2
    },
    {
        "name": "🌍 全部",
        "value": 3
    }
]


def get_enum_data():
    """
    返回一个包含name和value的枚举数据，在前端页面会呈现为下拉列表框；
    value就是你最终你能接收到的变量值
    """
    logger.info(f'{plugins_name}开始获取媒体库列表，格式：媒体库名称 编号')

    libtable = plex_sortout.get_library()
    return libtable


@plugin.command(name='select_data', title='整理 PLEX 媒体库', desc='自动翻译标签 & 拼音排序 & 添加TOP250标签 & 筛选Fanart封面', icon='MovieFilter', run_in_background=True)
def select_data(ctx: PluginCommandContext,
                library: ArgSchema(ArgType.Enum, '选择需要整理的媒体库', '', enum_values=get_enum_data, multi_value=True),
                threading_num: ArgSchema(ArgType.String, '多线程处理：填线程数量。默认为0，单线程处理', '示例：2000个媒体，设置40，则会启40个线程处理，每个线程处理50个。建议少于100个线程', default_value='0', required=False),
                sortoutNum: ArgSchema(ArgType.String, '整理数量，10 或 10-50，留空整理全部', '说明：10：整理最新的10个，10-50：整理第10-50个（入库时间排序）', default_value='ALL', required=False),
                is_lock: ArgSchema(ArgType.Enum, '选择需要执行的操作，留空执行设置中选中的全部操作', '', enum_values=lambda: is_lock_list, default_value='run_all', multi_value=False, required=False),
                collection_on_config: ArgSchema(ArgType.Enum, '临时启用合集整理：📴 关闭', '', enum_values=lambda: state_list, default_value='off', multi_value=False, required=False),
                spare_flag: ArgSchema(ArgType.Enum, '备用整理方案：✅ 开启', '', enum_values=lambda: state_list, default_value='on', multi_value=False, required=False)):
    # logger.info(f'library:{library[0]}')
    spare_flag = bool(spare_flag and spare_flag.lower() != 'off')
    collection_on_config = bool(
        collection_on_config and collection_on_config.lower() != 'off')
    threading_num = int(threading_num)
    plex_sortout.process_all(library, sortoutNum, is_lock,
                       threading_num, collection_on_config, spare_flag)
    user_list = list(filter(lambda x: x.role == 1, mbot_api.user.list()))
    if user_list:
        for user in user_list:
            if is_lock == 'run_all':
                mbot_api.notify.send_system_message(
                    user.uid, '手动运行整理 PLEX 媒体库', '翻译标签 && 拼音排序 && 添加TOP250标签完毕 && 筛选Fanart封面')
            else:
                mbot_api.notify.send_system_message(
                    user.uid, '手动运行整理 PLEX 媒体库', '锁定 PLEX 海报和背景完毕')
    return PluginCommandResponse(True, f'手动运行整理 PLEX 媒体库完成')


@plugin.command(name='import_plex', title='导入 PLEX 媒体', desc='将 PLEX 中的媒体导入到 Mbot 数据库', icon='SaveAlt', run_in_background=True)
def import_plex(ctx: PluginCommandContext,
                library: ArgSchema(ArgType.Enum, '选择需要导入的的媒体库', '', enum_values=get_enum_data, multi_value=True)):

    for i in range(len(library)):
        logger.info(f"{plugins_name}开始导入媒体库 ['{library[i]}']")
        push_sub_main(library[i])
    return PluginCommandResponse(True, f'导入 PLEX 媒体库到 Mbot 数据库完成')


@plugin.command(name='add_info', title='海报添加信息', desc='将媒体主要信息添加到海报', icon='AddPhotoAlternate', run_in_background=True)
def add_info(ctx: PluginCommandContext,
             library: ArgSchema(ArgType.Enum, '选择需要处理的的媒体库', '', enum_values=get_enum_data, multi_value=True),
             restore_config: ArgSchema(ArgType.Enum, '恢复模式：📴 关闭', '开启后恢复所有处理前的原始海报且下方设置失效', enum_values=lambda: state_list, default_value='off', multi_value=False, required=False),
             force_add_config: ArgSchema(ArgType.Enum, '强制添加模式：📴 关闭', '开启：所有海报重新处理。关闭：处理过的海报不再处理', enum_values=lambda: state_list, default_value='off', multi_value=False, required=False),
             only_show_config: ArgSchema(ArgType.Enum, '对于剧集只处理剧集封面：📴 关闭', '', enum_values=lambda: state_list, default_value='off', multi_value=False, required=False)):
    force_add = bool(force_add_config and force_add_config.lower() != 'off')
    restore = bool(restore_config and restore_config.lower() != 'off')
    only_show = bool(only_show_config and only_show_config.lower() != 'off')
    show_log = True
    if force_add:
        force_add_text = '强制添加信息（处理过的海报将重新处理）'
    else:
        force_add_text = '仅处理未处理过的海报'
    for i in range(len(library)):
        logger.info(
            f"{plugins_name}开始处理媒体库 ['{library[i]}']，模式: {force_add_text}")
        add_info_to_posters_main(library[i], force_add, restore, show_log,only_show)
    return PluginCommandResponse(True, f'将媒体主要信息添加到海报运行完成')


@plugin.command(name='get_top250', title='更新 TOP250 列表', desc='获取最新豆瓣和IMDB TOP250 列表', icon='MilitaryTech', run_in_background=True)
def get_top250_echo(ctx: PluginCommandContext):
    logger.info(f'{plugins_name}开始手动获取最新 TOP250 列表')
    # DouBanTop250 = [278, 10997, 13, 597, 101, 637, 129, 424, 27205, 157336, 37165, 28178, 10376, 20453, 5528, 10681, 10775, 269149, 37257, 21835, 81481, 238, 1402, 77338, 43949, 8392, 746, 354912, 31439, 155, 671, 122, 770, 532753, 255709, 14160, 389, 517814, 360814, 4935, 25838, 87827, 51533, 640, 365045, 423, 13345, 10515, 121, 9475, 11216, 804, 490132, 207, 47759, 120, 603, 240, 8587, 242452, 10451, 550, 453, 4922, 14574, 582, 47002, 100, 10867, 15121, 411088, 19995, 857, 510, 21334, 12445, 274, 11324, 120467, 1124, 1954, 23128, 9470, 489, 311, 680, 673, 3082, 18329, 74308, 53168, 2832, 807, 11423, 4977, 22, 672, 152578, 31512, 158445, 25538, 37703, 398818, 142, 162, 197, 16804, 76, 745, 11104, 49026, 128, 177572, 4291, 80, 194, 37185, 161285, 294682, 9559, 51739, 2517, 210577, 30421, 336026, 37797, 1100466, 122906, 594, 10191, 242, 92321, 348678, 10494, 585, 674, 10193, 4348, 396535, 24238, 20352, 165213, 68718, 54186, 587, 74037, 55157, 77117, 333339, 9261, 10950, 205596, 209764, 324786, 843, 55156, 346, 150540, 526431, 4588, 605, 539, 372058, 176, 359940, 152532, 49519, 292362, 205, 598, 2503, 11471, 81, 315846, 47423, 132344, 497, 77, 39693, 31743, 265195, 45380, 872, 505192, 244786, 82690, 295279, 62, 12405, 475557, 425, 11647, 26466, 40751, 508, 508442, 15804, 89825, 7350, 16859, 13398, 44214, 475149, 16074, 901, 380, 45612, 11036, 334541, 57627, 644, 8290, 424694, 39915, 12477, 280, 548, 76341, 40213, 782, 406997, 16869, 12429, 473267, 220289, 1541, 604, 1372, 525832, 313369, 695932, 25050, 1830, 43824, 286217, 2502, 33320, 12444, 122973, 4476, 9345, 18311, 2501, 8055, 198277, 1427, 36970, 14069, 675, 7508]
    # server.common.set_cache('top250', 'douban', DouBanTop250)
    get_top250()
    logger.info(f'{plugins_name}手动获取最新 TOP250 列表完成')
    return PluginCommandResponse(True, f'手动获取最新 TOP250 列表完成')


@plugin.command(name='get_lost_top250', title='TOP250缺了哪些', desc='查询媒体库中缺失的 TOP250 列表并订阅缺失的影片', icon='MilitaryTech', run_in_background=True)
def get_lost_douban_top250_echo(ctx: PluginCommandContext,
                                lost_top250_config: ArgSchema(ArgType.Enum, '选择查询缺失类型：🟢 豆瓣 TOP250', '', enum_values=lambda: lost_top250_list, default_value=1, multi_value=False, required=False),
                                sub_config: ArgSchema(ArgType.Enum, '订阅 TOP250 缺失的影片：📴 关闭', '', enum_values=lambda: state_list, default_value='off', multi_value=False, required=False),
                                filter_name: ArgSchema(ArgType.Enum, '选择订阅时使用的过滤器，默认：自动选择', '', enum_values=get_filter_list, default_value='', multi_value=False, required=False)):
    sub_set = bool(sub_config and sub_config.lower() != 'off')
    logger.info(f'{plugins_name}开始获取缺失的TOP250列表')
    if lost_top250_config == 1:
        get_lost_douban_top250(sub_set,filter_name)
    elif lost_top250_config == 2:
        get_lost_imdb_top250(sub_set,filter_name)
    else:
        get_lost_top250(sub_set,filter_name)
    result_text = f'缺失的 TOP250 列表获取完成并订阅' if sub_set else f'缺失的 TOP250 列表获取完成'
    logger.info(f'{plugins_name}{result_text}')
    return PluginCommandResponse(True, result_text)


@plugin.command(name='single_video', title='整理 PLEX 媒体', desc='整理指定电影名称的媒体', icon='LocalMovies', run_in_background=True)
def single_video(ctx: PluginCommandContext,
                 single_videos: ArgSchema(ArgType.String, '整理指定电影名称的媒体,支持回车换行，一行一条', '', default_value='', required=True),
                 spare_flag: ArgSchema(ArgType.Enum, '备用整理方案：✅ 开启', '', enum_values=lambda: state_list, default_value='on', multi_value=False, required=False)):
    spare_flag = bool(spare_flag and spare_flag.lower() != 'off')
    logger.info(f'{plugins_name}开始手动整理指定媒体')
    plex_sortout.process_single_video(single_videos, spare_flag)
    logger.info(f'{plugins_name}手动整理指定媒体完成')
    return PluginCommandResponse(True, f'手动整理指定媒体完成')
