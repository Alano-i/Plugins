import datetime
import threading
import httpx
import logging
import re

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from cacheout import Cache
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response
from xml.etree.ElementTree import fromstring
from tenacity import wait_random_exponential, stop_after_attempt, retry

from notifyhub.plugins.components.qywx_Crypt.WXBizMsgCrypt import WXBizMsgCrypt
from notifyhub.common.response import json_500

from .utils import config
from .api.tmdbapi import tmdb
from .api.nullbr import nullbr
from .api.media302_api import media302

logger = logging.getLogger(__name__)

token_cache = Cache(maxsize=1)
search_cache = Cache(maxsize=1, ttl=180)
resource_cache = Cache(maxsize=1, ttl=300)
SHARE_LINK_PATTERN = r'(https://(?:115\.com|115cdn\.com)/s/[^#\s]+)'

# FastAPI路由器
wx_nullbr_router = APIRouter(prefix="/wx-nullbr", tags=["wx-nullbr"])

APP_USER_AGENT = "wx-nullbr/0.1.0"
XML_TEMPLATES = {
    "reply": """<xml>
<ToUserName><![CDATA[{to_user}]]></ToUserName>
<FromUserName><![CDATA[{from_user}]]></FromUserName>
<CreateTime>{create_time}</CreateTime>
<MsgType><![CDATA[{msg_type}]]></MsgType>
<Content><![CDATA[{content}]]></Content>
<MsgId>{msg_id}</MsgId>
<AgentID>{agent_id}</AgentID>
</xml>"""
}


@dataclass
class QywxMessage:
    """企业微信消息数据类"""
    content: str
    from_user: str
    to_user: str
    create_time: str
    msg_type: str
    msg_id: str


