#!/usr/bin/env python3
# encoding: utf-8

# 记录开始时间
import html
import json

from datetime import datetime

from component import *

def convert_bytes(bytes_value):
    if bytes_value >= 1024 ** 4:
        tb = bytes_value / (1024 ** 4)  # TB
        return f"{tb:.2f}TB"
    elif bytes_value >= 1024 ** 3:
        gb = bytes_value / (1024 ** 3)  # GB
        return f"{gb:.2f}GB"
    elif bytes_value >= 1024 ** 2:
        mb = bytes_value / (1024 ** 2)  # MB
        return f"{mb:.2f}MB"
    elif bytes_value >= 1024:
        kb = bytes_value / 1024  # KB
        return f"{kb:.2f}KB"
    elif bytes_value==0:
        return 0
    else:
        return f"{bytes_value} bytes"

def convert_time(elapsed_time):
    # 检查是否包含天数
    if 'day' in elapsed_time:
        days, time_part = elapsed_time.split('day,')
        days = int(days.strip())
    else:
        days = 0
        time_part = elapsed_time

    # 解析时间字符串
    hours, minutes, seconds = map(float, time_part.split(':'))
    total_seconds = days * 86400 + hours * 3600 + minutes * 60 + seconds + 1
    running_time = total_seconds

    if total_seconds < 60:
        running_time = f"{int(total_seconds)} 秒"
    elif total_seconds < 3600:
        minutes, seconds = divmod(total_seconds, 60)
        running_time = f"{int(minutes)} 分钟 {int(seconds)} 秒"
    elif total_seconds < 86400:
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        running_time = f"{int(hours)} 小时 {int(minutes)} 分钟 {int(seconds)} 秒"
    else:
        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        running_time = f"{int(days)} 天 {int(hours)} 小时 {int(minutes)} 分钟 {int(seconds)} 秒"

    running_time = running_time.replace(" 0 分钟", "").replace(" 0 小时", "").replace(" 0 秒", "")
    return running_time

# 转换字典中的所有 datetime 对象为不带微秒的字符串
def convert_datetime_in_dict(d):
    for key, value in d.items():
        if isinstance(value, datetime):
            d[key] = value.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(value, dict):
            convert_datetime_in_dict(value)
    return d

# 定义你的高亮样式
highlight_styles = {
    "string": "color:#ce9178;",
    "number": "color:#b5cea8;",
    "boolean": "color:#569cd6;",
    "null": "color:#569cd6;",
    "key": "color:#9cdcfe;",
    "braces": "color:#ffd700;",
    "brackets": "color:#d76fd3;",
}

def json_to_html(json_obj, indent=0):
    html_code = []
    indent_space = "  " * indent
    if isinstance(json_obj, dict):
        html_code.append(f'{indent_space}<span style="{highlight_styles["braces"]}">{{</span>\n')
        for key, value in json_obj.items():
            html_code.append(f'{indent_space}  <span style="{highlight_styles["key"]}">"{html.escape(str(key))}"</span>: {json_to_html(value, indent + 1)},\n')
        html_code[-1] = html_code[-1].rstrip(',\n') + '\n'
        html_code.append(f'{indent_space}<span style="{highlight_styles["braces"]}">}}</span>\n')
    elif isinstance(json_obj, list):
        html_code.append(f'{indent_space}<span style="{highlight_styles["brackets"]}">[</span>\n')
        for item in json_obj:
            html_code.append(f'{indent_space}  {json_to_html(item, indent + 1)},\n')
        html_code[-1] = html_code[-1].rstrip(',\n') + '\n'
        html_code.append(f'{indent_space}<span style="{highlight_styles["brackets"]}">]</span>\n')
    elif isinstance(json_obj, str):
        html_code.append(f'<span style="{highlight_styles["string"]}">"{html.escape(json_obj)}"</span>')
    elif isinstance(json_obj, (int, float)):
        html_code.append(f'<span style="{highlight_styles["number"]}">{html.escape(str(json_obj))}</span>')
    elif isinstance(json_obj, bool):
        html_code.append(f'<span style="{highlight_styles["boolean"]}">{"true" if json_obj else "false"}</span>')
    elif json_obj is None:
        html_code.append(f'<span style="{highlight_styles["null"]}">null</span>')
    return ''.join(html_code)
    


