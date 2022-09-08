# Plex 企业微信通知
plex企业微信通知，基于 tautulli 通知规则编写 ，需要配合 tautulli 可正常使用。

可通过微信接收 Plex 服务器的`影片入库` `播放` `报错` 等通知，展示当前播放方式，谁在播放，播放进度等以及一些影片的基本信息。

## 效果预览
<div align=center><img src="https://github.com/Alano-i/wecom-notification/blob/main/Plex/plex%E9%80%9A%E7%9F%A5%E9%A2%84%E8%A7%88.png" width="800" /></div>

## 使用方法
- 将`wxapp_nofity.py` 和`config.yml`文件放入 tautulli 的/config/script/目录下，`wxapp_nofity.py`不需要改动，在`config.yml`中填入自己的配置
- Tautulli 需要添加 yaml 支持(进入tautulli命令行，执行 `pip3 install pyyaml`)
- Tautulli 新建通知-类型选-script
- 选择 `wxapp_nofity.py`
- 填入下方通知代码
- 保存即可

#### 需要填入 tautulli 中的通知代码

播放通知
```
<movie>
{art} {themoviedb_url} ▶️{title}" @"{user}{"  "⭐️<rating>} {bitrate} 0:0:0 {progress_percent} {ip_address} {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} {transcode_decision}" ⤷ "{quality_profile}{" · "<stream_video_dynamic_range>} "progress! "{<progress_percent>%} {播放时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} 观看进度：{progress_time}({progress_percent}%){"  "剩余<remaining_duration>分钟} {文件大小：<file_size>} {首映日期：<air_date>} {播放设备：<player>}{" · "<product>} {设备地址：<ip_address>}"whereareyou!"
</movie>
<episode>
{art} {themoviedb_url} ▶️{show_name}" "S{season_num00}·E{episode_num00}" @"{user}{"  "⭐️<rating>} {bitrate} 0:0:0 {progress_percent} {ip_address} {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} {transcode_decision}" ⤷ "{quality_profile}{" · "<stream_video_dynamic_range>} "progress! "{<progress_percent>%} {播放时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} 观看进度：{progress_time}({progress_percent}%){"  "剩余<remaining_duration>分钟} {单集标题：<episode_name>} {文件大小：<file_size>} {首映日期：<air_date>} {播放设备：<player>}{" · "<product>} {设备地址：<ip_address>}"whereareyou!"
</episode>
```

继续播放通知
```
<movie>
{art} {themoviedb_url} ▶️{title}" @"{user}{"  "⭐️<rating>} {bitrate} 0:0:0 {progress_percent} {ip_address} {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} {transcode_decision}" ⤷ "{quality_profile}{" · "<stream_video_dynamic_range>} "progress! "{<progress_percent>%} {继续时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} 观看进度：{progress_time}({progress_percent}%){"  "剩余<remaining_duration>分钟} {文件大小：<file_size>}"  "{video_codec!u}" ⤷ "{stream_video_codec!u} {首映日期：<air_date>} {播放设备：<player>}{" · "<product>} {设备地址：<ip_address>}"whereareyou!"
</movie>
<episode>
{art} {themoviedb_url} ▶️{show_name}" "S{season_num00}·E{episode_num00}" @"{user}{"  "⭐️<rating>} {bitrate} 0:0:0 {progress_percent} {ip_address} {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} {transcode_decision}" ⤷ "{quality_profile}{" · "<stream_video_dynamic_range>} "progress! "{<progress_percent>%} {继续时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} 观看进度：{progress_time}({progress_percent}%){"  "剩余<remaining_duration>分钟} {单集标题：<episode_name>} {文件大小：<file_size>}"  "{video_codec!u}" ⤷ "{stream_video_codec!u} {首映日期：<air_date>} {播放设备：<player>}{" · "<product>} {设备地址：<ip_address>}"whereareyou!"
</episode>
```

停止播放通知
```
<movie>
{art} {themoviedb_url} ⏹{title}" @"{user}{"  "⭐️<rating>} {bitrate} {stream_time} {progress_percent} {ip_address} {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} {transcode_decision}" ⤷ "{quality_profile}{" · "<stream_video_dynamic_range>} "progress! "{<progress_percent>%} {停止时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} 观看时长：watchtime! 观看进度：{progress_time}({progress_percent}%){"  "剩余<remaining_duration>分钟} {文件大小：<file_size>} {首映日期：<air_date>} {播放设备：<player>}{" · "<product>} {设备地址：<ip_address>}"whereareyou!"
</movie>
<episode>
{art} {themoviedb_url} ⏹{show_name}" "S{season_num00}·E{episode_num00}" @"{user}{"  "⭐️<rating>} {bitrate} {stream_time} {progress_percent} {ip_address} {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} {transcode_decision}" ⤷ "{quality_profile}{" · "<stream_video_dynamic_range>} "progress! "{<progress_percent>%} {停止时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} 观看时长：watchtime! 观看进度：{progress_time}({progress_percent}%){"  "剩余<remaining_duration>分钟} {单集标题：<episode_name>} {文件大小：<file_size>} {首映日期：<air_date>} {播放设备：<player>}{" · "<product>} {设备地址：<ip_address>}"whereareyou!"
</episode>
```

