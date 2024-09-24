## 青龙
`docker` 映射端口 `1150`，然后反代`青龙的ip:1150` 以获得外网可访问地址
## 依赖
依赖管理-创建依赖-python3-是-填入依赖名称
```console
python-115
cachetools
uvicorn
numpy==1.26.4
ddddocr==1.4.11
colored
pygments
posixpatht
tenacity
requests
```

## 订阅
订阅管理-创建订阅-粘贴下方代码
```console
ql repo https://github.com/Alano-i/Plugins.git "qinglong/115Master/qrcode_cookie_115_web|qinglong/115Master/sign|qinglong/115Master/crack_captcha|qinglong/115Master/pull.py|qinglong/115Master/push_server|qinglong/115Master/life_list_monitor|qinglong/115Master/get_new_cookie|qinglong/115Master/add_env|qinglong/115Master/qrcode_cookie_115_web" "" "__init__|component|config|notify_server|qinglong_api|requirements|pull|push|del|pull_after|predicate" ""
```
名称
```console
115Master
```
定时规则
```console
8 1 * * *
```

## 环境变量

| 变量名      | 说明                   |
| :---------- | :--------------------- |
| cookie_115     | cookie               |
| touser     | 企业微信通知接收者               |
| corpid     | 企业 ID               |
| corpsecret     | corp secret               |
| agentid     | 应用 ID               |
| wecom_proxy_api_url     | 企业微信api代理，按需添加               |
| pic_url_115     | 115通知封面               |
| push_notify_115     | 115通知开关，on 或 off               |
| normal_notify_115     | 115无风控通知开关，on 或 off               |
| media_id_115     | 企业微信 封面素材 Media id               |
| del_root_id     | 删除大于10万的文件夹，文件夹id               |


## 添加 cookie
`Alano-i_Plugins/qinglong/115Master/cookies` 文件夹内（如果没有就新建一个）分别新建 `pull.txt` `push.txt` 两个文件，并分别填入两个不同设备的 `cookie` (必须不同设备)

## 定时任务设置参数

### 获取cookie网页端
找到 `qrcode_cookie_115_web.py` 的定时任务（需要在青龙的docker参数中将7115端口映射出来）
```console
task Alano-i_Plugins/qinglong/115Master/qrcode_cookie_115_web.py -p 7115 -H 0.0.0.0
```


### 服务端
别人拉你的文件需要启动这个服务：找到 `push_server.py` 的定时任务
```console
task Alano-i_Plugins/qinglong/115Master/push_server.py -cp ./cookies/push.txt -p 1150 -ur urllib3 -r 12345678
```
说明：可指定挂载目录，使用 `-r 目录cid` ，默认不加 `-r` 参数则挂载根目录（注意不能添加 `-r 0` 来挂载根目录）。 

### 客户端
你拉别人的文件运行的服务：找到 `pull.py` 的定时任务
```console
task Alano-i_Plugins/qinglong/115Master/pull.py -ur urllib3 -s 90 -cp ./cookies/pull.txt -m 4 -u https://xxx.com -p 12345678 -t 23456789
```
`-u` 对方 push_server 的外网地址（就是第一步反代的那个）

`-p` 对方网盘文件夹的 `CID`

`-t` 你网盘文件夹的 `CID`

## 致谢
以上功能的核心实现，都来自 [@ChenyangGao](https://github.com/ChenyangGao) 大佬的 [项目](https://github.com/ChenyangGao/web-mount-packs)，本项目只做了微不足道的搬运而已，感谢！












