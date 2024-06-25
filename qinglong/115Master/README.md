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
ql repo https://github.com/Alano-i/Plugins.git "qinglong/115Master/sign|qinglong/115Master/crack_captcha|qinglong/115Master/pull.py|qinglong/115Master/push_server" "" "__init__|component|config|get_new_cookie|notify|requirements|pull|push|del|pull_after" "" "py|txt"
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
| pic_url_115     | 115通知封面               |
| push_notify_115     | 115通知开关，on 或 off               |
| normal_notify_115     | 115无风控通知开关，on 或 off               |
| media_id_115     | 企业微信 封面素材 Media id               |
| del_root_id     | 删除大于10万的文件夹，文件夹id               |


## 添加 cookie
`Alano-i_Plugins/qinglong/115Master/cookies` 文件夹内分别在 `pull.txt` `push.txt` 中填两个不同设备的 `cookie` (必须不同设备)

## 定时任务设置参数
### 服务端
别人拉你的文件需要启动这个服务：找到 `push_server.py` 的定时任务
```console
task Alano-i_Plugins/qinglong/115Master/push_server.py -cp ./cookies/push.txt -p 1150 -ur urllib3
```

### 客户端
你拉别人的文件运行的服务：找到 `pull.py` 的定时任务
```console
task Alano-i_Plugins/qinglong/115Master/pull.py -ur urllib3 -s 90 -cp ./cookies/pull.txt -m 4 -u https://xxx.com -p 12345678 -t 23456789
```
`-u` 对方 push_server 的外网地址（就是第一步反代的那个）

`-p` 对方网盘文件夹的 `CID`

`-t` 你网盘文件夹的 `CID`













