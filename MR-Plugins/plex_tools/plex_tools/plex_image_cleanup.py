import glob, os, re, shutil, sqlite3, sys, time, zipfile
from concurrent.futures import ProcessPoolExecutor
from contextlib import closing
from datetime import datetime
from urllib.parse import quote

if sys.version_info[0] != 3 or sys.version_info[1] < 11:
    print("Version Error: Version: %s.%s.%s incompatible please use Python 3.11+" % (sys.version_info[0], sys.version_info[1], sys.version_info[2]))
    sys.exit(0)

try:
    import plexapi, requests
    from num2words import num2words
    from pmmutils import args, logging, schedule, util
    from plexapi.exceptions import Unauthorized
    from plexapi.server import PlexServer
    from pmmutils.args import PMMArgs
    from pmmutils.exceptions import Continue, Failed
    from requests.status_codes import _codes as codes
    from retrying import retry
    from tqdm import tqdm
except (ModuleNotFoundError, ImportError):
    print("Requirements Error: Requirements are not installed")
    sys.exit(0)

def not_failed(exception):
    return not isinstance(exception, Failed)

modes = {
    "nothing": {
        "ed": "", "ing": "", "space": "",
        "desc": "Metadata Directory Files will not even be looked at."
    },
    "clear": {
        "ed": "Cleared", "ing": "Clearing", "space": "Space Recovered",
        "desc": "Clears out the PIC Restore Directory. (CANNOT BE RESTORED)"
    },
    "report": {
        "ed": "Reported", "ing": "Reporting", "space": "Potential Recovery",
        "desc": "Metadata Directory File changes will be reported but not performed."
    },
    "move": {
        "ed": "Moved", "ing": "Moving", "space": "Potential Recovery",
        "desc": "Metadata Directory Files will be moved to the PIC Restore Directory. (CAN BE RESTORED)"
    },
    "restore": {
        "ed": "Restored", "ing": "Restoring", "space": "",
        "desc": "Restores the Metadata Directory Files from the PIC Restore Directory."
    },
    "remove": {
        "ed": "Removed", "ing": "Removing", "space": "Space Recovered",
        "desc": "Metadata Directory Files will be removed. (CANNOT BE RESTORED)"
    }
}
mode_descriptions = '\n\t'.join([f"{m}: {d}" for m, d in modes.items()])
sc_options = ["mode", "photo-transcoder", "empty-trash", "clean-bundles", "optimize-db"]
options = [
    {"arg": "p",  "key": "plex",             "env": "PLEX_PATH",        "type": "str",  "default": None,     "help": "Path to the Plex Config Directory (Contains Directories: Cache, Metadata, Plug-in Support)."},
    {"arg": "m",  "key": "mode",             "env": "MODE",             "type": "str",  "default": "report", "help": f"Global Mode to Run the Script in ({', '.join(modes)}). (Default: report)"},
    {"arg": "sc", "key": "schedule",         "env": "SCHEDULE",         "type": "str",  "default": None,     "help": "Schedule to run in continuous mode."},
    {"arg": "u",  "key": "url",              "env": "PLEX_URL",         "type": "str",  "default": None,     "help": "Plex URL of the Server you want to connect to."},
    {"arg": "t",  "key": "token",            "env": "PLEX_TOKEN",       "type": "str",  "default": None,     "help": "Plex Token of the Server you want to connect to."},
    {"arg": "di", "key": "discord",          "env": "DISCORD",          "type": "str",  "default": None,     "help": "Webhook URL to channel for Notifications."},
    {"arg": "ti", "key": "timeout",          "env": "TIMEOUT",          "type": "int",  "default": 600,      "help": "Connection Timeout in Seconds that's greater than 0. (Default: 600)"},
    {"arg": "s",  "key": "sleep",            "env": "SLEEP",            "type": "int",  "default": 60,       "help": "Sleep Timer between Empty Trash, Clean Bundles, and Optimize DB. (Default: 60)"},
    {"arg": "i",  "key": "ignore",           "env": "IGNORE_RUNNING",   "type": "bool", "default": False,    "help": "Ignore Warnings that Plex is currently Running."},
    {"arg": "l",  "key": "local",            "env": "LOCAL_DB",         "type": "bool", "default": False,    "help": "The script will copy the database file rather than downloading it through the Plex API (Helps with Large DBs)."},
    {"arg": "e",  "key": "existing",         "env": "USE_EXISTING",     "type": "bool", "default": False,    "help": "Use the existing database if less then 2 hours old."},
    {"arg": "pt", "key": "photo-transcoder", "env": "PHOTO_TRANSCODER", "type": "bool", "default": False,    "help": "Global Toggle to Clean Plex's PhotoTranscoder Directory."},
    {"arg": "et", "key": "empty-trash",      "env": "EMPTY_TRASH",      "type": "bool", "default": False,    "help": "Global Toggle to Run Plex's Empty Trash Operation."},
    {"arg": "cb", "key": "clean-bundles",    "env": "CLEAN_BUNDLES",    "type": "bool", "default": False,    "help": "Global Toggle to Run Plex's Clean Bundles Operation."},
    {"arg": "od", "key": "optimize-db",      "env": "OPTIMIZE_DB",      "type": "bool", "default": False,    "help": "Global Toggle to Run Plex's Optimize DB Operation."},
    {"arg": "tr", "key": "trace",            "env": "TRACE",            "type": "bool", "default": False,    "help": "Run with extra trace logs."},
    {"arg": "lr", "key": "log-requests",     "env": "LOG_REQUESTS",     "type": "bool", "default": False,    "help": "Run with every request logged."},
    {"arg": "nt", "key": "notify_type",      "env": "NOTIFY_TYPE",      "type": "str",  "default": None,     "help": "通知服务类型，支持 'mbot' 或 'nh'"},
    {"arg": "na", "key": "nh_api_url",       "env": "NH_API_URL",       "type": "str",  "default": None,     "help": "NH通知服务器的URL，例如：https://nh.xxx.com"},
    {"arg": "ri", "key": "nh_route_id",      "env": "NH_ROUTE_ID",      "type": "str",  "default": None,     "help": "NH通知服务器的route_id，例如：route_l822"},
    {"arg": "mu", "key": "mbot-url",         "env": "MBOT_URL",         "type": "str",  "default": None,     "help": "Mbot通知服务器的URL，例如：http://10.0.0.1:1329"},
    {"arg": "ak", "key": "access-key",       "env": "ACCESS_KEY",       "type": "str",  "default": None,     "help": "Mbot的 access_key"},
    {"arg": "pu", "key": "pic-url",          "env": "PIC_URL",          "type": "str",  "default": "https://raw.githubusercontent.com/Alano-i/Mbot-Plugins/main/MR-Plugins/plex_tools/plex_tools/overlays/clean.jpg",     "help": "接收通知的图片封面URL"},
    {"arg": "ci", "key": "channel-id",       "env": "CHANNEL_ID",       "type": "int",  "default": 0,        "help": "接收通知消息通道ID"}
    
]
script_name = "Plex Image Cleanup"
plex_db_name = "com.plexapp.plugins.library.db"
base_dir = os.path.dirname(os.path.abspath(__file__))
config_dir = os.path.join(base_dir, "config")
pmmargs = PMMArgs("meisnate12/Plex-Image-Cleanup", base_dir, options, use_nightly=False)
logger = logging.PMMLogger(script_name, "plex_image_cleanup", os.path.join(config_dir, "logs"), discord_url=pmmargs["discord"], is_trace=pmmargs["trace"], log_requests=pmmargs["log-requests"])
logger.secret([pmmargs["url"], pmmargs["discord"], pmmargs["token"], quote(str(pmmargs["url"])), requests.utils.urlparse(pmmargs["url"]).netloc])
requests.Session.send = util.update_send(requests.Session.send, pmmargs["timeout"])
plexapi.BASE_HEADERS["X-Plex-Client-Identifier"] = pmmargs.uuid

