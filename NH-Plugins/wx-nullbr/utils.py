import logging
import time

from typing import Optional, Dict, Any, List

from notifyhub.plugins.utils import get_plugin_config

logger = logging.getLogger(__name__)


class wxNullbrConfig:
    """wx-nullbr配置管理"""
    PLUGIN_ID = "wx-nullbr"
    
    def __init__(self):
        self._config_cache = None
        self._last_fetch_time = 0
        self._cache_ttl = 30  # 缓存30秒，避免频繁数据库查询
    
    def _fetch_config(self) -> Optional[Dict[str, Any]]:
        """
        从数据库获取最新配置
        
        Returns:
            Optional[Dict]: 插件配置，如果不存在返回None
        """
        try:
            config = get_plugin_config(self.PLUGIN_ID)
            return config
        except Exception as e:
            logger.error(f"获取wx-nullbr配置失败: {e}")
            return None
    
    def _get_config_with_cache(self) -> Optional[Dict[str, Any]]:
        """
        获取配置（带缓存机制）
        
        Returns:
            Optional[Dict]: 配置信息，如果不存在返回None
        """
        current_time = time.time()
        
        # 检查缓存是否过期
        if (self._config_cache is None or 
            current_time - self._last_fetch_time > self._cache_ttl):
            
            # 从数据库获取最新配置
            config_data = self._fetch_config()
            if config_data:
                try:
                    self._config_cache = config_data
                    self._last_fetch_time = current_time
                except (ValueError, SyntaxError) as e:
                    logger.error(f"解析wx-nullbr配置失败: {e}")
                    return None
            else:
                self._config_cache = None
                self._last_fetch_time = current_time
        
        return self._config_cache
    
    def get_config(self) -> Optional[Dict[str, Any]]:
        """
        获取wx-nullbr配置
        
        Returns:
            Optional[Dict]: 配置信息，如果不存在返回None
        """
        return self._get_config_with_cache()
    
    def _get_config_value(self, key: str, default: Any = None) -> Any:
        """
        获取配置值的通用方法
        
        Args:
            key: 配置键名
            default: 默认值
            
        Returns:
            Any: 配置值或默认值
        """
        config = self._get_config_with_cache()
        if config is None:
            return default
        return config.get(key, default)
    
    @property
    def qywx_base_url(self) -> Optional[str]:
        """获取企业微信基础URL"""
        return self._get_config_value("qywx_base_url", "https://qyapi.weixin.qq.com")
    
    @property
    def sCorpID(self) -> Optional[str]:
        """获取企业微信ID"""
        return self._get_config_value("sCorpID", "")
    
    @property
    def sCorpsecret(self) -> Optional[str]:
        """获取企业微信secret"""
        return self._get_config_value("sCorpsecret", "")
    
    @property
    def sAgentid(self) -> Optional[str]:
        """获取企业微信agentid"""
        return self._get_config_value("sAgentid", "")
    
    @property
    def sToken(self) -> Optional[str]:
        """获取企业微信token"""
        return self._get_config_value("sToken", "")
    
    @property
    def sEncodingAESKey(self) -> Optional[str]:
        """获取企业微信EncodingAESKey"""
        return self._get_config_value("sEncodingAESKey", "")
    
    @property
    def nullbr_appid(self) -> Optional[str]:
        """获取nullbr appid"""
        return self._get_config_value("nullbr_appid", "")
    
    @property
    def nullbr_apikey(self) -> Optional[str]:
        """获取nullbr apikey"""
        return self._get_config_value("nullbr_apikey", "")
    
    def validate_config(self) -> Dict[str, bool]:
        """
        验证配置完整性
        
        Returns:
            Dict[str, bool]: 各配置项的验证结果
        """
        validation_result = {
            'nullbr_appid': bool(self.nullbr_appid),
            'nullbr_apikey': bool(self.nullbr_apikey),
        }
        
        return validation_result
    
    def get_missing_configs(self) -> List[str]:
        """
        获取缺失的配置项
        
        Returns:
            List[str]: 缺失的配置项列表
        """
        validation_result = self.validate_config()
        missing_configs = [key for key, valid in validation_result.items() if not valid]
        return missing_configs


# 全局配置实例
config = wxNullbrConfig()