class QywxMessageSender:
    """企业微信消息发送器"""
    
    def __init__(self):
        self.base_url = config.qywx_base_url
        self.corpid = config.sCorpID
        self.corpsecret = config.sCorpsecret
        self.agentid = config.sAgentid
    
    @retry(stop=stop_after_attempt(3), wait=wait_random_exponential(min=10, max=30), reraise=True)
    def get_access_token(self) -> Optional[str]:
        """
        获取企业微信访问令牌
        
        Returns:
            Optional[str]: 访问令牌，获取失败返回None
        """
        # 检查缓存中的token是否有效
        cached_token = token_cache.get('access_token')
        expires_time = token_cache.get('expires_time')
        
        if (expires_time is not None and 
            expires_time >= datetime.datetime.now() and 
            cached_token):
            return cached_token
        
        if not all([self.corpid, self.corpsecret]):
            logger.error("配置错误")
            return None
        
        # 重新获取token
        try:
            response = httpx.get(
                f"{self.base_url.strip('/')}/cgi-bin/gettoken",
                params={
                    'corpid': self.corpid,
                    'corpsecret': self.corpsecret
                },
                headers={'user-agent': APP_USER_AGENT},
                timeout=180
            )
            
            result = response.json()
            if result.get('errcode') == 0:
                access_token = result['access_token']
                expires_in = result['expires_in']
                
                # 计算过期时间（提前500秒刷新）
                expires_time = datetime.datetime.now() + datetime.timedelta(
                    seconds=expires_in - 500
                )
                
                # 缓存token和过期时间
                token_cache.set('access_token', access_token, ttl=expires_in - 500)
                token_cache.set('expires_time', expires_time, ttl=expires_in - 500)
                
                # logger.info(f"{SUCCESS_MESSAGES['token_success']}")
                return access_token
            else:
                logger.error(f"获取企业微信accessToken失败: {result}")
                return None
                
        except Exception as e:
            logger.error(f"获取企业微信accessToken异常: {e}", exc_info=True)
            return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_random_exponential(min=10, max=30), reraise=True)
    def _send_message(self, access_token: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送消息到企业微信
        
        Args:
            access_token: 访问令牌
            message_data: 消息数据
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        try:
            url = f"{self.base_url.strip('/')}/cgi-bin/message/send"
            params = {'access_token': access_token}
            
            response = httpx.post(
                url,
                params=params,
                json=message_data,
                headers={'user-agent': APP_USER_AGENT},
                timeout=180
            )
            
            return response.json()
            
        except Exception as e:
            logger.error(f"发送企业微信消息异常: {e}", exc_info=True)
            return {'errcode': -1, 'errmsg': str(e)}
    
    def send_text_message(self, text: str, to_user: str) -> bool:
        """
        发送文本消息
        
        Args:
            text: 消息内容
            to_user: 接收用户ID
            
        Returns:
            bool: 发送是否成功
        """
        access_token = self.get_access_token()
        if not access_token:
            logger.error("获取企业微信accessToken失败")
            return False
        
        message_data = {
            'touser': to_user,
            'agentid': self.agentid,
            'msgtype': 'text',
            'text': {'content': text}
        }
        
        result = self._send_message(access_token, message_data)
        
        if result.get('errcode') == 0:
            return True
        else:
            logger.error(f"发送企业微信消息失败: {result}")
            return False

    def send_news_message(self, to_user: str, articles: List[Dict[str, Any]]) -> bool:
        """
        发送图文消息
        
        Args:
            to_user: 接收用户ID
            articles: 图文列表，包含title/description/url/picurl
        
        Returns:
            bool: 发送是否成功
        """
        access_token = self.get_access_token()
        if not access_token:
            logger.error("获取企业微信accessToken失败")
            return False
        message_data = {
            'touser': to_user,
            'agentid': self.agentid,
            'msgtype': 'news',
            'news': {
                'articles': articles[:8]  # 限制最多8条
            }
        }
        result = self._send_message(access_token, message_data)
        if result.get('errcode') == 0:
            return True
        else:
            logger.error(f"发送企业微信图文消息失败: {result}")
            return False


class QywxMessageProcessor:
    """企业微信消息处理器"""
    
    def __init__(self):
        # self.message_sender = QywxMessageSender()
        # self.user_records = UserRecords()
        self._crypto = None
    
    def _get_crypto(self) -> WXBizMsgCrypt:
        """
        获取加密组件实例（按需创建）
        
        Returns:
            WXBizMsgCrypt: 加密组件实例
            
        Raises:
            ValueError: 当配置参数缺失时抛出异常
        """
        if self._crypto is None:
            # 验证配置参数
            if not all([config.sToken, config.sEncodingAESKey, config.sCorpID]):
                raise ValueError("配置错误")
            
            self._crypto = WXBizMsgCrypt(
                config.sToken,
                config.sEncodingAESKey,
                config.sCorpID
            )
        return self._crypto
    
    def _parse_xml_message(self, xml_data: str) -> QywxMessage:
        """
        解析XML消息
        
        Args:
            xml_data: XML格式的消息数据
            
        Returns:
            QywxMessage: 解析后的消息对象
        """
        try:
            root = fromstring(xml_data)
            message_data = {node.tag: node.text for node in root}
            
            return QywxMessage(
                content=message_data.get('Content', ''),
                from_user=message_data.get('FromUserName', ''),
                to_user=message_data.get('ToUserName', ''),
                create_time=message_data.get('CreateTime', ''),
                msg_type=message_data.get('MsgType', ''),
                msg_id=message_data.get('MsgId', '')
            )
        except Exception as e:
            logger.error(f"解析XML消息失败: {e}")
            raise ValueError("消息格式错误")
    
    def _create_reply_xml(self, message: QywxMessage, content: str) -> str:
        """
        创建回复XML
        
        Args:
            message: 原始消息
            content: 回复内容
            
        Returns:
            str: XML格式的回复
        """
        return XML_TEMPLATES["reply"].format(
            to_user=message.to_user,
            from_user=message.from_user,
            create_time=message.create_time,
            msg_type=message.msg_type,
            content=content,
            msg_id=message.msg_id,
            agent_id=config.sAgentid
        )
    
    def process_message(self, encrypted_msg: str, msg_signature: str, 
                       timestamp: str, nonce: str) -> str:
        """
        处理企业微信消息
        
        Args:
            encrypted_msg: 加密的消息
            msg_signature: 消息签名
            timestamp: 时间戳
            nonce: 随机数
            
        Returns:
            str: 加密的回复消息
        """
        try:
            # 解密消息
            crypto = self._get_crypto()
            ret, decrypted_msg = crypto.DecryptMsg(
                encrypted_msg, msg_signature, timestamp, nonce
            )
            
            if ret != 0:
                logger.error(f"消息解密失败: {decrypted_msg}")
                raise ValueError("消息解密失败")
            
            # 解析消息
            message = self._parse_xml_message(decrypted_msg.decode('utf-8'))
            content = (message.content or "").strip()
            user_cache = search_cache.get(message.from_user)
            user_resource_cache = resource_cache.get(message.from_user)
            is_pick_digit = content.isdigit() and 1 <= int(content) <= 8
            share_match = re.search(SHARE_LINK_PATTERN, content)

            if share_match:
                job = {
                    'type': 'save_share',
                    'share_url': share_match.group(1)
                }
                self._process_chat_message_async(message, job)
                reply_content = ''
            elif is_pick_digit:
                index = int(content) - 1
                if user_resource_cache and 0 <= index < len(user_resource_cache):
                    job = {
                        'type': 'save_pick',
                        'index': index
                    }
                elif user_cache and 0 <= index < len(user_cache):
                    job = {
                        'type': 'pick_index',
                        'index': index
                    }
                else:
                    job = {
                        'type': 'tmdb_search',
                        'keyword': content
                    }
                self._process_chat_message_async(message, job)
                reply_content = ''
            else:
                # 中文或任意非1-8数字/文本，均作为关键词搜索
                job = {
                    'type': 'tmdb_search',
                    'keyword': content
                }
                self._process_chat_message_async(message, job)
                reply_content = ''
            
            if not reply_content: return
            # 创建回复XML
            reply_xml = self._create_reply_xml(message, reply_content)
            
            # 加密回复
            ret, encrypted_reply = crypto.EncryptMsg(reply_xml, nonce, timestamp)
            
            if ret != 0:
                logger.error(f"消息加密失败: {encrypted_reply}")
                raise ValueError("消息加密失败")
            
            return encrypted_reply
            
        except Exception as e:
            logger.error(f"处理企业微信消息失败: {e}")
            raise
    
    def _process_chat_message_async(self, message: QywxMessage, job: Optional[Dict[str, Any]] = None):
        """
        异步处理聊天消息
        
        Args:
            message: 消息对象
        """
        thread = QywxChatThread(message, job)
        thread.start()


class QywxChatThread(threading.Thread):
    """企业微信聊天处理线程"""
    
    def __init__(self, message: QywxMessage, job: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.name = "QywxChatThread"
        self.message = message
        self.message_sender = QywxMessageSender()
        self.max_length = 768
        self.job = job or {'type': 'tmdb_search', 'keyword': (message.content or '').strip()}
    
    def run(self):
        """线程执行方法"""
        try:
            job_type = self.job.get('type')
            if job_type == 'tmdb_search':
                self._handle_tmdb_search()
            elif job_type == 'pick_index':
                self._handle_pick_index()
            elif job_type == 'save_pick':
                self._handle_save_pick()
            elif job_type == 'save_share':
                self._handle_save_share()
            else:
                logger.warning(f"未知任务类型: {job_type}")
            
        except Exception as e:
            logger.error(f"搜索处理失败: {e}", exc_info=True)
            # 发送错误提示
            error_msg = f"搜索处理失败: {e}"
            self.message_sender.send_text_message(error_msg, self.message.from_user)

    def _truncate(self, text: str, limit: int) -> str:
        if not text:
            return ""
        return text if len(text) <= limit else text[: limit - 1] + "…"

    def _extract_share_link(self, text: str) -> Optional[str]:
        if not text:
            return None
        match = re.search(SHARE_LINK_PATTERN, text)
        return match.group(1) if match else None

    def _handle_tmdb_search(self):
        keyword = (self.job.get('keyword') or '').strip()
        if not keyword:
            self.message_sender.send_text_message("请输入要搜索的影片名称", self.message.from_user)
            return
        # 重置资源缓存，避免数字选择误选旧资源
        try:
            resource_cache.delete(self.message.from_user)
        except Exception:
            resource_cache.set(self.message.from_user, None)
        # 1) 调用TMDB搜索
        results = tmdb.search_by_keyword(keyword) or []
        if not results:
            self.message_sender.send_text_message("未找到相关影片，请尝试其他关键词", self.message.from_user)
            return
        # 2) 仅取前8条，并写入缓存供用户按1-8选择
        top_results = results[:8]
        search_cache.set(self.message.from_user, top_results)
        # 3) 组装图文articles
        articles: List[Dict[str, Any]] = []
        for idx, item in enumerate(top_results, start=1):
            media_type = item.get('type')  # movie/tv
            tmdb_id = item.get('tmdb_id')
            # title = f"{idx} {item.get('title', '')}({item.get('release_year', '')}) ⭐️ {item.get('rating', 0):.1f}"
            title = f"{idx} {item.get('title', '')}({item.get('release_year', '')}) ⭐️ {item.get('rating', 0):.1f}".replace('⭐️ 0.0', '')
            # description = self._truncate(item.get('overview', '') or '', 256)
            # TMDB详情页
            url = f"https://www.themoviedb.org/{media_type}/{tmdb_id}?language=zh-CN"
            backdrop_path = item.get('backdrop_path')
            picurl = tmdb.get_backdrop_url(backdrop_path) if backdrop_path else ""
            articles.append({
                'title': title,
                # 'description': description,
                'url': url,
                'picurl': picurl
            })
        # 4) 发送图文
        ok = self.message_sender.send_news_message(self.message.from_user, articles)
        if not ok:
            # 降级为文本
            lines = [
                f"{idx} {item.get('title', '')}({item.get('release_year', '')}) ⭐️ {item.get('rating', 0):.1f}"
                for idx, item in enumerate(top_results, start=1)
            ]
            lines.append("回复 1-8 选择对应条目，获取115资源")
            text = "\n".join(lines)
            self.message_sender.send_text_message(text, self.message.from_user)

    def _handle_pick_index(self):
        circled_nums = {
            1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣",
            6: "6️⃣", 7: "7️⃣", 8: "8️⃣", 9: "9️⃣", 10: "🔟"
        }

        index = int(self.job.get('index'))
        cached = search_cache.get(self.message.from_user) or []
        if not cached or index < 0 or index >= len(cached):
            self.message_sender.send_text_message("选择无效或已过期，请重新搜索", self.message.from_user)
            return
        chosen = cached[index]
        media_type = chosen.get('type')
        tmdb_id = chosen.get('tmdb_id')
        title = chosen.get('title')
        # 1) 调用nullbr搜索115资源
        resources = nullbr.search_by_tmdbid(tmdb_id, media_type) or []
        if not resources:
            self.message_sender.send_text_message(f"未找到与【{title}】相关的115资源", self.message.from_user)
            return
        resource_cache.set(self.message.from_user, resources)
        # 2) 整理文本回复
        lines: List[str] = [f"【{title}】115资源："]
        for i, r in enumerate(resources, start=1):
            size = r.get('size')
            share_link = r.get('share_link')
            resolution = r.get('resolution')
            quality = r.get('quality')
            r_title = f"{r.get('title')}"
            if r.get('season_list'):
                season_info = ",".join([s for s in r.get('season_list') if s])
                r_title = f"{r_title} ({season_info})"
            circled = circled_nums.get(i, str(i)) # 超过10则用数字
            line = f"{circled} {r_title} · {size}"
            # line = f"{i}. {r_title} · {size}"
            if resolution:
                line += f" · {resolution}"
            if quality:
                line += f" · {quality}"
            line += f"\n🍿 {share_link}"
            lines.append(line)
        lines.append("回复数字转存到 115 并生成 strm")
        text = "\n\n".join(lines[:50])  # 控制长度
        self.message_sender.send_text_message(text, self.message.from_user)

    def _handle_save_pick(self):
        circled_nums = {
            1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣",
            6: "6️⃣", 7: "7️⃣", 8: "8️⃣", 9: "9️⃣", 10: "🔟"
        }
        if self.job.get('index') is None:
            self.message_sender.send_text_message("资源选择无效，请重新选择", self.message.from_user)
            return
        index = int(self.job.get('index'))
        cached = resource_cache.get(self.message.from_user) or []
        if not cached or index < 0 or index >= len(cached):
            self.message_sender.send_text_message("资源选择无效或已过期，请重新搜索", self.message.from_user)
            return
        chosen = cached[index]
        r_title = f"{chosen.get('title')}"
        if chosen.get('season_list'):
            season_info = ",".join([s for s in chosen.get('season_list') if s])
            r_title = f"{r_title} ({season_info})"
        circled = circled_nums.get(index + 1, str(index + 1))
        title_hint = f"{circled} {r_title}"
        self._save_and_reply(chosen.get('share_link'), title_hint)

    def _handle_save_share(self):
        share_url = self.job.get('share_url') or self._extract_share_link(self.message.content or "")
        if not share_url:
            self.message_sender.send_text_message("未检测到有效的115分享链接，请重新输入", self.message.from_user)
            return
        self._save_and_reply(share_url)

    def _save_and_reply(self, share_url: Optional[str], title_hint: Optional[str] = None):
        if not share_url:
            self.message_sender.send_text_message("未检测到有效的115分享链接，请重新输入", self.message.from_user)
            return
        result = media302.save_share(share_url)
        text = self._format_result_message(result, title_hint)
        self.message_sender.send_text_message(text, self.message.from_user)

    def _format_result_message(self, result: Dict[str, Any], title_hint: Optional[str]) -> str:
        # 成功场景
        success_msgs = ('success', '文件已接收，无需重复接收！')
        msg_value = result.get('msg')
        code = result.get('code')
        is_success = (
            msg_value in success_msgs
            or result.get('success') is True
            or code == 0
        )
        def _clean_path(s: str) -> str:
            if not s:
                return ""
            # 常见返回前缀“✅ ”去除
            s = str(s).strip()
            if s.startswith("✅"):
                s = s.lstrip("✅").strip()
            return s

        if is_success:
            # 处理 msg 中的路径字符串
            path_str = ""
            if isinstance(msg_value, str) and msg_value:
                # msg 可能是路径或包含多行，取首行
                path_str = msg_value.splitlines()[0].strip()
                path_str = _clean_path(path_str)
            elif isinstance(result.get('data'), str):
                path_str = _clean_path(result['data'])

            lines = ["✅ 转存并整理成功"] if path_str != "文件已接收，无需重复接收！" else ["✅ 文件已转存，❌ 整理失败"]
            if title_hint:
                lines.append(f"\n资源：{title_hint}")
            if path_str:
                if path_str != "文件已接收，无需重复接收！":
                    lines.append(f"路径：{path_str}")
                else:
                    lines.append(f"路径：整理失败，请手动整理！")
            return "\n".join(lines)

        # 失败场景
        error_msg = result.get('message') or msg_value or "未知错误"
        lines = [f"❌ 转存失败\n\n原因：{error_msg}"]
        if title_hint:
            lines.append(f"资源：{title_hint}")
        return "\n".join(lines)


class QywxCallbackHandler:
    """企业微信回调处理器"""
    
    def __init__(self):
        self._crypto = None
        self.message_processor = QywxMessageProcessor()
    
    def _get_crypto(self) -> WXBizMsgCrypt:
        """
        获取加密组件实例（按需创建）
        
        Returns:
            WXBizMsgCrypt: 加密组件实例
            
        Raises:
            ValueError: 当配置参数缺失时抛出异常
        """
        if self._crypto is None:
            # 验证配置参数
            if not all([config.sToken, config.sEncodingAESKey, config.sCorpID]):
                raise ValueError("配置错误")
            
            self._crypto = WXBizMsgCrypt(
                config.sToken,
                config.sEncodingAESKey,
                config.sCorpID
            )
        return self._crypto
    
    def verify_url(self, msg_signature: str, timestamp: str, 
                   nonce: str, echostr: str) -> str:
        """
        验证回调URL
        
        Args:
            msg_signature: 消息签名
            timestamp: 时间戳
            nonce: 随机数
            echostr: 验证字符串
            
        Returns:
            str: 验证结果
        """
        try:
            crypto = self._get_crypto()
            ret, echo_str = crypto.VerifyURL(
                msg_signature, timestamp, nonce, echostr
            )
            
            if ret == 0:
                logger.info(f"企业微信URL验证成功: {echo_str.decode('utf-8')}")
                return echo_str.decode('utf-8')
            else:
                logger.error(f"企业微信URL验证失败: {echo_str}")
                raise ValueError("企业微信URL验证失败")
                
        except Exception as e:
            logger.error(f"企业微信URL验证异常: {e}")
            raise
    
    def handle_message(self, encrypted_msg: str, msg_signature: str,
                      timestamp: str, nonce: str) -> str:
        """
        处理接收到的消息
        
        Args:
            encrypted_msg: 加密的消息
            msg_signature: 消息签名
            timestamp: 时间戳
            nonce: 随机数
            
        Returns:
            str: 加密的回复消息
        """
        return self.message_processor.process_message(
            encrypted_msg, msg_signature, timestamp, nonce
        )


# 全局处理器实例
callback_handler = QywxCallbackHandler()


@wx_nullbr_router.get("/chat")
async def verify_callback(request: Request):
    """
    企业微信回调URL验证接口
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        Response: 验证结果
    """
    try:
        # 获取验证参数
        msg_signature = request.query_params.get('msg_signature')
        timestamp = request.query_params.get('timestamp')
        nonce = request.query_params.get('nonce')
        echostr = request.query_params.get('echostr')
        
        # 验证必要参数
        if not all([msg_signature, timestamp, nonce, echostr]):
            logger.error("缺少必要的验证参数")
            raise HTTPException(status_code=400, detail="缺少必要的验证参数")
        
        # 执行验证
        try:
            result = callback_handler.verify_url(msg_signature, timestamp, nonce, echostr)
            return int(result)
        except ValueError as e:
            logger.error(f"配置错误: {e}")
            raise HTTPException(status_code=500, detail="配置错误")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"企业微信回调验证失败: {e}")
        return json_500("服务器内部错误")


@wx_nullbr_router.post("/chat")
async def receive_message(request: Request):
    """
    企业微信消息接收接口
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        Response: 加密的回复消息
    """
    try:
        # 获取消息参数
        msg_signature = request.query_params.get('msg_signature')
        timestamp = request.query_params.get('timestamp')
        nonce = request.query_params.get('nonce')
        
        # 验证必要参数
        if not all([msg_signature, timestamp, nonce]):
            logger.error("缺少必要的验证参数")
            raise HTTPException(status_code=400, detail="缺少必要的验证参数")
        
        # 获取请求体
        body = await request.body()
        encrypted_msg = body.decode('utf-8')
        
        # 处理消息
        try:
            result = callback_handler.handle_message(
                encrypted_msg, msg_signature, timestamp, nonce
            )
            return Response(content=result, media_type="text/plain")
        except ValueError as e:
            logger.error(f"配置错误: {e}")
            raise HTTPException(status_code=500, detail="配置错误")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"企业微信消息处理失败: {e}", exc_info=True)
        return json_500("服务器内部错误")