######################################### 自定义部分 #########################################
def get_arg(key, default=""):
    try:
        return pmmargs[key]
    except KeyError:
        return default
notify_type = get_arg("notify_type")
nh_api_url  = get_arg("nh_api_url")
nh_route_id = get_arg("nh_route_id")
access_key  = get_arg("access-key")
mbot_url    = get_arg("mbot-url")
pic_url     = get_arg("pic-url")
channel_id  = get_arg("channel-id")

if notify_type == 'mbot':
    logger.info(f"设置的通知方式: Mbot插件")
    logger.info(f"设置的 Mbot URL: {mbot_url}")
    logger.info(f"设置的 Mbot ACCESS_KEY : {access_key}")
    logger.info(f"设置的消息推送封面: {pic_url}")
    logger.info(f"设置的消息推送通道ID: {channel_id}")

if notify_type == 'nh':
    logger.info(f"设置的通知方式: NH通知服务器")
    logger.info(f"设置的 NH服务器通道API URL: {nh_api_url}")
    logger.info(f"设置的 NH服务器通道ID : {nh_route_id}")

def get_num(text):
    size,file_count = '0MB','0'
    # 匹配数字和单位
    match = re.search(r'(\d+(\.\d+)?)\s*([A-Za-z]+)', text)
    if match:
        size = match.group(1)  # 提取文件大小部分
        unit = match.group(3)  # 提取单位部分
        size = (f"{size} {unit}")
    else:
        print("No match found")
    file_count_match = re.search(r'Removing (\d+) Files', text)
    if file_count_match:
        file_count = file_count_match.group(1)
    else:
        print("File count not found")
    return size,file_count

