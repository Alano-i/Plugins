import asyncio
import time
from pyppeteer import launch
import logging
logger = logging.getLogger(__name__)
plugins_name = "有声书工具箱"

xm_sign = ''
async def generate_xm_sign():
    # 启动浏览器
    browser = await launch(headless=True)  # headless=True 表示不显示浏览器界面
    page = await browser.newPage()
    
    # 加载本地 HTML 文件
    await page.goto('file:////data/plugins/audio_tools/xm_sign.html')  # 替换成你的本地文件路径
    
    # 等待 2 秒钟，以确保 JavaScript 执行完成
    await page.waitFor(4000)  # 增加等待时间，确保 JavaScript 执行

    for i in range(10):
        # 等待 xm_sign 元素出现
        # await page.waitForSelector('#xm_sign')
        # 获取页面中的 xm_sign 值
        xm_sign = await page.evaluate('document.getElementById("xm_sign") ? document.getElementById("xm_sign").value : ""')
        logger.info(f"{plugins_name}第 {i+1}/10 次获取到 xm_sign: {xm_sign}")
        time.sleep(3)
        if xm_sign:
            break
    # 关闭浏览器
    await browser.close()

    return xm_sign

# 运行异步函数
async def main():
    global xm_sign
    xm_sign = await generate_xm_sign()
    # print(f'xm_sign: {xm_sign}')
# 执行
def get_xm_sign():
    # asyncio.get_event_loop().run_until_complete(main())
    asyncio.run(main())  # 使用 asyncio.run() 来运行异步任务
    return xm_sign