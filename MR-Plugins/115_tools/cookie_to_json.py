import json
def extract_cookie_dic(cookies):
    cookie_dic = {}
    pairs = cookies.replace(' ', '').split(';')
    for pair in pairs:
        if '=' in pair:
            key, value = pair.split('=')
            cookie_dic[key] = value
    return cookie_dic

def cookie_to_json(UID, CID, SEID):
    cookie_template = {
        "domain": ".115.com",
        "hostOnly": False,
        "httpOnly": True,
        "path": "/",
        "sameSite": "unspecified",
        "secure": False,
        "session": False,
        "storeId": "0",
        "id": 1
    }
    
    cookies = [
        {"name": "UID", "value": UID},
        {"name": "CID", "value": CID},
        {"name": "SEID", "value": SEID}
    ]
    
    cookie_json = []
    for index, cookie in enumerate(cookies, start=1):
        cookie_info = cookie_template.copy()
        cookie_info.update(cookie)
        cookie_info['id'] = index
        cookie_json.append(cookie_info)
    return cookie_json
def cookie2json(cookie_115):
    cookie_dic = extract_cookie_dic(cookie_115)
    cookie_json = cookie_to_json(cookie_dic.get('UID', None), cookie_dic.get('CID', None), cookie_dic.get('SEID', None))
    cookie_json = json.dumps(cookie_json, indent=2)
    return cookie_json
