import requests
from bs4 import BeautifulSoup


def get_announcement():
    notice_title_selector = 'td.text > div > a'
    notice_content_selector = 'td.text > div > div'
    url = 'https://kp.m-team.cc/index.php'
    cookie = ''
    headers = {
        'cookie': cookie,
    }
    response = requests.request("GET", url, headers=headers, timeout=30).text
    soup = BeautifulSoup(response, 'html.parser')
    announcement_title = soup.select(notice_title_selector)
    announcement_content = soup.select(notice_content_selector)
    caption = f'最新公告:\n标题: {announcement_title[0].text.strip()}\n内容: {announcement_content[0].text.strip()}'
    print(caption)
    return caption