def format_time(time_str):
    hours, minutes, seconds = map(int, time_str.split(':'))
    formatted_time = ""
    if hours > 0:
        formatted_time += f"{hours}小时"
    if minutes > 0:
        formatted_time += f"{minutes}分"
    if seconds > 0:
        formatted_time += f"{seconds}秒"
    return formatted_time

def get_mode(text):
    # 使用字符串切片提取 "Running in" 和 "with" 之间的字符串
    start_index = text.find("Running in") + len("Running in")
    end_index = text.find("Mode with")
    extracted_string = text[start_index:end_index].strip()
    return extracted_string
# 描述为：Running in Remove Mode with Empty Trash, Clean Bundles, and Optimize DB set to True
from collections import OrderedDict
def get_run_Operations(description: str) -> str:
    # 固定顺序映射
    mapping = OrderedDict([
        ('PhotoTrancoder', '清理PhotoTranscoder目录'),
        ('Empty Trash', '清空垃圾箱'),
        ('Clean Bundles', '清理捆绑包'),
        ('Optimize DB', '优化数据库'),
    ])
    
    run_ops = [op for key, op in mapping.items() if key in description]
    result = " · ".join(run_ops) if run_ops else "无操作"
    
    logger.info(f"执行的操作: {result}\n")
    return result


def send_msg(msg_digest):
    logger.info(f"设置的Mbot URL: {mbot_url}")
    logger.info(f"设置的Mbot ACCESS_KEY : {access_key}")
    logger.info(f"设置的消息推送封面: {pic_url}")
    logger.info(f"设置的消息推送通道ID: {channel_id}")
    notify_data = {
        'channel_id': channel_id,
        'msg_data': {
            'title': 'Plex 图片优化清理完成',
            'a': msg_digest,
            'pic_url': pic_url,
            'link_url': ''
        }
    }
    url = f'{mbot_url}/api/plugins/notify_server?access_key={access_key}'
    response = requests.post(url, json=notify_data)
    if response.status_code == 200:
        logger.info(f"已推送微信消息\n")
    else:
        logger.info(f"消息推送失败\n")


