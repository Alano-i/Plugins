from .install_package import *
from mbot.openapi import mbot_api
from mbot.openapi import media_server_manager


# 导入插件类
from .plex_sortout import plex_sortout
plex_sortout = plex_sortout()

# # 获取MR服务
# mrserver = mbot_api

# # 获取plex媒体库
# plexserver = media_server_manager.master_plex.plex
# servertype='plex'

# # 设置服务参数
# plex_sortout.setdata(plexserver,mrserver,servertype)

from .main import *
from .command import *
from .get_top250 import *
from .add_info import *
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
