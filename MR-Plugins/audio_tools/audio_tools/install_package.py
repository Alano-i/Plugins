#!/usr/bin/env python3
import logging
from importlib import import_module
import time
import os
logger = logging.getLogger(__name__)
plugins_name = '「有声书工具箱」'
#########################依赖库初始化###########################
# 依赖库列表
import_list=[
    'mutagen',
    'cn2an',
    'ffmpeg'
]
# 判断依赖库是否安装,未安装则安装对应依赖库
sourcestr = "https://pypi.tuna.tsinghua.edu.cn/simple/"  # 镜像源
sourceurl = "pypi.tuna.tsinghua.edu.cn"
# sourcestr = "http://pypi.douban.com/simple/"  # 镜像源
# sourceurl = "pypi.douban.com"
def GetPackage(PackageName):
    if PackageName == 'ffmpeg':
        PackageName == 'ffmpeg-python'
    comand = f"pip install {PackageName} -i {sourcestr} --trusted-host {sourceurl}"
    # 正在安装
    logger.info(f"{plugins_name} - 安装依赖脚本, 正在安装依赖 + {str(PackageName)}")
    logger.info(comand)
    try:
        # os.system(comand)
        install_log = os.popen(comand)
        # logger.error(f"「每天60秒读懂世界 - 安装依赖脚本」安装日志：{install_log}")
        logger.info(f'{plugins_name} - 安装依赖脚本, 安装依赖日志如下:\n{install_log.read()}')
        logger.warning(f'{plugins_name} - 安装依赖脚本, 如果下方报错：依赖库安装失败导致插件载入失败，请手动进入 MR 命令行安装，安装命令：pip install mutagen cn2an ffmpeg-python')
        # os.system(f'{comand} | tee /data/plugins/daily_news/install.log')
    except Exception as e:
        logger.error(f"{plugins_name} - 安装依赖脚本, 安装依赖库失败！原因：{e}")
for v in import_list:
    try:
        import_module(v)
    except ImportError:
        logger.error(f"{plugins_name} - 安装依赖脚本, 没有找到需要的依赖库: {v} 现在开始安装！")

        GetPackage(v)
##############################################################