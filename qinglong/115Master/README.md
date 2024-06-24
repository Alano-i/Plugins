## 青龙
`docker` 映射端口 `1150`，然后反代`青龙的ip:1150` 已获得外网可访问地址
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
ql repo https://github.com/Alano-i/Plugins.git "qinglong/115Master/sign|qinglong/115Master/crack_captcha|qinglong/115Master/pull.py|qinglong/115Master/push_server" "" "__init__|component|config|get_new_cookie|notify|requirements|pull|push|del|pull_after" "" "py txt"
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
<img width="1248"  alt="image" src="https://github.com/Alano-i/Plugins/assets/68833595/4a756bd8-65f0-4a6e-859b-ba8c970d387f">

## 添加 cookie
`Alano-i_Plugins/qinglong/115Master/cookies` 文件夹内有分别在 `pull.txt` `push.txt` 中填两个不同设备的 `cookie` (必须不同设备)

## 定时任务设置参数
找到 `push_server.py` 的定时任务
```console
task Alano-i_Plugins/qinglong/115Master/push_server.py -cp ./cookies/push.txt -p 1150 -ur urllib3
```

找到 `pull.py` 的定时任务
```console
task Alano-i_Plugins/qinglong/115Master/pull.py -ur urllib3 -s 90 -cp ./cookies/pull.txt -m 4 -u https://xxx.com -p 12345678 -t 23456789
```
`-u` 对方 push_server 的外网地址（就是第一步反代的那个）

`-p` 对方网盘文件夹的 `CID`

`-t` 你网盘文件夹的 `CID`













