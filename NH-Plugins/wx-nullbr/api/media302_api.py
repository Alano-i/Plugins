import httpx
import logging

from ..utils import config

logger = logging.getLogger(__name__)


class Media302Api:
    def __init__(self):
        self.app_user_agent = "wx-nullbr/0.0.2"
    
    @property
    def base_url(self):
        return config.media302_url
        
    @property
    def folder(self):
        return config.folder
        
    @property
    def token(self):
        return config.media302_token
    
    @property
    def media302_name(self):
        return config.media302_name
        
    def save_share(self, url: str) -> dict:
        """保存115分享链接到115网盘"""
        if not all([self.base_url, self.token]):
            logger.error("media302配置不完整")
            return {"success": False, "message": "插件配置不完整"}
            
        if not url.startswith(("https://115.com", "https://115cdn.com")):
            return {"success": False, "message": "无效的115分享链接"}
            
        try:
            api_url = f"{self.base_url.rstrip('/')}/strm/api/task/save-share"
            params = {"folder": self.folder, "token": self.token, "url": url}
            
            with httpx.Client() as client:
                response = client.get(api_url, params=params, timeout=30, headers={"User-Agent": self.app_user_agent})
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException as e:
            error_msg = f"请求超时: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 500:
                error_msg = "HTTP错误: 500 服务器内部错误，请稍后再试"
            else:
                error_msg = f"HTTP错误: {e.response.status_code} {str(e)}"
            logger.error(f"请求失败: {error_msg}, URL: {api_url}")
            return {"success": False, "message": error_msg}
        except httpx.RequestError as e:
            error_msg = f"请求失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
        except ValueError as e:
            error_msg = f"响应解析失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "message": error_msg}
    
    def re_organize(self) -> dict:
        """重新整理115文件，调用move-all任务"""
        if not all([self.base_url, self.token]):
            logger.error("media302配置不完整")
            return {"success": False, "message": "插件配置不完整"}
            
        try:
            api_url = f"{self.base_url.rstrip('/')}/strm/api/task/move-all"
            params = {"name": self.media302_name, "token": self.token}
            
            with httpx.Client() as client:
                response = client.get(api_url, params=params, timeout=30, headers={"User-Agent": self.app_user_agent})
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException as e:
            error_msg = f"请求超时: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 500:
                error_msg = "HTTP错误: 500 服务器内部错误，请稍后再试"
            else:
                error_msg = f"HTTP错误: {e.response.status_code} {str(e)}"
            logger.error(f"请求失败: {error_msg}, URL: {api_url}")
            return {"success": False, "message": error_msg}
        except httpx.RequestError as e:
            error_msg = f"请求失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
        except ValueError as e:
            error_msg = f"响应解析失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "message": error_msg}


# 全局API实例
media302 = Media302Api()

