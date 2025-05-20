import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
import logging
logger = logging.getLogger(__name__)
plugins_name = "有声书工具箱"

cookies = """_xmLog=h5&3c819b03-235f-49a4-bb4c-7852e06b0f17&process.env.sdkVersion; 1&remember_me=y; wfp=ACM0YmEzZjdjMmRmNTljODhhB5bvrqjoNc14bXdlYl93d3c; Hm_lvt_4a7d8ec50cfd6af753c4f8aee3425070=1731417010; HWWAFSESID=2d1101188cb6c820e2c; HWWAFSESTIME=1734528363238; DATE=1724579578293; crystal=U2FsdGVkX19FKt+YWvMl075HApapiyGcy0DeSWRe427IpdukBjQ8SLP4Jh/OgeIPknfinBlX3W2n2wWDBvW8gH6Za9Vlgd8Rk3V2xLlnozajQU1eMudEta97Gk0A1PVSZBcZTonxT1k7jgeWjCOzpcMcTkfliTx0SqqmvA0oxrm8RfKD4ZJgl5s80fH1dbCAzhgcVMlNaC677iWEv7cwN3tC8dCzAJIUbJ+/ucHQQ30mneAKGSTE3gcMxO7qvvJj; xm-page-viewid=ximalaya-web; impl=www.ximalaya.com.login; 1&_token=443903130&A206E440340N32E3494F3B1563D10BDFC7B422B5D9727FF3BD58DB523E6915953B6D93A2EF0981MD9911F4A6CEA92B_; 1_l_flag=443903130&A206E440340N32E3494F3B1563D10BDFC7B422B5D9727FF3BD58DB523E6915953B6D93A2EF0981MD9911F4A6CEA92B__2024-12-1821:26:12; login_type=password_mobile; vmce9xdq=U2FsdGVkX1+iYf6ZyMG7irSndCwNF3Kf9dc1e6S1UulJRUXvPlAK32rpBc0AmBSWmcjlxxIRM/QppHAP+w1OxnHjK6NhvTFqbgxQpC0CUuqCkcwYYNAeybIFIg1MMsQ8Q78Ersfmfx88dqDEP2edEvWDuZAREiRQ1XTIQtb+dYk=; cmci9xde=U2FsdGVkX1/S46NGwB+5s099iL2ku/oZat+1KLMVWreKMJ7yhdzhTN9D85kr/oysPiedeOWA6yOboV7NMnuvdw==; pmck9xge=U2FsdGVkX181Y3FAqWK48vvDlepKJZuODmNWBQvbfVQ=; assva6=U2FsdGVkX19JeYCoP5DImbA6ZaNsO01cmIGHJGNvxaY=; assva5=U2FsdGVkX1+ksCkbWtMCcV8eiTK/ZXO670sQwhFTs17OdjZh3YbJsRk51n6cFMVlbJqGucigQscmrDNIS8DuPQ==; web_login=1734629199342"""
cookie = dict([l.split("=", 1) for l in cookies.split("; ")])
# 转driver所需格式dict 键name和value是固定的
cookie_dict = list([{'name': k, 'value': v} for k,v in cookie.items()])

class captBrowser:
    def __init__(self):
        # self.chrome_driver = ExeUtils.get_resources(r"assets/chrome-linux64/chromedriver")  # 浏览器驱动
        self.chrome_driver = "/data/plugins/audio_tools/assets/chrome-linux64/chromedriver"  # 请替换为实际路径
        # self.chrome_app = ExeUtils.get_resources(r"assets/chrome-linux64/chrome")  # 浏览器
        # self.html_path = ExeUtils.get_resources(r'assets/xm_sign.html')
        self.html_path = "/data/plugins/audio_tools/assets/xm_sign.html"  # 请替换为实际路径
        self.test_url = "https://www.ximalaya.com"

        chrome_options = Options()
        chrome_options.add_argument('--disable-web-security')  # 启动时禁用同源策略
        chrome_options.add_argument("--headless")  # 无头模式
        chrome_options.add_argument("--disable-gpu")  # 禁用GPU加速
        chrome_options.add_argument("--no-sandbox")  # 提高兼容性，避免沙箱问题


        s = Service(self.chrome_driver)
        # chrome_options.binary_location = self.chrome_app  # 添加浏览器
        self.driver = webdriver.Chrome(service=s, options=chrome_options)
        # 获取 User-Agent
        # self.user_agent = self.driver.execute_script("return navigator.userAgent;")

    def open_test_url(self):
        logger.info(f"{plugins_name}打开测试页面: {self.test_url}")
        self.driver.get(self.test_url)  # 打开一个有效的 URL
        time.sleep(5) 

    def set_cookie(self):
        # 设置 Cookie
        for cook in cookie_dict:
            self.driver.add_cookie(cook)

    def open_url(self):
        logger.info(f"{plugins_name}打开本地HTML文件: {self.html_path}")
        # 打开本地HTML文件
        self.driver.get(f"file:///{self.html_path}")
        # 等待JavaScript加载完成
        time.sleep(5)  # 等待页面加载和JavaScript执行

    def get_xm_sign(self):
        user_agent = self.driver.execute_script("return navigator.userAgent;")
        xm_sign_value=''
        for i in range(10):
            # 获取页面中的 xm_sign 输入框的值
            try:
                xm_sign_value = self.driver.find_element(By.ID, "xm_sign").get_attribute("value")
            except Exception as e:
                logger.error(f"{plugins_name}第 {i+1}/10 次获取 xm_sign 失败: {e}")
            logger.info(f"{plugins_name}第 {i+1}/10 次获取到 xm_sign: {xm_sign_value}")
            if xm_sign_value:
                break
            else:
                time.sleep(3)  # 等待3秒
        # user_agent='MicroMessenger Client'
        return xm_sign_value,user_agent


# 示例用法
def get_xm_sign():
    br = captBrowser()
    # br.open_test_url()
    # br.set_cookie()
    br.open_url()
    xm_sign,user_agent = br.get_xm_sign()  # 获取 xm_sign 的值
    logger.info(f"{plugins_name}获取到 user_agent: {user_agent}")
    return xm_sign,user_agent
    # print(f"xm_sign: {xm_sign}")