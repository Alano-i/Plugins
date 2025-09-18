import os
import shutil
from concurrent.futures import ThreadPoolExecutor
import logging
logger = logging.getLogger(__name__)
plugins_name = '「删除不含媒体的文件夹」'

# 定义媒体文件扩展名
MEDIA_EXTENSIONS = {'.mp4', '.mkv', '.strm', '.m2ts', '.iso', '.wmv', '.3gp', '.ts', 
                   '.flv', '.rm', '.rmvb', '.avi', '.mov', '.vob', '.m4v', '.f4v', 
                   '.webm', '.mpg', '.mpeg', '.asf', '.asx', '.dat'}

# # 定义要检查的根目录列表
# ROOT_DIRS = [
#     '/Volumes/CloudNAS/115/影音视界/test',  # 替换为你的文件夹路径
#     # '/vol1/1000/strm/媒体库/电影',  # 替换为你的文件夹路径
# ]

def has_media_files(directory, recursive=True):
    """
    检查目录是否包含媒体文件。
    :param directory: 要检查的目录
    :param recursive: 是否递归检查子目录
    :return: 如果包含媒体文件返回 True，否则返回 False
    """
    if recursive:
        for root, _, files in os.walk(directory):
            for file in files:
                if os.path.splitext(file)[1].lower() in MEDIA_EXTENSIONS:
                    return True
    else:
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path) and os.path.splitext(file)[1].lower() in MEDIA_EXTENSIONS:
                return True
    return False

def should_delete_directory(directory):
    """
    判断目录是否应该被删除。
    :param directory: 要检查的目录
    :return: 如果应该删除返回 True，否则返回 False
    """
    # 检查是否是根目录
    if directory in ROOT_DIRS:
        return False

    # 检查父目录是否包含媒体文件
    parent_dir = os.path.dirname(directory)
    if parent_dir and has_media_files(parent_dir, recursive=False):
        return False

    # 检查当前目录及其子目录是否包含媒体文件
    return not has_media_files(directory)

def remove_directory(full_path):
    """
    删除目录的函数，用于多线程。
    :param full_path: 要删除的目录路径
    :return: 如果删除成功返回目录路径，否则返回 None
    """
    try:
        if os.path.exists(full_path):  # 再次检查目录是否存在
            shutil.rmtree(full_path)
            logger.info(f"{plugins_name}已删除目录: {full_path}")
            return full_path
    except Exception as e:
        logger.info(f"{plugins_name}删除目录 {full_path} 时出错: {e}")
    return None



def remove_empty_directories():
    """
    删除不包含媒体文件的目录（多线程版本）。
    :return: 被删除的目录列表
    """
    deleted_dirs = []
    
    # 使用线程池并发处理
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        
        # 遍历所有根目录
        for root_dir in ROOT_DIRS:
            if not os.path.exists(root_dir):
                logger.info(f"{plugins_name}目录不存在: {root_dir}")
                continue
                
            # 自下而上遍历目录，先删除子目录
            for dirpath, dirnames, _ in os.walk(root_dir, topdown=False):
                for dirname in dirnames:
                    full_path = os.path.join(dirpath, dirname)
                    if should_delete_directory(full_path):
                        futures.append(executor.submit(remove_directory, full_path))
        
        # 收集结果
        for future in futures:
            result = future.result()
            if result:
                deleted_dirs.append(result)

    # 最后检查根目录本身是否可以删除
    for root_dir in ROOT_DIRS:
        if os.path.exists(root_dir) and not has_media_files(root_dir):
            result = remove_directory(root_dir)
            if result:
                deleted_dirs.append(result)
    
    return deleted_dirs


def remove(DIRS):
    """
    主函数，执行目录检查和删除操作。
    """
    global ROOT_DIRS
    ROOT_DIRS=DIRS
    logger.info(f"{plugins_name}开始检查和删除不包含媒体文件的目录...")
    deleted_dirs = remove_empty_directories()
    
    if deleted_dirs:
        logger.info(f"{plugins_name}已删除的目录如下:")
        for dir_path in deleted_dirs:
            logger.info(f"{plugins_name}：{dir_path}")
        logger.info(f"{plugins_name}共删除 {len(deleted_dirs)} 个目录")
    else:
        logger.info(f"{plugins_name}没有找到需要删除的目录")
