import httpx
import logging

from ..utils import config

logger = logging.getLogger(__name__)

class NullbrApi:
    def __init__(self):
        self.nullbr_baseurl = "https://api.nullbr.online"
        self.appid = config.nullbr_appid
        self.apikey = config.nullbr_apikey
        self.headers = {
            "X-APP-ID": self.appid,
            "X-API-KEY": self.apikey
        }
        
    def get_115_resources(self, tmdbid, media_type):
        url = f"{self.nullbr_baseurl}/{media_type}/{tmdbid}/115"
        try:
            res = httpx.get(url, headers=self.headers, timeout=20)
            res.raise_for_status()
            data = res.json()
            if not isinstance(data, dict):
                logger.warning("Nullbr 响应非字典结构: %s", type(data))
                return {"115": [], "media_type": media_type}
            return data
        except httpx.TimeoutException as e:
            logger.warning("Nullbr 请求超时: %s", e)
            return {"115": [], "media_type": media_type}
        except httpx.HTTPStatusError as e:
            logger.warning("Nullbr HTTP 状态异常: %s", e)
            return {"115": [], "media_type": media_type}
        except httpx.RequestError as e:
            logger.warning("Nullbr 网络请求异常: %s", e)
            return {"115": [], "media_type": media_type}
        except ValueError as e:
            logger.warning("Nullbr JSON 解析失败: %s", e)
            return {"115": [], "media_type": media_type}
    
    def _parse_115_resources(self, resources):
        if not isinstance(resources, dict):
            logger.warning("Nullbr 解析入参非字典: %s", type(resources))
            return []
        if resources.get("115") == []:
            return []
        result = []
        for i in resources.get("115", []) or []:
            title = i.get("title")
            size = i.get("size")
            share_link = i.get("share_link")
            resolution = i.get("resolution", None)
            quality = i.get("quality", None)
            if quality and isinstance(quality, list):
                quality = " · ".join(quality)
            season_list = None
            if resources.get("media_type") == "tv":
                season_list = i.get("season_list")
            result.append({
                "title": title,
                "size": size,
                "share_link": share_link,
                "resolution": resolution,
                "quality": quality,
                "season_list": season_list if resources.get("media_type") == "tv" else None
            })
        return result
    
    def search_by_tmdbid(self, tmdbid, media_type):
        resources = self.get_115_resources(tmdbid, media_type)
        return self._parse_115_resources(resources)
    
nullbr = NullbrApi()
