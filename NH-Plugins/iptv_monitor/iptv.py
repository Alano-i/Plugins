import re
import json
import requests
from lxml import html
import os
import logging
logger = logging.getLogger(__name__)

from notifyhub.plugins.utils import (
    get_plugin_data,
    get_plugin_config,
)
from notifyhub.controller.server import server
from notifyhub.plugins.common import after_setup
from notifyhub.controller.schedule import register_cron_job

plugin_id = "iptv_monitor"
plugin_name = "IPTV频道同步"
task_falg=False

# 获取原始存储数据（含名称等元信息）
data = get_plugin_data(plugin_id)  # 存在时返回字典，不存在返回 None

# 获取配置字典
config = get_plugin_config(plugin_id)  # 返回 dict，不存在时返回空字典 {}

# logger.info(f"「{plugin_name}」原始存储数据（含名称等元信息）: {data}")
logger.info(f"「{plugin_name}」配置字典: {config}")

URL = "https://epg.51zmt.top:8001/sctvmulticast.html"
HEADERS = {"User-Agent": "Mozilla/5.0"}

UDPXY_URL = f"{config.get('udpxy_url', 'http://10.0.0.254:6868')}".rstrip('/')
IPTV_JSON_PATH = f"{config.get('iptv_json_url', '/data/iptv').rstrip('/')}/iptv.json"
M3U_PATH = f"{config.get('m3u_path', '/data/iptv').rstrip('/')}/iptv.m3u"
NOTIFY_SWITCH = config.get('notify_switch', True)
TASK_SWITCH = config.get('task_switch', True)
BIND_CHANNEL = config.get('bind_channel')
PUSH_LINK_URL = config.get('push_link_url','')
PUSH_IMG_URL = config.get('push_img_url','')
CRON_TASK_TIME = config.get('cron_task_time','')

# logger.info(f"「{plugin_name}」UDPXY_URL: {UDPXY_URL}")
# logger.info(f"「{plugin_name}」IPTV_JSON_PATH: {IPTV_JSON_PATH}")
# logger.info(f"「{plugin_name}」M3U_PATH: {M3U_PATH}")
# logger.info(f"「{plugin_name}」NOTIFY_SWITCH: {NOTIFY_SWITCH}")
# logger.info(f"「{plugin_name}」TASK_SWITCH: {TASK_SWITCH}")
# logger.info(f"「{plugin_name}」PUSH_LINK_URL: {PUSH_LINK_URL}")
# logger.info(f"「{plugin_name}」PUSH_IMG_URL: {PUSH_IMG_URL}")
# logger.info(f"「{plugin_name}」CRON_TASK_TIME: {CRON_TASK_TIME}")


def normalize_text(s: str) -> str:
    return " ".join((s or "").replace("\xa0", " ").split())

def extract_multicast(s: str) -> str:
    """提取并标准化 组播地址 -> ip:port"""
    s = normalize_text(s)
    m = re.search(r'((?:\d{1,3}\.){3}\d{1,3})(?::(\d{2,5}))', s)
    if m:
        return f"{m.group(1)}:{m.group(2)}"
    return s

def fetch_doc(url=URL, verify=False, timeout=15):
    r = requests.get(url, headers=HEADERS, verify=verify, timeout=timeout)
    r.raise_for_status()
    return html.fromstring(r.content)

def parse_table(doc):
    wanted = {"频道名称", "组播地址", "回放天数", "频道ID", "清晰度/帧率/编码", "回放地址"}
    tables = doc.xpath("//table[.//tr]")
    target, header_map = None, {}

    for t in tables:
        headers = [normalize_text(e.text_content()) for e in t.xpath(".//tr[1]/*")]
        if headers and len(set(headers) & wanted) >= 4:
            target = t
            header_map = {h: i for i, h in enumerate(headers)}
            break

    if target is None:
        raise RuntimeError("未找到包含所需字段的表格")

    def idx(name, fallback=None):
        alias = {
            "频道名称": ["频道", "频道名", "台名"],
            "组播地址": ["组播", "多播", "multicast", "组播IP", "地址"],
            "回放天数": ["回放天数", "回看天数", "回放", "天数"],
            "频道ID":   ["频道Id", "频道id", "ID", "台标ID", "台标id"],
            "清晰度/帧率/编码": ["清晰度", "帧率", "编码", "清晰度/帧率", "参数"],
            "回放地址": ["回放", "回看", "rtsp", "播放地址"],
        }
        for key in [name] + alias.get(name, []):
            if key in header_map:
                return header_map[key]
        return fallback

    i_title = idx("频道名称", 0)
    i_multi = idx("组播地址", 1)
    i_days  = idx("回放天数", None)
    i_id    = idx("频道ID", 2)
    i_quality = idx("清晰度/帧率/编码", None)
    i_play  = idx("回放地址", 3)

    iptv = []
    for tr in target.xpath(".//tr[position()>1][td]"):
        tds = tr.xpath("./td")
        get = lambda i: normalize_text(tds[i].text_content()) if i is not None and i < len(tds) else ""

        title = get(i_title)
        multicast = extract_multicast(get(i_multi))
        playback_days = get(i_days)
        channel_id = re.sub(r"\D", "", get(i_id)) or get(i_id)
        quality_info = get(i_quality)
        playback = get(i_play)

        if not (title or multicast or playback_days or channel_id or quality_info or playback):
            continue

        iptv.append({
            "title": title,
            "multicast_address": multicast,
            "playback_days": playback_days,
            "channel_ID": channel_id,
            "quality_info": quality_info,
            "playback_address": playback
        })

    return iptv