影片入库通知
```
<movie>
{art} {themoviedb_url} 🍿入库：{title}{"  "⭐️<rating>} {bitrate} 0:0:0 {progress_percent} "10.0.0.1" {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} "··········································" {入库时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} {文件大小：<file_size>} {首映日期：<air_date>} {主要演员：<actors:[:2]>} {剧情简介：<summary>}
</movie>
<show>
{art} {themoviedb_url} 📺入库：{show_name}{"  "⭐️<rating>} {bitrate} 0:0:0 {progress_percent} "10.0.0.1" {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} "··········································" {入库时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} {文件大小：<file_size>} {首映日期：<air_date>} {主要演员：<actors:[:2]>} {剧情简介：<summary>}
</show>
<season>
{art} {themoviedb_url} 📺入库：{show_name}" "S{season_num00}{"  "⭐️<rating>} {bitrate} 0:0:0 {progress_percent} "10.0.0.1" {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} "··········································" {入库时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} {文件大小：<file_size>} {首映日期：<air_date>} {主要演员：<actors:[:2]>} {剧情简介：<summary>}
</season>
<episode>
{art} {themoviedb_url} 📺入库：{show_name}" "S{season_num00}·E{episode_num00}{"  "⭐️<rating>} {bitrate} 0:0:0 {progress_percent} "10.0.0.1" {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} "··········································" {入库时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} {单集标题：<episode_name>} {文件大小：<file_size>} {首映日期：<air_date>} {主要演员：<actors:[:2]>} {剧情简介：<summary>}
</episode>
```

播放错误通知
```
<movie>
{art} {themoviedb_url} ⚠️{title}" 播放错误‼️ @"{user} {bitrate} 0:0:0 {progress_percent} {ip_address} {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} {transcode_decision}" ⤷ "{quality_profile}{" · "<stream_video_dynamic_range>} "progress! "{<progress_percent>%} {播放时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} 观看进度：{progress_time}({progress_percent}%){"  "剩余<remaining_duration>分钟} {文件大小：<file_size>} {首映日期：<air_date>} {播放设备：<player>}{" · "<product>} {设备地址：<ip_address>}"whereareyou!"
</movie>
<episode>
{art} {themoviedb_url} ⚠️{show_name}" "S{season_num00}·E{episode_num00}" 播放错误‼️ @"{user} {bitrate} 0:0:0 {progress_percent} {ip_address} {library_name}{" · "<video_resolution>}" · bitrate!"{" · "<video_dynamic_range>}{" · "<duration>分钟} {transcode_decision}" ⤷ "{quality_profile}{" · "<stream_video_dynamic_range>} "progress! "{<progress_percent>%} {播放时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} 观看进度：{progress_time}({progress_percent}%){"  "剩余<remaining_duration>分钟} {单集标题：<episode_name>} {文件大小：<file_size>} {首映日期：<air_date>} {播放设备：<player>}{" · "<product>} {设备地址：<ip_address>}"whereareyou!"
</episode>
```

plex 有更新通知
```
"picurl_plex_update!" {update_url} 🆕PLEX" "服务器更新可用🚀 0 0:0:0 0 "10.0.0.1" {检测时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} {当前平台：<server_platform>} {当前版本：<server_version>} {最新版本：<update_version>} {发布时间：<update_release_date>} {新增日志：<update_changelog_added>} {修复日志：<update_changelog_fixed>}
```


plex 无法连接通知
```
"picurl_plex_update!" {update_url} ⚠️PLEX" "服务器无法连接‼️ 0 0:0:0 0 "10.0.0.1" {触发时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp}
```

tautulli 数据库损坏通知
```
"picurl_plex_update!" {update_url} ⚠️PLEX" "服务器无法连接‼️ 0 0:0:0 0 "10.0.0.1" {触发时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp}
```

tautulli 有更新通知
```
"picurl_tautulli_update!" {tautulli_update_release_url} 🆕Tautulli" "更新可用🚀 0 0:0:0 0 "10.0.0.1" {检测时间：<datestamp>}"  "{周<current_weekday>}"  "{timestamp} {当前版本：<tautulli_version>} {最新版本：<tautulli_update_version>} {更新日志：<tautulli_update_changelog>}
```









