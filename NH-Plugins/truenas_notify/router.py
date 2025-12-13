from fastapi import APIRouter
from fastapi.responses import FileResponse
import os
import logging
logger = logging.getLogger(__name__)
plugin_id = "truenas_notify"
plugins_path = '/data/plugins/truenas_notify'
plugin_name = "「TrueNAS 通知」"

truenas_notify_router = APIRouter(prefix=f"/{plugin_id}", tags=[plugin_id])
@truenas_notify_router.get("/cover/{filename}")
async def cover(filename: str):
    # 图片在当前插件目录下的 cover 目录中
    file_path = os.path.join(plugins_path, 'cover', filename)
    logger.info(f"{plugin_name}收到请求图片: {file_path}")
    if os.path.exists(file_path) and os.path.isfile(file_path):
        # 自动根据后缀推断类型
        ext = os.path.splitext(filename)[-1].lower()
        media_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
        }.get(ext, "application/octet-stream")
        # return FileResponse(file_path, media_type=media_type, filename=filename)  # filename 参数用于下载时的默认文件名，浏览器下载图片
        response = FileResponse(file_path, media_type=media_type)   # 浏览器直接显示图片
        # 设置缓存头，比如缓存 7 天
        response.headers["Cache-Control"] = "public, max-age=604800"
        return response
    else:
        return {"error": "Image not found"}