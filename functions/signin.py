import json
import time

from graia.application import MessageChain
from graia.application.message.elements.internal import At, Plain

from function import ucf, get_timestamp_now, get_timestamp_today_start, get_timestamp_today_end
import os

if os.path.isfile('config.json'):
    with open('config.json', 'r', encoding='utf-8')as cfg_file:
        cfg = json.load(cfg_file)
else:
    cfg = {"BUY_PAN_INTERVAL": 3600, "SIGNIN_PAN": 5, "BUY_PAN_MIN": 1, "BUY_PAN_MAX": 10, "EAT_PAN_AMOUNT": 1}


async def user_signin(qq: int) -> MessageChain:
    """
    签到操作.

    :param qq: 用户QQ号
    :return: 返回的签到信息.
    """
    data = ucf.find_one({"qq": qq}, {"_id": 0})
    if not bool(data):
        data = {"qq": qq}

    signin_time = data.get('time') if data.get('time') else 0
    user_own_pan = data.get('pan') if data.get('pan') else 0
    sum_day = data.get('sum_day') if data.get('sum_day') else 0

    if signin_time == 0 or sum_day == 0:
        signin_time = get_timestamp_now()
        user_own_pan += cfg['SIGNIN_PAN']
        sum_day += 1
        data['time'] = signin_time
        data['pan'] = user_own_pan
        data['sum_day'] = sum_day
        str_time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(signin_time))
        res = ucf.update_one({"qq": qq}, {"$set": data})
        if res.modified_count == 0:
            ucf.insert_one(data)
        return MessageChain.create([
            At(target=qq),
            Plain(f"\n{str_time_now} \n初次签到成功！~\n摩卡给你{cfg['SIGNIN_PAN']}个面包哦~\n你现在有{user_own_pan}个面包啦~")
        ])

    if get_timestamp_today_start() < signin_time < get_timestamp_today_end():
        str_signin_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(signin_time))
        return MessageChain.create([
            At(target=qq),
            Plain(f"\n你已经在今天的{str_signin_time}已经签过到了哦~\n你现在有{user_own_pan}个面包哦~")
        ])

    signin_time = get_timestamp_now()
    user_own_pan += cfg['SIGNIN_PAN']
    sum_day += 1
    data['time'] = signin_time
    data['pan'] = user_own_pan
    data['sum_day'] = sum_day
    str_time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(signin_time))
    ucf.update_one({"qq": qq}, {"$set": data})
    return MessageChain.create([
        At(target=qq),
        Plain(f"\n{str_time_now} 签到成功，摩卡给你{cfg['SIGNIN_PAN']}个面包哦~\n"
              f"累计签到{sum_day}天\n你现在有{user_own_pan}个面包啦~")
    ])