def generate_m3u(iptv_list, base_url=f"{UDPXY_URL}/rtp/"):
    lines = ["#EXTM3U"]
    for idx, ch in enumerate(iptv_list, start=1):
        title = ch['title']
        addr = ch['multicast_address']
        # tvg-id 用 idx 占位，你也可以改成 channel_ID
        lines.append(f'#EXTINF:-1 tvg-id="{idx}" tvg-name="{title}" tvg-logo="" group-title="",{title}')
        lines.append(f"{base_url}{addr}")
    return "\n".join(lines)

def fetch_iptv(url=URL):
    doc = fetch_doc(url)
    return parse_table(doc)

def compare_iptv(old_list, new_list):
    """对比两个 IPTV 列表，返回差异信息"""
    results = []
    def key(ch): return ch.get("channel_ID") or ch.get("title")

    old_map = {key(ch): ch for ch in old_list}
    new_map = {key(ch): ch for ch in new_list}

    field_name_map = {
        "title": "频道名称",
        "multicast_address": "组播地址",
        "playback_days": "回放天数",
        "channel_ID": "频道ID",
        "quality_info": "清晰度/帧率/编码",
        "playback_address": "回放地址"
    }

    # 新增、删除单独输出
    for k in new_map:
        if k not in old_map:
            results.append(f"🆕 新增频道: {new_map[k]['title']}")
    for k in old_map:
        if k not in new_map:
            results.append(f"❌ 删除频道: {old_map[k]['title']}")

    # 更新项按频道分组
    updates_by_channel = {}
    for k in new_map:
        if k in old_map:
            for field in field_name_map.keys():
                old_val = old_map[k].get(field, "")
                new_val = new_map[k].get(field, "")
                if old_val != new_val:
                    title = new_map[k]['title']
                    updates_by_channel.setdefault(title, []).append(
                        f"{field_name_map[field]}： '{old_val}' → '{new_val}'"
                    )

    # 合并输出
    for title, changes in updates_by_channel.items():
        results.append(f"🔄 {title}")
        results.extend(changes)
        results.append("")  # 空行分隔

    return results

def send_notify(content,update_data=True):
    if NOTIFY_SWITCH:
        try:
            # 按渠道发送（单个渠道）
            server.send_notify_by_channel(
                channel_name=BIND_CHANNEL,
                title="IPTV 频道更新" if update_data else "IPTV 频道无更新",
                content=content if update_data else "",
                push_img_url=PUSH_IMG_URL,      # 可选
                push_link_url=PUSH_LINK_URL       # 可选
            )

            # 按通道发送（通道会绑定一个或多个渠道）
            # server.send_notify_by_router(
            #     route_id=BIND_ROUTES,
            #     title="IPTV 频道更新通知",
            #     content=content,
            #     push_img_url=None, # 可选
            #     push_link_url=None # 可选
            # )
            logger.info(f"「{plugin_name}」✅ 已发送通知")
        except Exception as e:
            logger.error(f"❌ 发送通知失败: {e}")
    else:
        logger.info(f"「{plugin_name}」通知开关未开启，跳过发送通知")

# if __name__ == "__main__":
def main():
    if task_falg:
        logger.info(f"「{plugin_name}」定时任务开始执行...")
    else:
        logger.info(f"「{plugin_name}」应用启动运行一次查询...")
    update_iptv=True
    iptv = fetch_iptv()
    # 对比旧数据
    if os.path.exists(IPTV_JSON_PATH):
        with open(IPTV_JSON_PATH, "r", encoding="utf-8") as f:
            old_iptv = json.load(f)
        diffs = compare_iptv(old_iptv, iptv)
        if diffs:
            logger.info(f"「{plugin_name}」📢 发现更新：")
            diff_text = "\n".join(diffs)
            # logger.info(diff_text)
            send_notify(diff_text.strip())
        else:
            logger.info(f"「{plugin_name}」✅ 没有发现频道更新")
            update_iptv=False
            send_notify("",update_data=False)
            
    else:
        logger.info(f"「{plugin_name}」首次运行，生成本地 IPTV 数据")

    # 保存最新数据
    os.makedirs(os.path.dirname(IPTV_JSON_PATH), exist_ok=True)
    with open(IPTV_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(iptv, f, ensure_ascii=False, indent=2)

    # 生成 m3u 文件
    if update_iptv:
        m3u_content = generate_m3u(iptv)
        with open(M3U_PATH, "w", encoding="utf-8") as f:
            f.write(m3u_content)
        logger.info(f"「{plugin_name}」✅ iptv.m3u 已生成")
    else:
        logger.info(f"「{plugin_name}」无需更新 iptv.m3u 文件")

# 在 after_setup 中注册定时任务（同步）
@after_setup(plugin_id=plugin_id, desc="查询IPTV更新")
def setup_cron_jobs():
    if TASK_SWITCH:
        logger.info(f"「{plugin_name}」注册定时查询任务...")
        # 注册定时任务，支持 cron 表达式
        if CRON_TASK_TIME:
            global task_falg
            task_falg=True
            register_cron_job(CRON_TASK_TIME, "IPTV频道同步任务", main, random_delay_seconds=10)
        else:
            logger.warning(f"「{plugin_name}」未配置 CRON_TASK_TIME，跳过注册定时任务")
    else:
        logger.info(f"「{plugin_name}」定时任务未开启，跳过注册定时任务")
