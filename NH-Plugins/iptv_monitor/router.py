from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import FileResponse
import os
import logging
logger = logging.getLogger(__name__)
plugin_id = "iptv_monitor"
plugin_name = "IPTV频道同步"
iptv_file_path='/data/plugins/iptv_monitor/iptv'
M3U_FILE_PATH = f"{iptv_file_path}/iptv-png.m3u"

iptv_monitor_router = APIRouter(prefix=f"/{plugin_id}", tags=[plugin_id])
@iptv_monitor_router.get("/iptv")
async def get_iptv(request: Request):
    # 优先获取反向代理传递的真实 IP
    forwarded_for = request.headers.get("x-forwarded-for")
    real_ip = request.headers.get("x-real-ip")

    if forwarded_for:
        # 可能有多个 IP，用逗号分隔，第一个是真实来源
        client_ip = forwarded_for.split(",")[0].strip()
    elif real_ip:
        client_ip = real_ip.strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    user_agent = request.headers.get("user-agent", "unknown")

    file_path = M3U_FILE_PATH
    if os.path.exists(file_path) and os.path.isfile(file_path):
        logger.info(f"「{plugin_name}」收到请求IPTV文件路径：{file_path}，IP={client_ip}, UA={user_agent}")
        # 强制浏览器按文本方式显示，而不是下载
        return FileResponse(file_path, media_type="text/plain; charset=utf-8")
    else:
        return {"error": "File not found"}