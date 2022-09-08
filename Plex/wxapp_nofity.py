#!/usr/bin/env python
# Author: Alano
# Date: 2022/09/08
# plex企业微信通知，基于tautulli通知规则编写 ，需要配合 tautulli 可正常使用。
# pip3 install pyyaml
#########################依赖库初始化###########################
# 依赖库列表
import os
from importlib import import_module
import sys
import_list=[
    'yaml',
]
# 判断依赖库是否安装,未安装则安装对应依赖库
sourcestr = "https://pypi.tuna.tsinghua.edu.cn/simple/"  # 镜像源
def GetPackage(PackageName):
    comand = "pip install " + PackageName +" -i "+sourcestr
    # 正在安装
    print("------------------正在安装" + str(PackageName) + " ----------------------")
    print(comand + "\n")
    os.system(comand)
for v in import_list:
    try:
        import_module(v)
    except ImportError:
        print("Not find "+v+" now install")
        GetPackage(v)
##############################################################

import yaml
import json, sys
import os
from urllib import request
from urllib import parse
from urllib.error import URLError, HTTPError
import ssl
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
import time
import hmac
import hashlib
import base64
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
        self.endpoint = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token='

    def formatMessage(self, touser, agentid, title, body, messagetype, tmdb_url, picurl):
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
        if messagetype == "news":
            return json_news
        elif messagetype == "textcard":
            return json_textcard
        else:
            return json_text

    def getToken(self, corpid, secret):
        resp = request.urlopen("https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=" + corpid + "&corpsecret=" + secret)
        json_resp = json.loads(resp.read().decode())
        token = json_resp["access_token"]
        return token
    #查询IP所在的地理位置
    def get_ip_info(self, ip_address, appcode):
        url = 'https://ipaddquery.market.alicloudapi.com/ip/address-query'
        # 配置正确的appcode可展示客户端ip归属地。该值为空则不展示。appcode获取方法（显示归属地其实没什么用，保持为空即可。如果一定要用，下面是方法）：在阿里云市场购买的1元含2万5千次请求，或者试用用免费的 https://reurl.cc/W103r5 进入管理控制台，在已购买的服务中可以找到AppCode
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
                area = i['area']        #区域
                region = i['region']    #地区/省
                city = i['city']        #城市/市
                isp = i['isp']          #运营商
                where = country + "·" + region + "·" + city + "·" + isp
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
            
    def push(self,config,content):
        #config.yml中导入配置参数
        corpid = config.get('corpid')
        secret = config.get('secret')
        agentid = config.get('agentid')
        touser = config.get('touser')
        messagetype = config.get('type')
        plex_server_url = config.get('plex_server_url')
        picurl_default = config.get('picurl_default')
        plex_token = config.get('plex_token')
        appcode = config.get('appcode')

        #处理消息内容
        if(len(content)<0):
            title = "参数个数不对!"
            body = "null"
        else:
            art = content[0]
            tmdb_url = content[1]
            title = content[2]
            title = title.replace('：', ' - ')
            # 去掉标题中首尾空格，当评分为空时，末尾会出现空格
            title = title.strip()
            bitrate = content[3]
            bitrate = ('%.1f' %(float(bitrate)/1000))
            # 观看时间
            try:
                watch_time = content[4]
                timelist = watch_time.split(':')
                if len(timelist)==2:
                    watch_time = timelist[0] + '小时 ' + timelist[1] + '分钟'
                else :
                    watch_time = timelist[0] + '小时 ' + timelist[1] + '分钟 ' + timelist[2] + '秒'
                watch_time = watch_time.replace('00小时 00分钟', '0分钟')
                watch_time = watch_time.replace('00小时 ', '')
                watch_time = watch_time.replace('00分钟 ', '')
            except Exception as e :
                print(e)
            # 进度条
            progress = content[5]
            progress_all_num = 21
            progress_do_text = "■"
            progress_undo_text = "□"
            progress_do_num = round(0.5 + ((progress_all_num * int(progress)) / 100))
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
                v = v.replace('Original · Dolby Vision', '原始质量')
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
        body = body.replace(' 100%', '100%')
        body = body.replace('周1', '周一')
        body = body.replace('周2', '周二')
        body = body.replace('周3', '周三')
        body = body.replace('周4', '周四')
        body = body.replace('周5', '周五')
        body = body.replace('周6', '周六')
        body = body.replace('周7', '周日')
        body = body.replace('MacBook-Pro.local', 'MBP')
        if appcode:
            where = self.get_ip_info(ip_address, appcode)
            where = where.replace('中国·', '')
            body = body.replace('whereareyou!', " (" + where + ")")
        else:
            body = body.replace('whereareyou!', '')
        # 只保留一个换行
        body = re.sub('\n+','\n',body)
        # 删除字符串末尾所有换行符
        body = body.strip('\n')
        # body = body + " (" + where + ")"
        if (len(art)<18):    #如果没有获取到本地背景封面就使用下方图片作为缺省图，正常art=/library/metadata/xxxx/xxxxxxx 长度大概30多，取 “/library/metadata/” 为临界长度，也可判断为空
            picurl = picurl_default
            tmdb_url = ""
        else:
            picurl = plex_server_url + art + '?X-Plex-Token=' + plex_token
            picurl = picurl.replace('picurl_plex_update!', picurl_default)
            picurl = picurl.replace('picurl_tautulli_update!', picurl_default)

        #initialize header and endpoint
        header = {
            "Content-Type": "application/json;charset=UTF-8"
        }
        # 获取token
        token = self.getToken(corpid, secret)
        endpoint = self.endpoint + token

        #format posting data
        message = self.formatMessage(touser, agentid, title, body, messagetype, tmdb_url, picurl)

        #send data to wxapp
        try:
            postdata = json.dumps(message)
            postdata = postdata.encode("utf-8")
            handler = request.Request(url=endpoint, data=postdata, headers=header) 
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
            handler = WxApp()
            resp = handler.push(config[service], args)
            print(service + ': ' + str(resp))
