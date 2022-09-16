# iCloudPD 通知设置
依托的 docker镜像为：[boredazfcuk/icloudpd](https://hub.docker.com/r/boredazfcuk/icloudpd)   
对 iCloud 图库同步状态监控通知，以及简要同步日志提示。  
`media_id_images`文件夹内的4个GIF图片（ _不要改后缀_ ）需要传到企业微信素材库，详见 [media_id获取方法](https://note.youdao.com/ynoteshare/index.html?id=351e08a72378206f9dd64d2281e9b83b&type=note&_time=1663295003299) ,看图片ID获取部分就行，其他的不用关注。
# 效果预览
空了补充
# 变量设置

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
