# 💌 TrueNAS 系统通知
- MR插件，获取 TrueNAS Scale 系统通知并推送到 MR 指定的通知通道（微信效果最佳）
- 通过 websocket 实时获取通知
- 如果没有安装MR，可以使用本项目上一级目录的通用脚本，该脚本是通过 API 轮询的方式获取，有兴趣的朋友可以基于此插件修改为 WS 的方式


## 效果预览
![truenas通知预览](https://user-images.githubusercontent.com/68833595/226232441-5b4c63b1-9220-4a41-8df9-72ca94865814.png)


## 使用说明
- 将 `truenas_notify` 文件夹放到 `Plugins` 文件夹或直接在 MR 插件市场下载自动安装，`设置好推送人保存后重启MR`，配置才会生效。
- 选择独立的微信通道时需先在设置中添加额外的微信通道（见下方设置独立微信应用通知）。

## 关于如何设置独立微信应用通知（和 MR 通知分开）
- 设置好额外的微信应用参数，接收人到插件设置页选择。
- 插件设置页选择新添加的额外微信应用通道

![image](https://user-images.githubusercontent.com/68833595/218243351-50e2a395-fde0-4910-b42f-bea311c4fb28.png)

## 为获得更好的效果体验，推送通道选择企业微信最好，配在 MR 系统中
- 配置路径：`应用设置` - `推送通道` 
- 在用户管理页为接收用户绑定 `微信账号`
- 如果这些参数你不知道怎么获取，可参见 [企业微信参数获取方法](https://alanoo.notion.site/thumb_media_id-64f170f7dcd14202ac5abd6d0e5031fb)
# 如果觉得好用的话可以请我喝杯咖啡
<img width="188" alt="image" src="https://user-images.githubusercontent.com/68833595/233236971-e59d4eef-b0af-49ea-9ad7-8c4ce479c623.png">
