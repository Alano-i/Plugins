# 🌎 每天60秒读懂世界 - 微信推送
MR插件，定时获取每日新闻和天气并微信通知
- 【每日新闻】`每小时获取一次直到获取到最新每日新闻` 获取到并推送后当天不再获取。
- 【影视资讯】`每天8:00` 获取到并推送后当天不再获取。
- 推送通知时调用调用当天天气，背景根据天气变化
- 点击消息封面可进入详情页，查看完整新闻列表内容
- 点击阅读原文跳转到源出处

本人能力有限，各位可帮助一起完善提PR即可！



## 使用说明
- 将 `daily_news` 文件夹放到 `Plugins` 文件夹，`设置好推送人保存后一定要重启MR`，配置才会生效。
- 本插件选用微信通道推送消息效果最佳，若没获取到相关参数，将采用 MR 主干默认消息通道推送。
- 如采用默认消息通道推送。
- 重启后如果日志报错：依赖库 `zhdate` 安装失败而导致插件载入失败，请手动进入 MR 命令行安装，安装命令：`pip install zhdate`

## 关于如何设置独立微信应用通知（和 MR 通知分开）
<img width="796" alt="image" src="https://user-images.githubusercontent.com/68833595/218129187-ccb09a99-e72e-4b4e-9c18-a754e329c5e3.png">

- 填好下图红框中的三项即可，接收人到插件设置页选择
<img width="823" alt="image" src="https://user-images.githubusercontent.com/68833595/218130974-585c3d6c-3eed-4504-8bb1-9290dd0f1032.png">

- 插件设置页选择刚刚新添加的额外微信应用通道
<img width="1289" alt="image" src="https://user-images.githubusercontent.com/68833595/218128832-d5c7cb7b-5cef-4da4-af12-8394d31cfb64.png">



## 为获得更好的效果体验，需要配置企业微信参数，配在MR系统里，下面是配置方法
- 在设置-设置企业微信页设置：`agentid` `corpid` `corpsecret`
- 在用户管理页设置 `微信账号`
- 如果这些参数你不知道怎么获取，可参见 [企业微信参数获取方法](https://alanoo.notion.site/thumb_media_id-64f170f7dcd14202ac5abd6d0e5031fb)



## 效果预览
![git](https://user-images.githubusercontent.com/68833595/216874085-3f036cb1-861b-4153-a890-8c723fae478b.png)






