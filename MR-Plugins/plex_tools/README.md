# 🌎 PLEX 工具箱
MR插件，PLEX 工具箱，原作者是BeiMou(yewei)，感谢。在此基础上修改优化了其中各项功能，并添加了许多其他实用功能！

主要功能如下图所示：

<div align=center><img src="https://github.com/Alano-i/Plex-Tools/assets/68833595/b4d3ea32-ef97-435a-a8c5-8a0723cea8d2" width="852" /></div>

## 使用说明
- 将 `plex_tools` 文件夹放到 `Plugins` 文件夹，配置好各项设置。
- 添加海报信息功能中，恢复模式仅在成功处理过的媒体上才能生效！

## 更新说明（*必看*，重要）
- 3.0 版本（2023-7-20发布）之后海报备份文件夹改为 `/data/poster_backup`
- 如果 3.0 版本之前安装过此插件，需要将`/data/plugins/plex_tools/overlays`目录下面的 `poster_backup` 目录移动到 `/data` 下面
- 本地 `/data/poster_backup` 文件夹中的内容不可删除，里面存放的是媒体的海报备份。
- 如果已经删除了，需要手动重新设置为未处理过的海报再次运行 plex_tools 插件方可正常使用

## 为海报添加媒体信息

<img width="1628" alt="image" src="https://github.com/Alano-i/Plex-Tools/assets/68833595/aaf76b61-8fba-44f6-96fe-8f0635e1b3d8">

### 清理不需要的海报图片
当多次运行添加媒体信息后可能会有一些不需要的海报， [按此项目的方法清理](https://github.com/meisnate12/Plex-Image-Cleanup)

建议使用docker版，Docker Compose 文件示例：
```console
version: "2.1"
services:
  plex-image-cleanup:
    image: meisnate12/plex-image-cleanup
    container_name: plex-image-cleanup
    environment:
      - TZ=TIMEZONE #optional
    volumes:
      - /path/to/config:/config
      - /path/to/plex:/plex
    restart: unless-stopped
```

安装好之后，在/config 文件夹下建立环境变量配置文件 `.env`,示例如下：
```console
PLEX_PATH=/plex                *这里需要修改,填plex的Plex Media Server目录映射到容器的目录
MODE=remove
SCHEDULE="05:15|daily"
PLEX_URL=http://10.0.0.1:32400 *这里需要修改
PLEX_TOKEN=12345678            *这里需要修改
DISCORD=                        这里按需填 DISCORD webhook url,可以收到清理通知
TIMEOUT=600
SLEEP=60
IGNORE_RUNNING=True
LOCAL_DB=False
USE_EXISTING=False
PHOTO_TRANSCODER=True
EMPTY_TRASH=True
CLEAN_BUNDLES=True
OPTIMIZE_DB=True
TRACE=True
LOG_REQUESTS=True
```


