#!/usr/bin/env python3
# Author: Alano 此脚本是站在巨人肩膀上编写的，感谢 @vincent806 @WadeChenn
# Date: 2022/09/08
# plex企业微信通知，基于tautulli通知规则编写 ，需要配合 tautulli 可正常使用。
# 下面两个依赖需要安装，命令如下
# pip3 install pyyaml

#########################依赖库初始化###########################
import os
from importlib import import_module
import sys
# 依赖库列表
import_list=[
    'yaml',
]
# 判断依赖库是否安装,未安装则安装对应依赖库
sourcestr = "https://pypi.tuna.tsinghua.edu.cn/simple/"  # 镜像源
def GetPackage(PackageName):
    PackageName = 'pyyaml' if PackageName == 'yaml' else PackageName
    comand = "pip install " + PackageName +" -i "+sourcestr
    # 正在安装
    print("------------------正在安装" + str(PackageName) + " ----------------------")
    print(comand + "\n")
    os.system(comand)
for v in import_list:
    try:
        import_module(v)
    except ImportError:
        print("未安装 "+v+" 现在开始安装此依赖")
        GetPackage(v)
##############################################################
import yaml
import time
import json, sys
from urllib import request
from urllib import parse
from urllib.error import URLError, HTTPError
# import ssl
import re
# import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
# 翻译
# from googletrans import Translator
import hashlib
import random
import getopt
import requests

