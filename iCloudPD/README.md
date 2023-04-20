# iCloudPD 通知设置
依托的 docker镜像为：[boredazfcuk/icloudpd](https://hub.docker.com/r/boredazfcuk/icloudpd)   
对 iCloud 图库定时同步到本地各状态监控通知，以及简要同步日志提醒（点击通知卡片查看）。  

`media_id_images`文件夹内的4个GIF图片（ _不要改后缀_ ）需要传到企业微信素材库，如果你想要展示自己的头像，可以使用`头像镂空`文件夹内的图自行加上自己的头像。
详见 [media_id获取方法](https://alanoo.notion.site/thumb_media_id-64f170f7dcd14202ac5abd6d0e5031fb) 
# 效果预览
同步状态通知
<div align=center><img src="https://user-images.githubusercontent.com/68833595/192769304-c433d861-2bca-4873-b075-3176e71f3108.png" width="1000" /></div>

简要日志  
<div align=center><img src="https://user-images.githubusercontent.com/68833595/192768687-d5ad10fc-3382-4a0d-86ff-77f820804fc5.png" width="334" /></div>

# 环境变量配置
>iCloudPD 其他环境变量设置此处省略，只列出通知环境变量。

`notification_type` 通知类型设置为 `WeCom`

`wecom_proxy` 微信白名单域名设置，格式：https://abc.com

`wecom_id` 企业微信通知，企业微信通知，企业ID 

`wecom_secret` 企业微信通知，企业应用的Secret 

`agentid` 企业微信通知，企业应用的id

`touser` 企业微信通知，接收通知的对象

`content_source_url` 企业微信通知，阅读原文跳转链接

`name` 企业微信通知，当前 Apple ID 所有人

`media_id_startup` 企业微信通知，启动成功通知封面

`media_id_download` 企业微信通知，下载通知封面

`media_id_delete` 企业微信通知，删除文件通知封面

`media_id_expiration` 企业微信通知，cookie即将过期通知封面

`media_id_warning` 企业微信通知，同步失败、cookiey已过期通知封面

# 如果觉得好用的话可以请我喝杯咖啡
<img width="188" alt="image" src="https://user-images.githubusercontent.com/68833595/233236971-e59d4eef-b0af-49ea-9ad7-8c4ce479c623.png">
