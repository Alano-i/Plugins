import time
from typing import Any, List, Dict, Tuple
from datetime import datetime, timedelta
import pytz
import requests
from app.core.config import settings
from app.core.context import MediaInfo
from app.core.event import eventmanager, Event
from app.modules.emby import Emby
from app.modules.jellyfin import Jellyfin
from app.modules.plex import Plex
from app.plugins import _PluginBase
from app.schemas import TransferInfo, RefreshMediaItem
from app.schemas.types import EventType
from app.log import logger
from app.plugins.plextools.add_info import *
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
types = {"movie": 1, "show": 2, "artist": 8, "album": 9, 'track': 10}
TYPES = {"movie": [1], "show": [2], "artist": [8, 9, 10]}
class plextools(_PluginBase):
    # 插件名称
    plugin_name = "Plex工具箱"
    # 插件描述
    plugin_desc = "Plex美化工具箱"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/Alano-i/Mbot-Plugins/main/MP-Plugins/plextools/logo.jpg"
    # 插件版本
    plugin_version = "1.2"
    # 插件作者
    plugin_author = "Alano-i"
    # 作者主页
    author_url = "https://github.com/Alano-i"
    # 插件配置项ID前缀
    plugin_config_prefix = "plextools_"
    # 加载顺序
    plugin_order = 14
    # 可使用的用户级别
    auth_level = 1
    # 运行线程数
    _thread_count = None
    # 定时器
    _scheduler = None
    _onlyonce = False
    # 退出事件
    _event = threading.Event()
    # 私有属性
    # 需要处理的媒体库
    _library_ids = None
    _enabled = False
    _delay = 0
    _emby = None
    _jellyfin = None
    _plex = None
    def init_plugin(self, config: dict = None):
        self._emby = Emby()
        self._plex = Plex()
        if config:
            self._enabled = config.get("enabled")
            self._delay = config.get("delay") or 0
            self._onlyonce = config.get("onlyonce")
            self._library_ids = config.get("library_ids")

        # 启动服务
        # 停止现有任务
        self.stop_service()

        self._scheduler = BackgroundScheduler(timezone=settings.TZ)
        if self._onlyonce:
            if "plex" in settings.MEDIASERVER:

                logger.info(f"Plex海报整理服务，立即运行一次")
                #参数配置
                lib_name='X0 全球电影'
                force_add=False
                restore=False
                show_log=True
                only_show=False
                bk_path = self.get_data_path()
                plexaddinfo = PlexAddInfo(bk_path)
                self._scheduler.add_job(
                    func=plexaddinfo.add_info_to_posters_main,
                    trigger="date",
                    run_date=datetime.now(tz=pytz.timezone(settings.TZ)) + timedelta(seconds=3),
                    name="Plex海报整理",
                    kwargs={
                        'libraries': self.__get_libraries(),
                        'force_add': force_add,
                        'restore': restore,
                        'show_log': show_log,
                        'only_show': only_show,
                        'plex_server': self._plex.get_plex()
                    }
                )
            else:
                logger.error(f"未找到plex媒体服务器配置")
            # 关闭一次性开关
            self._onlyonce = False
            self.__update_config()

            # 启动任务
            if self._scheduler.get_jobs():
                self._scheduler.print_jobs()
                self._scheduler.start()

    def __update_config(self):
        """
        更新配置
        """
        self.update_config({
            "enabled": self._enabled,
            "onlyonce": self._onlyonce,
            "delay": self._delay,
        })
    def __get_libraries(self):
        """获取媒体库信息"""
        libraries = {
            int(library.key): (int(library.key), TYPES[library.type], library.title, library.type)
            for library in self._plex._libraries
            if library.type != 'photo' and library.key in self._library_ids  # 排除照片库
        }

        return libraries
    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        if not settings.MEDIASERVER:
            logger.info(f"媒体库配置不正确，请检查")

        if "plex" not in settings.MEDIASERVER:
            logger.info(f"Plex配置不正确，请检查")

        if not self._plex:
            self._plex = Plex().get_plex()

        # 获取所有媒体库
        libraries = self._plex._libraries
        # 生成媒体库选项列表
        library_options = []

        # 遍历媒体库，创建字典并添加到列表中
        for library in libraries:
            # 排除照片库
            if library.TYPE == "photo":
                continue
            library_dict = {
                "title": f"{library.key}. {library.title} ({library.TYPE})",
                "value": library.key
            }
            library_options.append(library_dict)

        library_options = sorted(library_options, key=lambda x: x["value"])

        """
        拼装插件配置页面，需要返回两块数据：1、页面配置；2、数据结构
        """
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'enabled',
                                            'label': '启用插件',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'onlyonce',
                                            'label': '立即运行一次',
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'delay',
                                            'label': '延迟时间（秒）',
                                            'placeholder': '0'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [

                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VSelect',
                                        'props': {
                                            'model': 'library_ids',
                                            'multiple': True,
                                            'label': '媒体库',
                                            'items': library_options
                                        },
                                    }
                                ],
                            },
                        ],
                    },
                ]
            }
        ], {
            "enabled": False,
            "delay": 0
        }

    def get_page(self) -> List[dict]:
        pass

    @eventmanager.register(EventType.TransferComplete)
    def after_transfer(self, event: Event):
        """
        发送通知消息
        """
        if not self._enabled:
            return

        event_info: dict = event.event_data
        if not event_info:
            return

        # 刷新媒体库
        if not settings.MEDIASERVER:
            return

        if self._delay:
            logger.info(f"延迟 {self._delay} 秒后添加海报信息... ")
            time.sleep(float(self._delay))

        # Plex
        if "plex" in settings.MEDIASERVER:
            # self._plex.refresh_library_by_items(items)
            lib='X0 全球电影'
            force_add=False
            restore=False
            show_log=True
            only_show=False
            logger.info(f"plex_server {self._plex.get_plex()}...")
            bk_path = self.get_data_path()
            plexaddinfo = PlexAddInfo(bk_path)
            self._scheduler.add_job(
                func=plexaddinfo.add_info_to_posters_main,
                trigger="date",
                run_date=datetime.now(tz=pytz.timezone(settings.TZ)) + timedelta(seconds=3),
                name="Plex海报整理",
                kwargs={
                    'libraries': self.__get_libraries(),
                    'force_add': force_add,
                    'restore': restore,
                    'show_log': show_log,
                    'only_show': only_show,
                    'plex_server': self._plex.get_plex()
                }
            )
        # 启动任务
        if self._scheduler.get_jobs():
            self._scheduler.print_jobs()
            self._scheduler.start()
        



    def stop_service(self):
        """
        退出插件
        """
        try:
            if self._scheduler:
                self._scheduler.remove_all_jobs()
                if self._scheduler.running:
                    self._event.set()
                    self._scheduler.shutdown()
                    self._event.clear()
                self._scheduler = None
        except Exception as e:
            logger.info(str(e))