class ConfigLoader():
    def loadConfig(self,configpath="config.yml"):
        configpath = configpath.strip()
        basename = os.path.basename(configpath)
        if(configpath == basename):
            scriptdir = os.path.dirname(sys.argv[0])
            configpath = os.path.join(scriptdir,configpath)
        print('reading config from: ' + configpath)
        with open(configpath, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        return(config)

class MessageFormatter():
    def __init__(self):
        self.rounddigit = 2

    def convertBytes(self,inputstr):
        outputstr = inputstr
        pattern = re.compile(r'\d*bytes')
        match = pattern.search(inputstr)
        if match:
            matchstr = match.group()
            size = int(matchstr.replace('bytes',''))
            t = size
            u = "B"
            if t>1024:
                t = t / 1024
                u = "K"
            if t>1024:
                t = t / 1024
                u = 'M'
            if t>1024:
                t = t / 1024
                u = "G"
            if t>1024:
                t = t / 1024
                u = "T"
            if u != "B":
                t = str(round(t,self.rounddigit))
            else:
                t = str(t)
            replacestr = t + u
            outputstr = inputstr.replace(matchstr,replacestr)
        return(outputstr)
    def getHostLocation(self,inputstr):
        outputstr = inputstr
        if inputstr.startswith("http://") or inputstr.startswith("https://"):  #extract host location rather than exposing the entire url where sensitive data might be in place
            parsedurl = parse.urlparse(inputstr)
            outputstr = parsedurl.netloc
        return(outputstr)
# plex企业微信通知，基于tautulli通知规则编写 ，需要配合tautulli可正常使用。
class WxApp():
    def __init__(self):
        self.delimiter = '\n'
        # print('设置了微信白名单代理，地址是：' +  wecom_proxy_url)
        self.endpoint = wecom_api_url + '/cgi-bin/message/send?access_token='

    def formatMessage(self, touser, agentid, title, body, msgtype, tmdb_url, picurl,content_detail,thumb_media_id):
        json_news = {
            "touser": touser,
            "msgtype": "news",
            "agentid": agentid,
            "news": {
                "articles" : [
                    {
                        "title" : title,
                        "description" : body,
                        "url" : tmdb_url,
                        "picurl" : picurl, 
                        #"appid": "wx123123123123123",
                        #"pagepath": "pages/index?userid=zhangsan&orderid=123123123",
                    }
                ]
            },
            "enable_id_trans": 0,
            "enable_duplicate_check": 0,
            "duplicate_check_interval": 1800
        }
        json_mpnews = {
            "touser": touser,
            "msgtype": "mpnews",
            "agentid": agentid,
            "mpnews": {
                "articles" : [
                    {
                        "title" : title,
                        "thumb_media_id" : thumb_media_id,   # 卡片头部图片链接，此图片存储在企业微信中
                        "author" : "检测到更新",                   # 点击卡片进入下级页面后，时间日期的旁边的作者
                        "content_source_url" : tmdb_url,     # 阅读原文链接
                        "digest" : body,                     # 图文消息的描述
                        "content" : content_detail,          # 点击卡片进入下级页面后展示的消息内容
                    }
                ]
            },
            "enable_id_trans": 0,
            "enable_duplicate_check": 0,
            "duplicate_check_interval": 1800
        }
        json_textcard = {
            "touser": touser,
            "msgtype": "textcard",
            "agentid": agentid,
            "textcard": {
                "title" : title,
                "description" : body,
                "url" : tmdb_url,
                "btntxt" : "更多"
            },
            "enable_id_trans": 0,
            "enable_duplicate_check": 0,
            "duplicate_check_interval": 1800
        }
        json_text = {
            "touser" : touser,
            "msgtype" : "text",
            "agentid" : agentid,
            "text" : {
               "content" : title + "\n\n" + body
           },
           "safe":0,
           "enable_id_trans": 0,
           "enable_duplicate_check": 0,
           "duplicate_check_interval": 1800
        }
        if msgtype == "news":
            return json_news
        elif msgtype == "mpnews":
            return json_mpnews
        elif msgtype == "textcard":
            return json_textcard
        else:
            return json_text

    def getToken(self, corpid, secret):
        resp = request.urlopen(wecom_api_url + "/cgi-bin/gettoken?corpid=" + corpid + "&corpsecret=" + secret)
        json_resp = json.loads(resp.read().decode())
        token = json_resp["access_token"]
        return token
    #查询IP所在的地理位置
    def get_ip_info(self, ip_address, appcode):
        url = 'https://ipaddquery.market.alicloudapi.com/ip/address-query'
        # 配置正确的appcode可展示客户端ip归属地。该值为空则不展示。appcode获取方法（显示归属地其实没什么用，保持为空即可。如果一定要用，下面是方法）：在阿里云市场获取免费的IP归属地解析 https://reurl.cc/V1mN0N  进入管理控制台，在已购买的服务中可以找到AppCode
        appcode = appcode
        # ip_address = '10.0.0.1'
        params = {
            'ip': ip_address
        }
        headers = {'Authorization': "APPCODE "+appcode,
            'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'
        }
        response = requests.post(url, data = params, headers = headers)
        # 参数错误，比如: appcode 认证失败
        if response.status_code == 400:
            where = '未知地区'
            return where
        else:
            if response.json()['code'] == 200:
                i = response.json()['data']
                country = i['country']  #国家
              # area = i['area']        #区域
                region = i['region']    #地区/省
                city = i['city']        #城市/市
                isp = i['isp']          #运营商
                # 中国·广东·深圳·电信
                if country == "中国":
                    country = ""
                if region and country:
                    region = "·" + region
                if city:
                    city = "·" + city
                if isp:
                    isp = "·" + isp                
                where = country + region + city + isp
                # where = country + "·" + region + "·" + city + "·" + isp
                return where
            elif response.json()['code'] == 702:
                where = '内网IP'
                return where
            elif response.json()['code'] == 604:
                where = '接口停用'
                return where
            elif response.json()['code'] == 501:
                where = '数据源维护'
                return where
            elif response.json()['code'] == 500:
                where = '系统维护'
                return where
            elif response.json()['code'] == 400:
                where = '参数错误'
                return where
            elif response.json()['code'] == 701:
                # IP地址信息不存在
                where = '地址不存在'
                return where
            else:
                where = response.json()['msg']
                return where
    # 翻译
    def make_sign(self, text, salt, app_id, secret_key):
        raw_sign = app_id + text + str(salt) + secret_key
        return hashlib.md5(raw_sign.encode()).hexdigest()

    def translate(self, text, app_id, secret_key):
        text=text.replace('\n','这里要换行你说气人不气人')
        base_url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
        salt = random.randint(1, 100000)
        
        params = {
            "q": text,
            "from": "en",
            "to": "zh",
            "appid": app_id,
            "salt": salt,
            "sign": self.make_sign(text, salt, app_id, secret_key)
        }
        
        response = requests.get(base_url, params=params)
        data = response.json()
        time.sleep(1)
        
        if "trans_result" in data:
            trans_text = data["trans_result"][0]["dst"]
            trans_text = trans_text.replace('这里要换行你说气人不气人','\n')
            return trans_text
        else:
            error_text = data.get('error_msg', 'Unknown error')
            print(f"Translation API error:{error_text}")
            trans_text = text.replace('这里要换行你说气人不气人','\n')
            return trans_text

    def push(self,config,content):
        #config.yml中导入配置参数
        corpid = config.get('corpid')
        secret = config.get('secret')
        agentid = config.get('agentid')
        touser = config.get('touser')
        msgtype = config.get('msgtype')
        plex_server_url = config.get('plex_server_url')
        picurl_default = config.get('picurl_default')
        picurl_music_default = config.get('picurl_music_default')
        PLEX_TOKEN = config.get('PLEX_TOKEN')
        appcode = config.get('appcode')
        app_id = config.get('app_id','')
        secret_key = config.get('secret_key','')
        thumb_media_id = config.get('thumb_media_id')
        translate_switch = config.get('translate_switch')
        play_music = ""

        # content = ['picurl_plex_update!', 'https://github.com/Alano-i/wecom-notification', '🆕PLEX 服务器更新可用🚀', '0', '0:0:0', '0', '10.0.0.1', '检测时间：2022-09-28 周三 18:08:56', '当前平台：Mac', '当前版本：v3.6587474', '最新版本：v4.023544', '发布时间：2022-09-29', '12新增日志：修复bug', '13修复日志：修复bug,完善体验']
        # content = ['picurl_plex_update!', 'https://downloads.plex.tv/plex-media-server-new/1.29.1.6316-f4cdfea9c/debian/plexmediaserver_1.29.1.6316-f4cdfea9c_amd64.deb', '🆕PLEX 服务器更新可用🚀', '0', '0:0:0', '0', '10.0.0.1', '检测时间：2022-10-21 周5 17:08:52', '当前平台：Linux', '当前版本：1.29.0.6244-819d3678c', '最新版本：1.29.1.6316-f4cdfea9c', '发布时间：2022-10-19', '● (HTTP) Added additional startup state notifications (#13777)\n(Linux) External user-mode graphics drivers no longer need to be installed to use hardware tone mapping on Intel systems (#13788)\n(macOS) Plex Media Server now requires macOS 10.11 or newer to run (#13841)', '● (Auto Update) Old update files are now cleaned up upon server start. (#12693)\n(DVR) EPG data might be lost for new recordings (#13694)\n(DVR) Plex Tuner Service might become unresponsive in certain complex scenarios (#12988)\n(DVR) Sport events recording by team might not be shown in DVR schedule (#13481)\n(Downloads) Corrected a case where played downloaded media was not marked as played on server (#13839)\n(Maintenance) Plex Media Server could quit unexpectedly when asked to clean bundles under certain conditions (#13855)\n(Photos) Photos could get reprocessed for geolocation unnecessarily (#13853)\n(Playback) Corrected playback decisions where metadata contained multiple medias and only some could be direct played or downloaded (#13843)\n(Scanner) Improvements to episode matching logic (#13792)\n(Database) Removed potential SQL syntax error (#13855)']
        # content = ['picurl_tautulli_update!', 'https://downloads.plex.tv/plex-media-server-new/1.29.0.6244-819d3678c/debian/plexmediaserver_1.29.0.6244-819d3678c_amd64.deb', '🆕Tautulli 更新可用🚀', '0', '0:0:0', '0', '', '检测时间：2022-09-29 周4 08:25:00', '当前版本：1.28.2.6151-914ddd2b3', '最新版本：1.29.0.6244-819d3678c', "● (Butler) The server could become unresponsive during database optimization (#13820)\n(HTTP) Certain client apps could quit unexpectedly when connecting to a server during startup maint"]
        # content = ['picurl_tautulli_update!', 'https://github.com/Tautulli/Tautulli/releases/tag/v2.10.5', 'Tautulli 更新啦 💬', '0', '0:0:0', '0', '10.0.0.1', '检测时间：2022-11-08 周2 10:23:13', '当前版本：v2.10.4', '最新版本：v2.10.5', '● ## Changelog\r\n\r\n#### v2.10.5 (2022-11-07)\r\n\r\n* Notifications:\r\n * New: Added edition_title notification parameter. (#1838)\r\n * Change: Track notifications link to MusicBrainz track instead of album.\r\n* Newsletters:\r\n * New: Added months time frame for newsletters. (#1876)\r\n* UI:\r\n * Fix: Broken link on library statistic cards. (#1852)\r\n * Fix: Check for IPv6 host when generating QR code for app registration.\r\n * Fix: Missing padding on condition operator dropdown on small screens.\r\n* Other:\r\n * Fix: Launching browser when webserver is bound to IPv6.\r\n * New: Tautulli can be installed via the Windows Package Manager (winget).\r\n * Change: Separate stdout and stderr console logging. (#1874)\r\n* API:\r\n * Fix: API not returning 400 response code.\r\n * New: Added edition_title to get_metadata API response.\r\n * New: Added collections to get_children_metadata API response.\r\n * New: Added user_thumb to get_history API response.\r\n * New: Validate custom notification conditions before saving notification agents. (#1846)\r\n * Change: Fallback to parent_thumb for seasons in get_metadata API response.\r\n ']

        #处理消息内容
        if(len(content)<8):
            print('Tautulli 传递过来的原始消息如下:')
            if content:
                print("———————————————————————————————————————————————\n")
                print(content)
                print("\n———————————————————————————————————————————————\n")
            else:
                print("———————————————————————————————————————————————\n原始消息为空，可能是未配置、配置错误或未接收到，请检查并重试！\n———————————————————————————————————————————————\n")
            print("➊ 可能是Tautulli未配置通知参数、配置错误。\n➋ Tautulli 未接收到通知参数。\n➌ 用户首次播放也可能获取失败触发此错误，后面就不会了！请检查并重试！\n \n说明: 每条消息至少需要配置8个参数，参考 https://github.com/Alano-i/wecom-notification/tree/main/Plex\n")
            # title = "参数个数不对!"
            title = ""
            art = ""
            content_detail = ""
            ip_address = ""
            body = ""
            sys.exit()
            # body = "➊ 可能是Tautulli未配置通知参数、配置错误。\n➋ Tautulli 未接收到通知参数。\n➌ 用户首次播放也可能获取失败触发此通知，后面就不会了！请检查并重试！\n \n说明: 每条消息至少需要配置8个参数，点击查看Github中各项设置与模板！"
        
        else:
            print('Tautulli 传递过来的原始消息如下:')
            print("———————————————————————————————————————————————\n")
            print(content)
            print("\n———————————————————————————————————————————————\n")
            print('参数传递数量正确，开始处理通知数据！\n')
            art = content[0]
            tmdb_url = content[1]
            title = content[2]
            title = title.replace('：', ' - ')
            # 去掉标题中首尾空格，当评分为空时，末尾会出现空格
            title = title.strip()
            bitrate = content[3]
            # if bitrate and bitrate != "music":
            if bitrate.isdigit():
                bitrate = ('%.1f' %(float(bitrate)/1000))
            elif bitrate == "music":
                play_music = "true"

            # 观看时间
            try:
                watch_time = content[4]
                timelist = watch_time.split(':')
                if len(timelist)==2:
                    watch_time = timelist[0] + '小时 ' + timelist[1] + '分钟'
                    watch_time = watch_time.replace('00小时 ', '')
                    watch_time = watch_time.replace('00分钟', '0分钟')
                else:
                    watch_time = timelist[0] + '小时 ' + timelist[1] + '分钟 ' + timelist[2] + '秒'
                    watch_time = watch_time.replace('00小时 ', '')
                    watch_time = watch_time.replace('00分钟 ', '')
            except Exception as e :
                print(e)
            # 进度条
            progress = content[5]
            progress_all_num = 21
            # 黑白进度条
            progress_do_text = "■"
            progress_undo_text = "□"
            # 彩色进度条
            # progress_do_text = "🟩"
            # progress_undo_text = "⬜"

            progress_do_num = min(progress_all_num, round(0.5 + ((progress_all_num * int(progress)) / 100)))
            # 处理96%-100%进度时进度条展示，正常计算时，进度大于等于96%就已是满条，需单独处理
            if 95 < int(progress) < 100:
                progress_do_num = progress_all_num - 1
            # else:
            #     progress_do_num = progress_do_num
            progress_undo_num = progress_all_num - progress_do_num
            progress_do = progress_do_text * progress_do_num
            progress_undo = progress_undo_text * progress_undo_num
            progress = progress_do + progress_undo
            # ip地址转归属地
            ip_address = content[6]
            # ip_address = '10.0.0.1'
            # ip_address = '103.149.249.30'
            # ip_address = '178.173.224.106'

            # plex 服务器有更新
            if art == "picurl_plex_update!":
                print('Plex 服务器有更新，开始处理更新日志！\n')
                changelog_add = content[12]
                changelog_fix = content[13]
                if changelog_add:
                    if translate_switch == "on" and secret_key and app_id:
                        changelog_add_origin = "<p style='line-height:135%;opacity:0.75'><font color=#888888><small><small>" + changelog_add + "</small></small><br/></font></p>"
                        changelog_add_origin = changelog_add_origin.replace('\n', '<br/>● ')
                        print('开始翻译【新增功能】日志！\n')
                        # print(f'翻译前:{changelog_add}')
                        changelog_add_translate = self.translate(changelog_add,app_id,secret_key)
                        # print(f'翻译后:{changelog_add_translate}')
                        changelog_add_translate = "··························· <b><small><big>新增功能</b></big></small> ···························<br/>" + "<p style='line-height:165%'><small>" + changelog_add_translate + "</small></p>"
                        changelog_add_translate = changelog_add_translate.replace('\n', '<br/>●')
                        changelog_add_translate = changelog_add_translate.replace('（', ' (')
                        changelog_add_translate = changelog_add_translate.replace('）', ') ')
                        changelog_add_translate = changelog_add_translate
                    else:
                        print('未开启日志翻译或者未设置 app_id 和 secret_key，【新增功能】日志将展示为英文！\n')
                        changelog_add_origin = "··························· <b><small><big>新增功能</b></big></small> ···························<br/>" + "<p style='line-height:165%'><small>" + changelog_add + "</small></p>"
                        changelog_add_origin = changelog_add_origin.replace('\n', '<br/>●')
                        changelog_add_translate = ""
                if changelog_fix:
                    if translate_switch == "on" and secret_key and app_id:
                        changelog_fix_origin = "<p style='line-height:135%;opacity:0.75'><font color=#888888><small><small>" + changelog_fix + "</small></small><br/></font></p>"
                        changelog_fix_origin = changelog_fix_origin.replace('\n', '<br/>● ')
                        print('开始翻译【修复功能】日志！\n')
                        changelog_fix_translate = self.translate(changelog_fix,app_id,secret_key)
                        changelog_fix_translate = "··························· <b><big><small>修复日志</small></b></big> ···························<br/>" + "<p style='line-height:165%'><small>" + changelog_fix_translate + '</small></p>'
                        changelog_fix_translate = changelog_fix_translate.replace('\n', '<br/>●')
                        changelog_fix_translate = changelog_fix_translate.replace('（', ' (')
                        changelog_fix_translate = changelog_fix_translate.replace('）', ') ')
                    else:
                        print('未开启日志翻译或者未设置 app_id 和 secret_key，【修复功能】日志将展示为英文！\n')
                        changelog_fix_origin = "··························· <b><small><big>修复日志</b></big></small> ···························<br/>" + "<p style='line-height:165%'><small>" + changelog_fix + "</small></p>"
                        changelog_fix_origin = changelog_fix_origin.replace('\n', '<br/>●')
                        changelog_fix_translate = ""
                content_detail = changelog_add_translate + changelog_add_origin + changelog_fix_translate  + changelog_fix_origin
                if not content_detail:
                    print('暂无更新日志！\n')
                    content_detail = "暂无更新日志"
                content = content[0:12]
                # 切换为 mpnews 通知模式
                if thumb_media_id:
                    msgtype = "mpnews"
                else:
                    msgtype = "textcard"
                body = ""
                for i in range(7,len(content)):
                    v = content[i]
                    v = MessageFormatter().convertBytes(v)
                    v = MessageFormatter().getHostLocation(v)
                    body = body + v + self.delimiter
            # tautulli 有更新
            elif art == "picurl_tautulli_update!":
                print('Tautulli 服务器有更新，开始处理更新日志！\n')
                changelog = content[10]
                if changelog:
                    changelog = "<small>" + changelog + "</small>"
                    changelog = changelog.replace('\r\n*', '<br/><b><big>●')
                    changelog = changelog.replace(':\r\n', ':</big></b><br/>')
                    changelog = changelog.replace('*', '○')
                    changelog = changelog.replace('\n', '<br/>')
                    # changelog = changelog.replace('*', '<br/>')
                    # changelog_origin = changelog
                    content_detail = changelog
                    # changelog_translate = self.translate(changelog_origin)
                    # content_detail = changelog_translate + "<br/>" + changelog_origin
                    # content_detail = content_detail.replace('●', '● ')
                    # content_detail = content_detail.replace('○', '○ ')
                    # content_detail = content_detail.replace('○ 新：', '○ 新增：')
                else:
                    print('暂无更新日志！\n')
                    content_detail = "暂无更新日志"
                content = content[0:10]
                # 切换为 mpnews 通知模式
                if thumb_media_id:
                    msgtype = "mpnews"
                else:
                    msgtype = "textcard"
                body = ""
                for i in range(7,len(content)):
                    v = content[i]
                    v = MessageFormatter().convertBytes(v)
                    v = MessageFormatter().getHostLocation(v)
                    body = body + v + self.delimiter
            # 播放 暂停 停止通知
            else:
                content_detail = ""
                body = ""
                for i in range(7,len(content)):
                    v = content[i]
                    v = v.replace('Direct Play', '直接播放')
                    v = v.replace('Direct Stream', '直接串流')
                    v = v.replace('Transcode', '转码播放')
                    v = v.replace('0.2 Mbps 160p', '160P · 0.2Mbps')
                    v = v.replace('0.3 Mbps 240p', '240P · 0.3Mbps')
                    v = v.replace('0.7 Mbps 328p', '328P · 0.7Mbps')
                    v = v.replace('1.5 Mbps 480p', '480P · 1.5Mbps')
                    v = v.replace('2 Mbps 720p', '720P · 2.0Mbps')
                    v = v.replace('3 Mbps 720p', '720P · 3.0Mbps')
                    v = v.replace('4 Mbps 720p', '720P · 4.0Mbps')
                    v = v.replace('8 Mbps 1080p', '1080P · 8.0Mbps')
                    v = v.replace('10 Mbps 1080p', '1080P · 10Mbps')
                    v = v.replace('12 Mbps 1080p', '1080p · 12Mbps')
                    v = v.replace('20 Mbps 1080p', '1080P · 20Mbps')
                    v = v.replace('Original · HDR10', '原始质量')
                    v = v.replace('Original · SDR', '原始质量')
                    v = v.replace('Original · HDR', '原始质量')
                    v = v.replace('Original · Dolby Vision/', '原始质量 · ')
                    v = v.replace('Original · Dolby Vision', '原始质量')
                    v = v.replace('Dolby Vision/HDR10 ·', '杜比视界 ·')
                    v = v.replace('Dolby Vision/HDR ·', '杜比视界 ·')
                    v = v.replace('Original', '原始质量')
                    v = v.replace('HDR10 HDR10', 'HDR10')
                    v = v.replace('HDR10 HDR', 'HDR10')
                    v = v.replace('HDR10 SDR', 'HDR10')
                    v = v.replace('SDR SDR', 'SDR')
                    v = v.replace('HDR HDR', 'HDR')
                    v = v.replace('HDR SDR', 'HDR')
                    v = v.replace('bitrate!', bitrate + 'Mbps')
                    v = v.replace('watchtime!', watch_time)
                    v = v.replace('Dolby Vision ·', '杜比视界 ·')
                    v = v.replace('4k ·', '4K ·')
                    v = v.replace('2160 ·', '2160P ·')
                    v = v.replace('1080 ·', '1080P ·')
                    v = v.replace('720 ·', '720P ·')
                    v = v.replace('progress!',progress )
                    # 所有空格全部替换为特殊字符串replace!，后面可通过操作这个字符串来控制空格数量（大于2个空格的替换为2个空格，一个空格的则不变）
                    v = v.replace(' ', 'replace!')
                    # 去掉换行主要用于去掉剧情简介的换行
                    v = v.replace('\n', '')
                    # 去掉中文空格，主要用于去掉剧情简介的缩进
                    v = v.replace('　', '')
                    # 剧情简介有缩进的另一种情况，可能是通过英文空格来缩进的，全部去掉
                    v = v.replace('replace!replace!replace!replace!replace!replace!replace!replace!replace!replace!', '')
                    v = v.replace('replace!replace!replace!replace!replace!replace!replace!replace!replace!', '')
                    v = v.replace('replace!replace!replace!replace!replace!replace!replace!replace!', '')
                    v = v.replace('replace!replace!replace!replace!replace!replace!replace!', '')
                    # 大于等于2个空格的替换为2个空格，一个空格的则不变
                    v = v.replace('replace!replace!replace!replace!replace!replace!', '  ')
                    v = v.replace('replace!replace!replace!replace!replace!', '  ')
                    v = v.replace('replace!replace!replace!replace!', '  ')
                    v = v.replace('replace!replace!replace!', '  ')
                    v = v.replace('replace!replace!', '  ')
                    v = v.replace('replace!', ' ')
                    v = MessageFormatter().convertBytes(v)
                    v = MessageFormatter().getHostLocation(v)
                    body = body + v + self.delimiter
                if (len(body)>5000):  #bark has limitation of 5000 characters in body
                    body = body[0:5000]

        body = body.replace(' · 0.0Mbps', '')
        # body = body.replace(' 100%', ' 完')
        body = body.replace('周1', '周一')
        body = body.replace('周2', '周二')
        body = body.replace('周3', '周三')
        body = body.replace('周4', '周四')
        body = body.replace('周5', '周五')
        body = body.replace('周6', '周六')
        body = body.replace('周7', '周日')
        body = body.replace('.local', '')
        if ip_address:
            if appcode:
                print('已配置 appcode，处理IP归属地！\n')
                where = self.get_ip_info(ip_address, appcode)
                # where = where.replace('中国·', '')
                body = body.replace('whereareyou!', " (" + where + ")")
                body = body.replace('(·', '(')
                body = body.replace('·)', ')')
            else:
                print('未配置 appcode，按默认类型处理IP归属地！\n')
                body = body.replace('whereareyou!', '')
        # 只保留一个换行
        body = re.sub('\n+','\n',body)
        # 删除字符串末尾所有换行符
        body = body.strip('\n')
        # if (len(art)<18):    #如果没有获取到本地背景封面就使用下方图片作为缺省图，正常art=/library/metadata/xxxx/xxxxxxx 长度大概30多，取 “/library/metadata/” 为临界长度，也可判断为空
        if not art:    #如果没有获取到本地背景封面就使用下方图片作为缺省图，正常art=/library/metadata/xxxx/xxxxxxx 长度大概30多，取 “/library/metadata/” 为临界长度，也可判断为空
            if play_music:
                picurl = picurl_music_default
            else:
                picurl = picurl_default
                tmdb_url = "https://github.com/Alano-i/wecom-notification/tree/main/Plex"
        elif art == "picurl_plex_server_down!":
            picurl = picurl_default
        elif art == "picurl_tautulli_database_corruption!":
            picurl = picurl_default
        else:
            picurl = plex_server_url + art + '?X-Plex-Token=' + PLEX_TOKEN

        #initialize header and endpoint
        header = {
            "Content-Type": "application/json;charset=UTF-8"
        }
        # 获取token
        token = self.getToken(corpid, secret)
        endpoint = self.endpoint + token

        #format posting data
        message = self.formatMessage(touser, agentid, title, body, msgtype, tmdb_url, picurl,content_detail,thumb_media_id)
        print('消息处理完毕，先来预览看看将要推送到微信的消息是什么样的：')
        print("———————————————————————————————————————————————\n标题：" + title)
        print("内容：" + body + "\n———————————————————————————————————————————————\n")
        #send data to wxapp
        try:
            postdata = json.dumps(message)
            postdata = postdata.encode("utf-8")
            handler = request.Request(url=endpoint, data=postdata, headers=header) 
            print('好了，预览也预览了，准备干活，开始请求企业微信接口推送通知！\n')
            resp = request.urlopen(handler) 
            return(resp.read().decode())
        except HTTPError as e:
            # do something
            return('Error code: ', e.code)
        except URLError as e:
            # do something
            return('Reason: ', e.reason)
        else:
            # do something
            return('Unknown exception!')

if __name__ == '__main__':

    # load config
    opts,args = getopt.getopt(sys.argv[1:],'-c:',['config='])
    configpath = "config.yml"
    for optname,optvalue in opts:
        if optname in ('-c','--config'):
            configpath = optvalue # config from -c or --config parameter
            break
    config = ConfigLoader().loadConfig(configpath)
  
    for service in config:
        if service == 'wxapp':
            print("\n启用企业微信发送通知，下面开始处理\n")
            wecom_proxy_url = config[service].get('wecom_proxy_url')
            if wecom_proxy_url:
                print('设置了微信白名单代理，地址是：' +  wecom_proxy_url + '\n')
                wecom_api_url = wecom_proxy_url
            else:
                print('未设置微信白名单代理，使用官方 api 地址\n')
                wecom_api_url = 'https://qyapi.weixin.qq.com'            
            handler = WxApp()
            resp = handler.push(config[service], args)
            print('推送返回结果：' +service + ': ' + str(resp))
            print("\n企业微信通知推送处理完毕！\n")