def push_msg(stats,all_tasks):
    # 删除 src_attr 和 dst_attr
    stats.pop('src_attr', None)
    stats.pop('dst_attr', None)
    stats = convert_datetime_in_dict(stats)

    print(f"stats:{stats}")

    failed_tasks = all_tasks.get('failed', {})
    
    print(f"failed_tasks:{failed_tasks}")

    # 统计脚本运行时间
    running_time = convert_time(stats['elapsed'])   # 0:00:01.718300/1 day, 10:27:16.584357

    print(f"\n\n拉取耗时：{running_time}\n")

    # stats ={'tasks': {'total': 51404, 'files': 41197, 'dirs': 10207}, 'unfinished': {'total': 2, 'files': 2, 'dirs': 0}, 'success': {'total': 51401, 'files': 41194, 'dirs': 10207}, 'failed': {'total': 1, 'files': 1, 'dirs': 0}, 'errors': {'total': 119, 'files': 102, 'dirs': 17, 'reasons': {'urllib.error.URLError': 109, 'urllib.error.HTTPError': 9, 'httpx.RemoteProtocolError': 1}}, 'is_completed': False}
    success_files = stats['success']['files']
    success_dirs = stats['success']['dirs']
    total_success_size = convert_bytes(stats['success']['size'])
    total_size = convert_bytes(stats['tasks']['size'])

    failed_files = stats['failed']['files']
    failed_dirs = stats['failed']['dirs']
    total_failed_size = convert_bytes(stats['failed']['size'])


    # 发送通知
    table_template = f"""
    <div style="border: 1px solid #f1f1f1; font-size: 14px">
    <table style="border-collapse: collapse; width: 100%;">
    <tr style="background-color: #f1f1f1;">
        <th style="border-bottom: 1px solid #e8e8e8; padding: 8px; text-align: center;">类型</th>
        <th style="border-bottom: 1px solid #e8e8e8; padding: 8px; text-align: center;">文件</th>
        <th style="border-bottom: 1px solid #e8e8e8; padding: 8px; text-align: center;">文件夹</th>
        <th style="border-bottom: 1px solid #e8e8e8; padding: 8px; text-align: center;">大小</th>
    </tr>
    <tr>
        <td style="border-bottom: 1px solid #f1f1f1; padding: 8px; text-align: center;">🕓 任务</td>
        <td style="border-bottom: 1px solid #f1f1f1; padding: 8px; text-align: center;">{stats['tasks']['files']}</td>
        <td style="border-bottom: 1px solid #f1f1f1; padding: 8px; text-align: center;">{stats['tasks']['dirs']}</td>
        <td style="border-bottom: 1px solid #f1f1f1; padding: 8px; text-align: center;">{total_size}</td>
    </tr>
    <tr>
        <td style="border-bottom: 1px solid #f1f1f1; padding: 8px; text-align: center;">✅ 成功</td>
        <td style="border-bottom: 1px solid #f1f1f1; padding: 8px; text-align: center;">{success_files}</td>
        <td style="border-bottom: 1px solid #f1f1f1; padding: 8px; text-align: center;">{success_dirs}</td>
        <td style="border-bottom: 1px solid #f1f1f1; padding: 8px; text-align: center;">{total_success_size}</td>
    </tr>
    <tr>
        <td style="border-bottom: 1px solid #f1f1f1; padding: 8px; text-align: center;">⭕️ 失败</td>
        <td style="border-bottom: 1px solid #f1f1f1; padding: 8px; text-align: center;">{failed_files}</td>
        <td style="border-bottom: 1px solid #f1f1f1; padding: 8px; text-align: center;">{failed_dirs}</td>
        <td style="border-bottom: 1px solid #f1f1f1; padding: 8px; text-align: center;">{total_failed_size}</td>
    </tr>
    <tr>
        <td style="padding: 8px; text-align: center;">❌ 错误</td>
        <td style="padding: 8px; text-align: center;">{stats['errors']['files']}</td>
        <td style="padding: 8px; text-align: center;">{stats['errors']['dirs']}</td>
        <td style="padding: 8px; text-align: center;"></td>
    </tr>
    </table>
    </div>
    """

    stats_content = f"""
    <pre style="background-color:#1e1e1e;color:#d4d4d4;padding:10px;border-radius:4px;font-size:11px;line-height:2;">
    <code style="color:#d4d4d4;font-family:Menlo, Monaco, Consolas, 'Courier New', monospace;">
    {json_to_html(stats).strip()}
    </code>
    </pre>
    """


    if push_notify:
        if failed_files or failed_dirs:
            message = f"✅ 文　件：{success_files} 个\n✅ 文件夹：{success_dirs} 个\n📦 大　小：{total_success_size} / {total_size}\n\n❌ 文　件：{failed_files} 个\n❌ 文件夹：{failed_dirs} 个\n\n共耗时 {running_time}"
        else:
            message = f"✅ 文　件：{success_files} 个\n✅ 文件夹：{success_dirs} 个\n📦 大　小：{total_success_size}\n\n全部拉取成功，耗时 {running_time}"  
        msg=message.replace("\n", "<br/>")

        if failed_tasks:
            content = f"部分拉取完成，耗时 {running_time}<br><br>{table_template}<br>{stats_content}<pre style='line-height:1.5; font-size:12px'><code>{failed_tasks}</code></pre>" 
        else:
            content = f"全部拉取成功，耗时 {running_time}<br><br>{table_template}<br>{stats_content}" 

        wecom_notify.send_mpnews(title="115拉取完成", message=message, media_id=media_id, touser=touser, content=content)