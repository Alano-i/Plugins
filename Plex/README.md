
# Plex 企业微信通知
Plex 企业微信通知，基于 Tautulli 通知规则编写 ，需要配合 Tautulli 使用。

可通过微信接收 Plex 服务器的`影片入库` `播放` `报错` 等通知，展示 `当前播放方式` `谁在播放` `播放进度` 等以及一些影片的基本信息。  
>ps: 显示效果基于 6.1寸 iPhone 微信字体大小为"标准"设计，其他分辩率或微信字体大小显示效果可能会不同。

## 效果预览
<div align=center><img src="https://github.com/Alano-i/wecom-notification/blob/main/Plex/pic/preview.png" width="1000" /></div>

## 使用方法
- 将`wxapp_notify.py` 和`config.yml`文件放入 tautulli 的/config/script/目录下，`wxapp_notify.py`不需要改动，在`config.yml`中填入自己的配置
- 如果想收到服务器有更新时带图片的通知，在 Tautulli 设置中`开启服务器更新监控`（参见下方图片有说明），并将本项目 `pic` 文件夹下 update_bg.gif（不要改后缀，保持gif，你也可以传你自己喜欢的图） 需要传到企业微信素材库从而获取 `thumb_media_id` 填入config中，[thumb_media_id获取方法](https://alanoo.notion.site/thumb_media_id-64f170f7dcd14202ac5abd6d0e5031fb)
- Tautulli 需要添加 `yaml` `googletrans` 支持（进入tautulli命令行，执行以下命令，或在 tautulli 的 `start.sh` 中加入自动安装的模块）（翻译调用谷歌翻译，需要网络环境支持,如果网络环境不支持或不想翻译，将 `translate_switch` 设置为 `off`,默认为`on`，如果网络环境不支持还设置为 `on`，将会报错 ）
```console
pip3 install pyyaml -i http://pypi.douban.com/simple/  --trusted-host pypi.douban.com
```
```console
pip3 install googletrans==4.0.0-rc1 -i http://pypi.douban.com/simple/  --trusted-host pypi.douban.com
```
- 增加白名单IP代理域名设置，在config.yml中设置
- Tautulli  Settings-General-Time Format 设置为 `HH:mm:ss`
- Tautulli 中新建通知-类型选-script
- 选择 `wxapp_notify.py`
- 填入下方通知代码
- 保存即可

## 企业微信几个参数配置方法
<div align=center><img src="https://github.com/Alano-i/wecom-notification/blob/main/Plex/pic/guide-wecom.png" width="1000" /></div>

## 需要填入 Tautulli 中的通知代码
需要哪种场景的通知就将下面对应的代码全部复制到 Tautulli
<div align=center><img src="https://github.com/Alano-i/wecom-notification/blob/main/Plex/pic/guide-tautulli.png" width="1000" /></div>
<div align=center><img src="https://user-images.githubusercontent.com/68833595/193074170-a68660df-3e1f-46f1-8074-6b8a6d439b8e.png" width="1000" /></div>

**播放通知**
```console
<movie>
{art} {themoviedb_url} ▶️{title}" @"{user}{"  "⭐️<rating>} {bitrate} 0:0:0 {progress_percent} {ip_address} {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} {transcode_decision}" ⤷ "{quality_profile}{" · "<stream_video_dynamic_range>} "progress! "{<progress_percent>%} {播放时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} 观看进度：{progress_time}({progress_percent}%){"  "剩余<remaining_duration>分钟} {文件大小：<file_size>} {首映日期：<air_date>} {播放设备：<player>}{" · "<product>} {设备地址：<ip_address>}"whereareyou!"
</movie>
<episode>
{art} {themoviedb_url} ▶️{show_name}" "S{season_num00}·E{episode_num00}" @"{user}{"  "⭐️<rating>} {bitrate} 0:0:0 {progress_percent} {ip_address} {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} {transcode_decision}" ⤷ "{quality_profile}{" · "<stream_video_dynamic_range>} "progress! "{<progress_percent>%} {播放时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} 观看进度：{progress_time}({progress_percent}%){"  "剩余<remaining_duration>分钟} {单集标题：<episode_name>} {文件大小：<file_size>} {首映日期：<air_date>} {播放设备：<player>}{" · "<product>} {设备地址：<ip_address>}"whereareyou!"
</episode>
<track>
{art} {themoviedb_url} ▶️{track_name}" @"{user}{"  "⭐️<rating>} music 0:0:0 {progress_percent} {ip_address} {library_name}{" · "<track_artist>}{" · "<album_name>}{" · "<duration>分钟} {transcode_decision}" ⤷ "{quality_profile}{" · "<stream_video_dynamic_range>} "progress! "{<progress_percent>%} {播放时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} 播放进度：{progress_time}({progress_percent}%){"  "剩余<remaining_duration>分钟} {文件大小：<file_size>} {首映日期：<air_date>} {播放设备：<player>}{" · "<product>} {设备地址：<ip_address>}"whereareyou!"
</track>
```

**继续播放通知**
```console
<movie>
{art} {themoviedb_url} ▶️{title}" @"{user}{"  "⭐️<rating>} {bitrate} 0:0:0 {progress_percent} {ip_address} {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} {transcode_decision}" ⤷ "{quality_profile}{" · "<stream_video_dynamic_range>} "progress! "{<progress_percent>%} {继续时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} 观看进度：{progress_time}({progress_percent}%){"  "剩余<remaining_duration>分钟} {文件大小：<file_size>}"  "{video_codec!u}" ⤷ "{stream_video_codec!u} {首映日期：<air_date>} {播放设备：<player>}{" · "<product>} {设备地址：<ip_address>}"whereareyou!"
</movie>
<episode>
{art} {themoviedb_url} ▶️{show_name}" "S{season_num00}·E{episode_num00}" @"{user}{"  "⭐️<rating>} {bitrate} 0:0:0 {progress_percent} {ip_address} {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} {transcode_decision}" ⤷ "{quality_profile}{" · "<stream_video_dynamic_range>} "progress! "{<progress_percent>%} {继续时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} 观看进度：{progress_time}({progress_percent}%){"  "剩余<remaining_duration>分钟} {单集标题：<episode_name>} {文件大小：<file_size>}"  "{video_codec!u}" ⤷ "{stream_video_codec!u} {首映日期：<air_date>} {播放设备：<player>}{" · "<product>} {设备地址：<ip_address>}"whereareyou!"
</episode>
<track>
{art} {themoviedb_url} ▶️{track_name}" @"{user}{"  "⭐️<rating>} music 0:0:0 {progress_percent} {ip_address} {library_name}{" · "<track_artist>}{" · "<album_name>}{" · "<duration>分钟} {transcode_decision}" ⤷ "{quality_profile}{" · "<stream_video_dynamic_range>} "progress! "{<progress_percent>%} {继续时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} 播放进度：{progress_time}({progress_percent}%){"  "剩余<remaining_duration>分钟} {文件大小：<file_size>} {首映日期：<air_date>} {播放设备：<player>}{" · "<product>} {设备地址：<ip_address>}"whereareyou!"
</track>
```

**停止播放通知**
```console
<movie>
{art} {themoviedb_url} ⏹️{title}" @"{user}{"  "⭐️<rating>} {bitrate} {stream_time} {progress_percent} {ip_address} {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} {transcode_decision}" ⤷ "{quality_profile}{" · "<stream_video_dynamic_range>} "progress! "{<progress_percent>%} {停止时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} 观看时长：watchtime! 观看进度：{progress_time}({progress_percent}%){"  "剩余<remaining_duration>分钟} {文件大小：<file_size>} {首映日期：<air_date>} {播放设备：<player>}{" · "<product>} {设备地址：<ip_address>}"whereareyou!"
</movie>
<episode>
{art} {themoviedb_url} ⏹️{show_name}" "S{season_num00}·E{episode_num00}" @"{user}{"  "⭐️<rating>} {bitrate} {stream_time} {progress_percent} {ip_address} {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} {transcode_decision}" ⤷ "{quality_profile}{" · "<stream_video_dynamic_range>} "progress! "{<progress_percent>%} {停止时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} 观看时长：watchtime! 观看进度：{progress_time}({progress_percent}%){"  "剩余<remaining_duration>分钟} {单集标题：<episode_name>} {文件大小：<file_size>} {首映日期：<air_date>} {播放设备：<player>}{" · "<product>} {设备地址：<ip_address>}"whereareyou!"
</episode>
<track>
{art} {themoviedb_url} ⏹️{track_name}" @"{user}{"  "⭐️<rating>} music {stream_time} {progress_percent} {ip_address} {library_name}{" · "<track_artist>}{" · "<album_name>}{" · "<duration>分钟} {transcode_decision}" ⤷ "{quality_profile}{" · "<stream_video_dynamic_range>} "progress! "{<progress_percent>%} {停止时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} 播放时长：watchtime! 播放进度：{progress_time}({progress_percent}%){"  "剩余<remaining_duration>分钟} {文件大小：<file_size>} {首映日期：<air_date>} {播放设备：<player>}{" · "<product>} {设备地址：<ip_address>}"whereareyou!"
</track>
```

**影片入库通知**  
关于剧集入库: `<show>` 多季入库，  `<season>` 单季多集入库，  `<episode>` 单季单集入库
```console
<movie>
{art} {themoviedb_url} 🍿入库:" "{title}{"  "⭐️<rating>} {bitrate} 0:0:0 0 "10.0.0.1" {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} "··········································" {入库时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} {文件大小：<file_size>} {首映日期：<air_date>} {主要演员：<actors:[:2]>} {剧情简介：<summary>}
</movie>
<show>
{art} {themoviedb_url} 📺入库:" "{show_name}{" "S<season_num00>}{·E<episode_num00>}{"  "⭐️<rating>} 0 0:0:0 0 "10.0.0.1" {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} "··········································" {入库时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} {文件大小：<file_size>} {首映日期：<air_date>} {主要演员：<actors:[:2]>} {剧情简介：<summary>}
</show>
<season>
{art} {themoviedb_url} 📺入库:" "{show_name}{" "S<season_num00>}{·E<episode_num00>}{"  "⭐️<rating>} 0 0:0:0 0 "10.0.0.1" {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟/集} "··········································" {入库时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} {文件大小：<file_size>} {首映日期：<air_date>} {主要演员：<actors:[:2]>} {剧情简介：<summary>}
</season>
<episode>
{art} {themoviedb_url} 📺入库:" "{show_name}{" "S<season_num00>}{·E<episode_num00>}{"  "⭐️<rating>} {bitrate} 0:0:0 0 "10.0.0.1" {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} "··········································" {入库时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} {单集标题：<episode_name>} {文件大小：<file_size>} {首映日期：<air_date>} {主要演员：<actors:[:2]>} {剧情简介：<summary>}
</episode>
```

**播放错误通知**
```console
<movie>
{art} {themoviedb_url} ⚠️{title}" 播放错误‼️ @"{user} {bitrate} 0:0:0 {progress_percent} {ip_address} {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} {transcode_decision}" ⤷ "{quality_profile}{" · "<stream_video_dynamic_range>} "progress! "{<progress_percent>%} {播放时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} 观看进度：{progress_time}({progress_percent}%){"  "剩余<remaining_duration>分钟} {文件大小：<file_size>} {首映日期：<air_date>} {播放设备：<player>}{" · "<product>} {设备地址：<ip_address>}"whereareyou!"
</movie>
<episode>
{art} {themoviedb_url} ⚠️{show_name}" "S{season_num00}·E{episode_num00}" 播放错误‼️ @"{user} {bitrate} 0:0:0 {progress_percent} {ip_address} {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} {transcode_decision}" ⤷ "{quality_profile}{" · "<stream_video_dynamic_range>} "progress! "{<progress_percent>%} {播放时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} 观看进度：{progress_time}({progress_percent}%){"  "剩余<remaining_duration>分钟} {单集标题：<episode_name>} {文件大小：<file_size>} {首映日期：<air_date>} {播放设备：<player>}{" · "<product>} {设备地址：<ip_address>}"whereareyou!"
</episode>
```

**Plex 有更新通知**
```console
"picurl_plex_update!" {update_url} PLEX" "服务器更新啦" "💬 0 0:0:0 0 "10.0.0.1" {检测时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} {当前平台：<server_platform>} {当前版本：<server_version>} {最新版本：<update_version>} {发布时间：<update_release_date>} {●" "<update_changelog_added>} {●" "<update_changelog_fixed>}
```


**Plex 无法连接通知**
```console
"picurl_plex_server_down!" {update_url} ⚠️PLEX" "服务器无法连接‼️ 0 0:0:0 0 "10.0.0.1" {触发时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp}
```

**Tautulli 数据库损坏通知**
```console
"picurl_tautulli_database_corruption!" {update_url} ⚠️Tautulli" "数据库损坏‼️ 0 0:0:0 0 "10.0.0.1" {触发时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp}
```

**Tautulli 有更新通知**
```console
"picurl_tautulli_update!" {tautulli_update_release_url} Tautulli" "更新啦" "💬 0 0:0:0 0 "10.0.0.1" {检测时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} {当前版本：<tautulli_version>} {最新版本：<tautulli_update_version>} {●" "<tautulli_update_changelog>}
```

# 如果觉得好用的话可以请我喝杯咖啡
<img width="188" alt="image" src="https://user-images.githubusercontent.com/68833595/233236971-e59d4eef-b0af-49ea-9ad7-8c4ce479c623.png">