def send_nh_msg(msg_digest):
    data = {
        "route_id": nh_route_id,
        "title": "Plex 图片优化清理完成",
        "content": msg_digest,
        # "push_img_url": "https://example.com/test.jpg",
        # "push_link_url": "https://example.com"
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(nh_api_url, json=data, headers=headers)
    if response.status_code == 200:
        logger.info(f"已推送NH消息\n")
    else:
        logger.info(f"消息推送失败\n")

def send_to_notify_server(description,report):
    size_bloat,file_count_bloat,size_tc,file_count_tc,clean_text = '','','','',''
    for i, rep in enumerate(report, start=0):
        if i+1<len(report):
            m=report[i+1][0][1]
        else:
            m=''
        if rep[0][0] == 'Total Runtime': all_time = format_time(rep[0][1])
        if 'Removing Bloat Images' in rep[0][0] and 'Space Recovered Removing' in m:
            size_bloat,file_count_bloat = get_num(report[i+1][0][1])
            clean_text = f"清理多余图片：{file_count_bloat} 张，共 {size_bloat}\n"
        if 'Remove PhotoTranscoder Images' in rep[0][0] and 'Space Recovered Removing' in m:
            size_tc,file_count_tc = get_num(report[i+1][0][1])
            clean_text = f"{clean_text}清理转换图片：{file_count_tc} 张，共 {size_tc}"
    mode=get_mode(description)
    if mode == 'Remove': mode = 'Remove (删除元数据，不可恢复)'
    run_Operations = get_run_Operations(description)
    msg_digest = f"运行模式： {mode}\n清理时长： {all_time}\n\n{clean_text}\n\n{run_Operations}"
    if notify_type == 'mbot':
        send_msg(msg_digest)
    elif notify_type == 'nh':
        send_nh_msg(msg_digest)

######################################### 自定义部分结束 #########################################

def pic_thread(attrs):
    with ProcessPoolExecutor(max_workers=1) as executor:
        executor.submit(run_plex_image_cleanup, *[attrs])

def run_plex_image_cleanup(attrs):
    logger.header(pmmargs, sub=True, discord_update=True)
    logger.separator("Validating Options", space=False, border=False)
    do_transcode = attrs["photo-transcoder"] if "photo-transcoder" in attrs else pmmargs["photo-transcoder"]
    do_trash = attrs["empty-trash"] if "empty-trash" in attrs else pmmargs["empty-trash"]
    do_bundles = attrs["clean-bundles"] if "clean-bundles" in attrs else pmmargs["clean-bundles"]
    do_optimize = attrs["optimize-db"] if "optimize-db" in attrs else pmmargs["optimize-db"]
    local_run = pmmargs["local"]
    if "mode" in attrs and attrs["mode"]:
        mode = str(attrs["mode"]).lower()
    elif pmmargs["mode"]:
        mode = str(pmmargs["mode"]).lower()
    else:
        mode = "report"
    description = f"Running in {mode.capitalize()} Mode"
    extras = []
    if do_trash:
        extras.append("Empty Trash")
    if do_bundles:
        extras.append("Clean Bundles")
    if do_optimize:
        extras.append("Optimize DB")
    if do_transcode:
        extras.append("PhotoTrancoder")
    if extras:
        description += f" with {', '.join(extras[:-1])}{', and ' if len(extras) > 1 else ''}{extras[-1]} set to True"
    logger.info(description)

    try:
        logger.info("Script Started", log=False, discord=True, start="script")
    except Failed as e:
        logger.error(f"Discord URL Error: {e}")
    report = []
    messages = []
    try:
        # Check Mode
        if mode not in modes:
            raise Failed(f"Mode Error: {mode} Invalid. Options: \n\t{mode_descriptions}")
        logger.info(f"{mode.capitalize()}: {modes[mode]['desc']}")
        do_metadata = mode in ["report", "move", "remove"]
        if do_metadata and not local_run and not pmmargs["url"] and not pmmargs["token"]:
            local_run = True
            logger.warning("No Plex URL and Plex Token Given assuming Local Run")

        # Check Plex Path
        if not pmmargs["plex"]:
            if not os.path.exists(os.path.join(base_dir, "plex")):
                raise Failed("Args Error: No Plex Path Provided")
            logger.warning(f"No Plex Path Provided. Using default: {os.path.join(base_dir, 'plex')}")
            pmmargs["plex"] = os.path.join(base_dir, "plex")
        pmmargs["plex"] = os.path.abspath(pmmargs["plex"])
        transcoder_dir = os.path.join(pmmargs["plex"], "Cache", "PhotoTranscoder")
        databases_dir = os.path.join(pmmargs["plex"], "Plug-in Support", "Databases")
        meta_dir = os.path.join(pmmargs["plex"], "Metadata")
        restore_dir = os.path.join(pmmargs["plex"], "PIC Restore")

        if not os.path.exists(pmmargs["plex"]):
            raise Failed(f"Directory Error: Plex Databases Directory Not Found: {os.path.abspath(pmmargs['plex'])}")
        elif local_run and not os.path.exists(databases_dir):
            raise Failed(f"Directory Error: Plug-in Support\\Databases Directory Not Found: {databases_dir}")
        elif mode != "nothing" and not os.path.exists(meta_dir):
            raise Failed(f"Directory Error: Metadata Directory Not Found: {meta_dir}")
        elif do_transcode and not os.path.exists(transcoder_dir):
            logger.error(f"Directory Error: PhotoTranscoder Directory Not Found and will not be cleaned: {transcoder_dir}")
            do_transcode = False

        # Connection to Plex
        server = None
        if do_trash or do_bundles or do_optimize or (do_metadata and not local_run):
            logger.info("Connecting To Plex")
            if not pmmargs["url"]:
                raise Failed("Args Error: No Plex URL Provided")
            if not pmmargs["token"]:
                raise Failed("Args Error: No Plex Token Provided")
            plexapi.server.TIMEOUT = pmmargs["timeout"]
            os.environ["PLEXAPI_PLEXAPI_TIMEOUT"] = str(pmmargs["timeout"])

            @retry(stop_max_attempt_number=5, wait_incrementing_start=60000, wait_incrementing_increment=60000, retry_on_exception=not_failed)
            def plex_connect():
                try:
                    return PlexServer(pmmargs["url"], pmmargs["token"], timeout=pmmargs["timeout"])
                except Unauthorized:
                    raise Failed("Plex Error: Plex token is invalid")
                except Exception as e1:
                    logger.error(e1)
                    raise
            server = plex_connect()
            logger.info("Successfully Connected to Plex")

        try:
            if do_metadata and os.path.exists(restore_dir):
                logger.error(f"{mode} mode invalid while the PIC Restore Directory exists.", discord=True, rows=[
                    [("PIC Path", restore_dir)],
                    [("Mode Options",
                      "Mode: restore (Restore the bloat images back into Plex)\nMode: remove (Remove the bloat images)")]
                ])
                logger.error(f"PIC Path: {restore_dir}\n"
                             f"Mode Options:\n"
                             f"    Mode: restore (Restore the bloat images back into Plex)\n"
                             f"    Mode: remove (Remove the bloat images)")
            if do_metadata:

                # Check if Running
                if local_run:
                    if any([os.path.exists(os.path.join(databases_dir, f"{plex_db_name}-{t}")) for t in ["shm", "wal"]]):
                        temp_db_warning = "At least one of the SQLite temp files is next to the Plex DB; this indicates Plex is still running\n" \
                                          "and copying the DB carries a small risk of data loss as the temp files may not have updated the\n" \
                                          "main DB yet.\n" \
                                          "If you restarted Plex just before running Plex Image Cleanup, and are still getting this error, it\n" \
                                          "can be ignored by using `--ignore` or setting `IGNORE_RUNNING=True` in the .env file."
                        if not pmmargs["ignore"]:
                            raise Failed(temp_db_warning)
                        logger.info(temp_db_warning)
                        logger.info("Warning Ignored")

                # Download DB
                logger.separator("Database")
                dbpath = os.path.join(config_dir, plex_db_name)
                temp_dir = os.path.join(config_dir, "temp")

                is_usable = False
                if pmmargs["existing"]:
                    if os.path.exists(dbpath):
                        is_usable, time_ago = util.in_the_last(dbpath, hours=2)
                        if is_usable:
                            logger.info(f"Using existing database (age: {time_ago})")
                        else:
                            logger.info(f"Existing database too old to use (age: {time_ago})")
                    else:
                        logger.warning(f"Existing Database not found {'making' if local_run else 'downloading'} a new copy")

                report.append([("Database", "")])
                fields = []
                if is_usable:
                    report.append([("", "Using Existing Database")])
                else:
                    report.append([("", f"{'Copied' if local_run else 'Downloaded'} New Database")])
                    if os.path.exists(dbpath):
                        os.remove(dbpath)
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
                    os.makedirs(temp_dir)
                    if local_run:
                        logger.info(f"Copying database from {os.path.join(databases_dir, plex_db_name)}", start="database")
                        util.copy_with_progress(os.path.join(databases_dir, plex_db_name), dbpath, description=f"Copying database file to: {dbpath}")
                    else:
                        logger.info("Downloading Database via the Plex API. First Plex will make a backup of your database.\n"
                                    "To see progress, log into Plex and go to Settings | Manage | Console and filter on Database.\n"
                                    "You can also look at the Plex Dashboard to see the progress of the Database backup.", start="database")
                        logger.info()

                        # fetch the data to be saved
                        headers = {'X-Plex-Token': server._token}
                        response = server._session.get(server.url('/diagnostics/databases'), headers=headers, stream=True)
                        if response.status_code not in (200, 201, 204):
                            message = f"({response.status_code}) {codes.get(response.status_code)[0]}; {response.url} "
                            raise Failed(f"Database Download Failed Try Using Local Copy: {message} " + response.text.replace('\n', ' '))
                        os.makedirs(temp_dir, exist_ok=True)

                        filename = None
                        if response.headers.get('Content-Disposition'):
                            filename = re.findall(r'filename=\"(.+)\"', response.headers.get('Content-Disposition'))
                            filename = filename[0] if filename[0] else None
                        if not filename:
                            raise Failed("DB Filename not found")
                        filename = os.path.basename(filename)
                        fullpath = os.path.join(temp_dir, filename)
                        extension = os.path.splitext(fullpath)[-1]
                        if not extension:
                            contenttype = response.headers.get('content-type')
                            if contenttype and 'image' in contenttype:
                                fullpath += contenttype.split('/')[1]

                        with tqdm(unit='B', unit_scale=True, total=int(response.headers.get('content-length', 0)), desc=f"| {filename}") as bar:
                            with open(fullpath, 'wb') as handle:
                                for chunk in response.iter_content(chunk_size=4024):
                                    handle.write(chunk)
                                    bar.update(len(chunk))

                        # check we want to unzip the contents
                        if fullpath.endswith('zip'):
                            with zipfile.ZipFile(fullpath, 'r') as handle:
                                handle.extractall(temp_dir)

                        if backup_file := next((o for o in os.listdir(temp_dir) if str(o).startswith("databaseBackup")), None):
                            shutil.move(os.path.join(temp_dir, backup_file), dbpath)
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
                    if not os.path.exists(dbpath):
                        raise Failed(f"File Error: Database File Could not {'Copied' if local_run else 'Downloaded'}")
                    logger.info(f"Plex Database {'Copy' if local_run else 'Download'} Complete")
                    logger.info(f"Database {'Copied' if local_run else 'Downloaded'} to: {dbpath}")
                    logger.info(f"Runtime: {logger.runtime()}")
                    fields.append(("Copied" if local_run else "Downloaded", f"{logger.runtime('database')}"))

                # Query DB
                urls = []
                with sqlite3.connect(dbpath) as connection:
                    logger.info()
                    logger.info("Database Opened Querying For In-Use Images", start="query")
                    connection.row_factory = sqlite3.Row
                    with closing(connection.cursor()) as cursor:
                        for field in ["user_thumb_url", "user_art_url", "user_banner_url"]:
                            cursor.execute(f"SELECT {field} AS url FROM metadata_items WHERE {field} like 'upload://%' OR {field} like 'metadata://%'")
                            urls.extend([requests.utils.urlparse(r["url"]).path.split("/")[-1] for r in cursor.fetchall() if r and r["url"]])
                    logger.info(f"{len(urls)} In-Use Images Found")
                    logger.info(f"Runtime: {logger.runtime()}")
                    fields.append(("Query", f"{logger.runtime('query')}"))

                report.append(fields)

                # Scan for Bloat Images
                logger.separator(f"{modes[mode]['ing']} Bloat Images")
                logger.info(f"Scanning Metadata Directory For Bloat Images: {meta_dir}", start="scanning")
                bloat_paths = [
                    os.path.join(r, f) for r, d, fs in tqdm(os.walk(meta_dir), unit=" directories", desc="| Scanning Metadata for Bloat Images") for f in fs
                    if 'Contents' not in r and "." not in f and f not in urls
                ]
                logger.info(f"{len(bloat_paths)} Bloat Images Found")
                logger.info(f"Runtime: {logger.runtime()}")

                # Work on Bloat Images
                if bloat_paths:
                    logger.info()
                    logger.info(f"{modes[mode]['ing']} Bloat Images", start="work")
                    logger["size"] = 0
                    messages = []
                    for path in tqdm(bloat_paths, unit=f" {modes[mode]['ed'].lower()}", desc=f"| {modes[mode]['ing']} Bloat Images"):
                        logger["size"] += os.path.getsize(path)
                        if mode == "move":
                            messages.append(f"MOVE: {path} --> {os.path.join(restore_dir, path.removeprefix(meta_dir)[1:])}.jpg")
                            util.move_path(path, meta_dir, restore_dir, suffix=".jpg")
                        elif mode == "remove":
                            messages.append(f"REMOVE: {path}")
                            os.remove(path)
                        else:
                            messages.append(f"BLOAT FILE: {path}")
                    for message in messages:
                        if mode == "report":
                            logger.debug(message)
                        else:
                            logger.trace(message)
                    logger.info(f"{modes[mode]['ing']} Complete: {modes[mode]['ed']} {len(bloat_paths)} Bloat Images")
                    space = util.format_bytes(logger["size"])
                    logger.info(f"{modes[mode]['space']}: {space}")
                    logger.info(f"Runtime: {logger.runtime()}")
                    report.append([(f"{modes[mode]['ing']} Bloat Images", "")])
                    report.append([("", f"{space} of {modes[mode]['space']} {modes[mode]['ing']} {len(bloat_paths)} Files")])
                    report.append([("Scan Time", f"{logger.runtime('scanning')}"), (f"{mode.capitalize()} Time", f"{logger.runtime('work')}")])
            elif mode in ["restore", "clear"]:
                if not os.path.exists(restore_dir):
                    raise Failed(f"Restore Failed: PIC Restore Directory does not exist: {restore_dir}")
                if mode == "restore":
                    logger.separator("Restore Renamed Bloat Images")

                    logger.info("Scanning for Renamed Bloat Images to Restore", start="scanning")
                    restore_images = [f for f in tqdm(glob.iglob(os.path.join(restore_dir, "**", "*.jpg"), recursive=True), unit=" image", desc="| Scanning for Renamed Bloat Images to Restore")]
                    logger.info(f"Scanning Complete: Found {len(restore_images)} Renamed Bloat Images to Restore")
                    logger.info(f"Runtime: {logger.runtime()}")
                    logger.info()

                    logger.info("Restoring Renamed Bloat Images", start="work")
                    for path in tqdm(restore_images, unit=" restored", desc="| Restoring Renamed Bloat Images"):
                        messages.append(f"RENAME: {path}\n  ----> {os.path.join(meta_dir, path.removeprefix(restore_dir)[1:]).removesuffix('.jpg')}\n")
                        util.move_path(path, restore_dir, meta_dir, suffix='.jpg', append=False)
                    shutil.rmtree(restore_dir)
                    for message in messages:
                        logger.trace(message)
                    messages = []
                    logger.info(f"Restore Complete: Restored {len(restore_images)} Renamed Bloat Images")
                    logger.info(f"Runtime: {logger.runtime()}")
                    report.append([("Restore Renamed Bloat Images", "")])
                    report.append([("Scan Time", f"{logger.runtime('scanning')}"), ("Restore Time", f"{logger.runtime('work')}")])
                else:
                    logger.separator("Removing PIC Restore Directory")

                    logger.info("Scanning PIC Restore for Bloat Images to Remove", start="scanning")
                    del_paths = [os.path.join(r, f) for r, d, fs in tqdm(os.walk(restore_dir), unit=" directories", desc="| Scanning PIC Restore for Bloat Images to Remove") for f in fs]
                    logger.info(f"Scanning Complete: Found {len(del_paths)} Bloat Images in the PIC Directory to Remove")
                    logger.info(f"Runtime: {logger.runtime()}")
                    logger.info()

                    messages = []
                    logger.info("Removing PIC Restore Bloat Images", start="work")
                    logger["size"] = 0
                    for path in tqdm(del_paths, unit=" removed", desc="| Removing PIC Restore Bloat Images"):
                        messages.append(f"REMOVE: {path}")
                        logger["size"] += os.path.getsize(path)
                        os.remove(path)
                    shutil.rmtree(restore_dir)
                    for message in messages:
                        logger.trace(message)
                    logger.info(f"Removing Complete: Removed {len(del_paths)} PIC Restore Bloat Images")
                    space = util.format_bytes(logger["size"])
                    logger.info(f"Space Recovered: {space}")
                    logger.info(f"Runtime: {logger.runtime()}")
                    report.append([("Removing PIC Restore Bloat Images", "")])
                    report.append([("", f"{space} of Space Recovered Removing {len(del_paths)} Files")])
                    report.append([("Scan Time", f"{logger.runtime('scanning')}"), ("Restore Time", f"{logger.runtime('work')}")])
        except Failed as e:
            logger.error(f"Metadata Error: {e}")

        # Delete PhotoTranscoder
        if do_transcode:
            logger.separator(f"Remove PhotoTranscoder Images\nDir: {transcoder_dir}")

            head = logger.info("Scanning for PhotoTranscoder Images", start="transcode_scan")
            transcode_images = [f for f in tqdm(glob.iglob(os.path.join(transcoder_dir, "**", "*.*"), recursive=True), unit=" images", desc=f"| {head}")]
            logger.info(f"Scanning Complete: Found {len(transcode_images)} PhotoTranscoder Images to Remove")
            logger.info(f"Runtime: {logger.runtime()}")
            logger.info()

            head = logger.info("Removing PhotoTranscoder Images", start="transcode")
            logger["size"] = 0
            messages = []
            for f in tqdm(transcode_images, unit=" removed", desc=f"| {head}"):
                file = os.path.join(transcoder_dir, f)
                messages.append(f"REMOVE: {file}")
                logger["size"] += os.path.getsize(file)
                os.remove(file)
            for message in messages:
                logger.trace(message)

            logger.info(f"Remove Complete: Removed {len(transcode_images)} PhotoTranscoder Images")
            space = util.format_bytes(logger["size"])
            logger.info(f"Space Recovered: {space}")
            logger.info(f"Runtime: {logger.runtime()}")
            report.append([("Remove PhotoTranscoder Images", "")])
            report.append([("", f"{space} of Space Recovered Removing {len(transcode_images)} Files")])
            report.append([("Scan Time", f"{logger.runtime('transcode_scan')}"), ("Remove Time", f"{logger.runtime('transcode')}")])

        # Plex Operations
        for arg, arg_check, title, op in [
            ("empty-trash", do_trash, "Empty Trash", "emptyTrash"),
            ("clean-bundles", do_bundles, "Clean Bundles", "cleanBundles"),
            ("optimize-db", do_optimize, "Optimize DB", "optimize")
        ]:
            if arg_check:
                if server:
                    logger.separator()
                    getattr(server.library, op)()
                    logger.info(f"{title} Plex Operation Started")
                    for _ in tqdm(range(pmmargs["sleep"]), desc=f"Sleeping for {pmmargs['sleep']} seconds", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]"):
                        time.sleep(1)
                else:
                    logger.error(f"Plex Error: {title} requires a connection to Plex")
    except Failed as e:
        logger.separator()
        logger.critical(e, discord=True)
        logger.separator()
    except Exception as e:
        for message in messages:
            logger.debug(message)
        logger.stacktrace()
        logger.critical(e, discord=True)
    except KeyboardInterrupt:
        logger.separator(f"User Canceled Run {script_name}")
        logger.remove_main_handler()
        raise

    logger.error_report()
    logger.switch()
    report.append([(f"{script_name} Finished", "")])
    report.append([("Total Runtime", f"{logger.runtime('script')}")])
    logger.report(f"{script_name} Summary", description=description, rows=report, width=18, discord=True)

######################################### 自定义部分 #########################################
    try:
        logger.info(f"描述为：{description}\n")
        logger.info(f"内容为：{report}\n")
        notify_config = {
            "mbot": [mbot_url, access_key],
            "nh": [nh_api_url, nh_route_id],
        }

        if notify_type in notify_config:
            if all(notify_config[notify_type]):
                send_to_notify_server(description, report)
            else:
                logger.info(f"{notify_type.upper()}通知服务器信息配置不完整，请配置好后重试！\n")

    except Exception as e:
        logger.info(f"出错了，原因：{e}\n")
######################################### 自定义部分结束 #########################################

    logger.remove_main_handler()

if __name__ == "__main__":
    try:
        if pmmargs["schedule"]:
            pmmargs["schedule"] = pmmargs["schedule"].lower().replace(" ", "")
            valid_sc = []
            schedules = pmmargs["schedule"].split(",")
            logger.separator(f"{script_name} Continuous Scheduled")
            logger.info()
            logger.info("Scheduled Runs: ")
            for sc in schedules:
                run_str = ""
                parts = sc.split("|")
                if 1 < len(parts) < 4:
                    opts = None
                    if len(parts) == 2:
                        time_to_run, frequency = parts
                    else:
                        time_to_run, frequency, opts = parts
                    try:
                        datetime.strftime(datetime.strptime(time_to_run, "%H:%M"), "%H:%M")
                    except ValueError:
                        if time_to_run:
                            raise Failed(f'"Schedule Error: Invalid Time: {time_to_run}\nTime must be in the "HH:MM" format between 00:00-23:59"')
                        else:
                            raise Failed(f"Schedule Error: blank time argument")

                    options = {}
                    if opts:
                        for opt in opts.split(";"):
                            try:
                                k, v = opt.split('=')
                            except ValueError:
                                raise Failed(f'Schedule Error: Invalid Options: {opt}\nEach semicolon separated option must be in the "key=value" format')
                            if k not in sc_options:
                                keys = '", "'.join(sc_options[:-1])
                                raise Failed(f'Schedule Error: Invalid Key: {k}\nValid keys: "{keys}", and "{sc_options[-1]}"')
                            if k == "mode":
                                final = v
                                if final not in modes:
                                    raise Failed(f"Mode Error: {v} Invalid. Options: \n\t{mode_descriptions}")
                            else:
                                final = args.parse_bool(v)
                                if final is None:
                                    raise Failed(f'"{k.capitalize()} Error: {v} must be either "True" or "False""')
                            options[k] = final

                    if frequency == "daily":
                        run_str += "Daily"
                        schedule.every().day.at(time_to_run).do(pic_thread, options)
                    elif frequency.startswith("weekly(") and frequency.endswith(")"):
                        weekday = frequency[7:-1]
                        run_str += f"Weekly on {weekday.capitalize()}s"
                        match weekday:
                            case "sunday":
                                schedule.every().sunday.at(time_to_run).do(pic_thread, options)
                            case "monday":
                                schedule.every().monday.at(time_to_run).do(pic_thread, options)
                            case "tuesday":
                                schedule.every().tuesday.at(time_to_run).do(pic_thread, options)
                            case "wednesday":
                                schedule.every().wednesday.at(time_to_run).do(pic_thread, options)
                            case "thursday":
                                schedule.every().thursday.at(time_to_run).do(pic_thread, options)
                            case "friday":
                                schedule.every().friday.at(time_to_run).do(pic_thread, options)
                            case "saturday":
                                schedule.every().saturday.at(time_to_run).do(pic_thread, options)
                            case _:
                                raise Failed(f"Schedule Error: Invalid Weekly Frequency: {frequency}\nValue must a weekday")
                    elif frequency.startswith("monthly(") and frequency.endswith(")"):
                        try:
                            day = int(frequency[8:-1])
                            run_str += f"Monthly on the {num2words(day, to='ordinal_num')}"
                            if 0 < day < 32:
                                schedule.every().month_on(day).at(time_to_run).do(pic_thread, options)
                            else:
                                raise ValueError
                        except ValueError:
                            raise Failed(f"Schedule Error: Invalid Monthly Frequency: {frequency}\nValue must be between 1-31")

                    run_str += f" at {time_to_run}"
                    if options:
                        run_str += f" (Options: {'; '.join([f'{k}={v}' for k, v in options.items()])})"
                    logger.info(f"* {run_str}")
                else:
                    raise Failed(f'Schedule Error: Invalid Schedule: {sc}\nEach Schedule must be in either the "time|frequency" or "time|frequency|options" format')

            logger.info()
            logger.separator()
            logger.info()
            while True:
                schedule.run_pending()
                next_run = schedule.next_run()
                time_now = datetime.now()
                time_remaining = next_run - time_now

                td_sec = time_remaining.seconds
                hour_count, rem = divmod(td_sec, 3600)
                minute_count, second_count = divmod(rem, 60)
                remaining_str = ""
                if time_remaining.days > 0:
                    remaining_str += f"{time_remaining.days} day{'s' if hour_count > 1 else ''}"
                if hour_count > 0:
                    remaining_str += f"{', 'if remaining_str else ''}{hour_count} hour{'s' if hour_count > 1 else ''}"
                if minute_count > 0:
                    remaining_str += f"{', 'if remaining_str else ''}{minute_count} minute{'s' if hour_count > 1 else ''}"

                current_time = time_now.strftime("%A %B %d %H:%M")
                next_run_str = next_run.strftime("%A %B %d %H:%M")
                logger.ghost(f"Current Time: {current_time} | {remaining_str} until the next run on {next_run_str}")
                time.sleep(60)
        else:
            pic_thread({})
    except KeyboardInterrupt:
        logger.separator("Exiting Plex Image Cleanup")
