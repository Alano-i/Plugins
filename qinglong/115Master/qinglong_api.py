import json
import requests
import os
QL_URL = os.getenv('QL_URL')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

class QinglongApi:
    def __init__(self):
        if not QL_URL or not CLIENT_ID or not CLIENT_SECRET:
            raise Exception('请设置青龙环境变量 QL_URL, CLIENT_ID, CLIENT_SECRET')
        self.ql_url =  QL_URL
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.token = self.get_qinglong_token()
        self.envs = self.get_envs(self.token)

    # 获取青龙token
    def get_qinglong_token(self):
        url = f'{self.ql_url}/open/auth/token'
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        resp = requests.get(url=url, params=params)
        get_tk = json.loads(resp.text)['data']['token']
        return get_tk
    
    # 获取现有环境变量
    def get_envs(self,token):
        url = f'{self.ql_url}/open/envs'
        headers = {
            'Authorization': 'Bearer ' + token
        }
        resp = requests.get(url=url, headers=headers)
        envs = json.loads(resp.text)['data']
        return envs
    
    # 删除环境变量
    def delete_env(self, token, env_id):
        url = f'{self.ql_url}/open/envs'
        headers = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
        resp = requests.delete(url=url, headers=headers, json=[env_id])
        return resp.status_code == 200
    
    # 写入单个环境变量，如果环境变量已存在，会新增一个同名的环境变量
    def update_env(self, token, name, new_value, remarks):
        url = f'{self.ql_url}/open/envs'
        data = [{
            'name': name,         # 变量名
            'value': new_value,   # 变量值
            'remarks': remarks    # 备注
        }]
        headers = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
        resp = requests.post(url=url, headers=headers, json=data)
        return resp.status_code == 200
    
    # 批量添加环境变量（若环境变量已存在，则跳过添加）
    def add_env(self, new_envs):
        for new_env in new_envs:
            # 环境变量已存在，则跳过    
            if new_env['name'] in [env['name'] for env in self.envs]:
                print(f'环境变量【{new_env["name"]}】已存在，跳过添加\n')
                continue
            self.update_env(self.token, new_env['name'], new_env['value'], new_env['remarks'])
            print(f'环境变量【{new_env["name"]}】添加成功\n')

    # 批量更新环境变量（若环境变量已存在，则删除原环境变量重新添加）
    def update_envs(self, new_envs):
        for new_env in new_envs:
            remarks = None
            if new_env['name'] in [env['name'] for env in self.envs]:     # 环境变量已存在，删除原环境变量
                env_id = [env['id'] for env in self.envs if env['name'] == new_env['name']][0]
                print(f'环境变量【{new_env["name"]}】已存在，删除原环境变量,再重新添加')
                # 获取原环境变量的备注
                remarks = [env['remarks'] for env in self.envs if env['name'] == new_env['name']][0]
                self.delete_env(self.token, env_id)
            # 添加新环境变量，若原环境变量有备注，则使用原环境变量的备注
            self.update_env(self.token, new_env['name'], new_env['value'], remarks if remarks else new_env['remarks'])