from component import *
import datetime

client=clients[0]
fs=client.fs
del_success=False

def delete_item(id):
  global del_success
  while True:
      try:
          if datetime.datetime.now().second == 5:
            print(f"准备删除id为 {id} 的项目")
          time.sleep(1)
          res = client.fs_delete(id)
          if not res['state'] and res['errno'] == 990023:
              # 删除文件数量超过了上限，需要遍历子文件夹
              sub_items = fs.listdir_attr(id)
              for item in sub_items:
                  delete_item(item['id'])
              # 删除子文件夹内容后，再次尝试删除文件夹
              res = client.fs_delete(id)
              if not res['state']:
                  print(f"删除 {id} 时出错: {res}")
                  del_success=False
          if res['state']:
              del_success=True
              break
          elif res['errno'] == 990009:
              # 删除操作尚未执行完成，请稍后再试
              print(f"删除 {id} 时出错: {res}，将在5秒后重试...")
              del_success=False
              time.sleep(5)
          else:
              print(f"删除 {id} 时出错: {res}")
              del_success=False
              break
      except Exception as e:
          print(f"删除ID为 {id} 的项目时出错，原因：{e}")
          del_success=False
          break

def main():
  if del_root_id:
    delete_item(int(del_root_id))
  else:
    print('未设置文件/文件夾id')
    return

if __name__ == "__main__":
  main()
  print('执行完成')
  if push_notify:
    title = '✅ 115删除文件夹成功' if del_success else '⭕️ 115删除文件夹失败'
    wecom_notify.send_news(title=title, message=f"删除 [{del_root_id}] 任务执行完成", link_url="", pic_url=pic_url, touser=touser)