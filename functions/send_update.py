import json
import os
import time

import pymongo
import redis
import requests

client = pymongo.MongoClient(host='localhost', port=27017)

db1 = client['moca']
gkw = db1['group_keyword']
r = redis.Redis(db=3, decode_responses=True)

serverAddr = "http://127.0.0.1:8080/"
authData = {'authKey': 'INITKEYCYfJBNVe'}
verifyData = {'qq': 1400625889}
groupMessageUrl = serverAddr + 'sendGroupMessage'
releaseSession = serverAddr + 'release'
getGroupsListUrl = serverAddr + 'groupList?sessionKey='

sessionKey = ""

with open('../config.json', 'r', encoding='utf-8')as cfg:
    config: dict = json.load(cfg)

group_list = []


def mirai_auth():
    """
    功能：mirai认证
    参数：无
    返回：sessionKey，错误时返回错误码
    """
    global sessionKey
    about_data = json.loads(requests.get(serverAddr + "about").text)
    print("MiraiAPIHTTP Version:", about_data['data']['version'])

    r_auth_json = requests.post(serverAddr + "auth", json.dumps(authData))
    r_auth_json = json.loads(r_auth_json.text)
    print("Auth Session, Return Code:", r_auth_json['code'])
    verifyData['sessionKey'] = r_auth_json.get('session')

    r_verify_json = requests.post(serverAddr + "verify", json.dumps(verifyData))
    r_verify_json = json.loads(r_verify_json.text)
    if not r_verify_json.get('code') == 0:
        print(f'返回错误，错误代码：{r_verify_json.get("code")}')
        return r_verify_json.get('code')

    print(f'收到sessionKey: {r_auth_json.get("session")}')
    sessionKey = r_auth_json['session']
    return r_auth_json['session']


def mirai_close_session():
    """
    关闭mirai session
    """
    global sessionKey
    _data = {'sessionKey': sessionKey, 'qq': verifyData['qq']}
    res = requests.post(url=releaseSession, data=json.dumps(_data))
    r_json = json.loads(res.text)
    print("Close Session:", r_json['msg'])


def mirai_reply_image(target_id, path=''):
    """
    回复图片.
    :param: target_id: 群号
    :param: path: 图片相对于 %MiraiPath%/plugins/MiraiAPIHTTP/images/
    }
    :return: 正常时返回msg(success)，参数错误时返回"error_invalid_parameter"
    """
    global sessionKey
    if not target_id == '' and not sessionKey == '':
        data_dict = {"sessionKey": sessionKey, "target": target_id, "messageChain": [{"type": "Image", "path": path}]}
        if path == '':
            return
        print(f'Sending Picture to {target_id}')
        final_data = json.dumps(data_dict)
        res = requests.post(url=groupMessageUrl, data=final_data)
        r_json = json.loads(res.text)

        return r_json.get('msg')
    else:
        return 'error_invalid_parameter'


def mirai_get_all_groups():
    global sessionKey, group_list
    _data = {'sessionKey': sessionKey}
    print(_data)

    res = requests.get(url=getGroupsListUrl + sessionKey)
    group_list = json.loads(res.text)
    print(group_list)


if __name__ == "__main__":
    mirai_auth()
    cache_dir = os.path.join(config.get('resource_path'), 'cache')
    if not os.path.isdir(cache_dir):
        os.makedirs(os.path.join(config.get('resource_path'), 'cache'))
    mirai_get_all_groups()
    for item in group_list:
        print(item['id'], '-', item['name'], '-', item['permission'])
    mirai_close_session()

