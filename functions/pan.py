import random
import time

from graia.application import MessageChain
from graia.application.message.elements.internal import Plain, At

from function import ucf, get_timestamp_now, cfg_enabled, pl
from functions.fun_cfg import cfg

TWICE_LP_PAN_AMOUNT = 3


def pan_log(qq: int, amount: int, reason: str):
    """
    面包变化记录.

    :param qq: 用户QQ
    :param amount: 变化的数量(以正负区别增加、消耗)
    :param reason: 变化原因
    :return: 无
    """
    pl.insert_one({"time": get_timestamp_now(), "qq": qq, "pan": amount, "reason": reason})


def pan_change(qq: int, amount: int) -> list:
    """
    面包数量变化.

    :param qq: 用户QQ
    :param amount: 变化的数量(以正负区别增加、消耗)
    :return: [成功/失败(True/False), 变化后的数量，失败返回-1]
    """
    if amount > 0:
        res = ucf.update_one({"qq": qq}, {"$inc": {"pan": amount}})
        if res.modified_count == 0:
            ucf.insert_one({"qq": qq, "pan": amount})
            return [True, amount]
        else:
            new_pan_amount = ucf.find_one({"qq": qq}, {"pan": 1})
            return [True, new_pan_amount['pan']]
    else:
        user_data = ucf.find_one({"qq": qq}, {"_id": 0, "pan": 1})
        try:
            original_pan_amount = user_data['pan']
            if original_pan_amount + amount < 0:
                return [False, -1]
            else:
                ucf.update_one({"qq": qq}, {"$inc": {"pan": amount}})
                new_pan_amount = ucf.find_one({"qq": qq}, {"pan": 1})['pan']
                return [True, new_pan_amount]
        except TypeError:
            return [False, -1]
        except KeyError:
            return [False, -1]


async def buy_pan(qq: int) -> MessageChain:
    """
    买面包.

    :param qq: QQ号
    :return: 结果MessageChain
    """
    in_buy_cd = False
    data = ucf.find_one({"qq": qq}, {"_id": 0, "last_buy_time": 1, 'pan': 1})
    if not bool(data):
        data = {"qq": qq}

    last_buy_time = data.get('last_buy_time') if data.get('last_buy_time') else 0
    user_own_pan = data.get('pan') if data.get('pan') else 0
    time_interval = get_timestamp_now() - last_buy_time

    if time_interval < cfg.get('BUY_PAN_INTERVAL'):
        in_buy_cd = True

    if in_buy_cd:
        time_interval = last_buy_time + cfg.get('BUY_PAN_INTERVAL') - get_timestamp_now()
        if time_interval < 60:
            str_next_buy_time = f"{time_interval}秒"
        else:
            str_next_buy_time = f"{int(time_interval / 60)}分钟"
        return MessageChain.create([
            At(target=qq),
            Plain(f' 还不能购买呢~\n还要等{str_next_buy_time}才能再买哦~')
        ])

    buy_amount = random.randint(cfg.get('BUY_PAN_MIN'), cfg.get('BUY_PAN_MAX'))
    user_own_pan += buy_amount

    data['last_buy_time'] = get_timestamp_now()
    data['pan'] = user_own_pan
    res = ucf.update_one({"qq": qq}, {"$set": data})
    if res.modified_count == 0:
        ucf.insert_one(data)
    ucf.update_one({"qq": qq}, {"$inc": {'buy_count': 1}})
    pan_log(qq, buy_amount, "买面包")
    return MessageChain.create([
        At(target=qq),
        Plain(f' 成功购买了{buy_amount}个面包哦~\n你现在有{user_own_pan}个面包啦~')
    ])


async def eat_pan(qq: int) -> MessageChain:
    """
    吃~面~包~.

    :param qq: 用户qq
    :return: 结果MessageChain
    """
    res = pan_change(qq, -cfg.get('EAT_PAN_AMOUNT'))
    if not res[0]:
        return MessageChain.create([
            At(target=qq),
            Plain(' 面包不够吃了QAQ...')
        ])
    pan_log(qq, -cfg.get('EAT_PAN_AMOUNT'), "吃面包")
    return MessageChain.create([
            At(target=qq),
            Plain(f" 你吃掉了{cfg.get('EAT_PAN_AMOUNT')}个面包，还剩{res[1]}个面包哦~")
        ])


def twice_lp(group: int, member: int):
    """
    双倍lp

    :param group: 群号
    :param member: QQ号
    :return: [要发发送的图片数量，剩余面包数量]
    """
    if cfg_enabled(group, "pan"):
        result = pan_change(member, -TWICE_LP_PAN_AMOUNT)
        if result[0]:
            pan_log(member, -TWICE_LP_PAN_AMOUNT, "双倍lp")
            return [2, result[1]]
        else:
            return [1, result[1]]
    else:
        return [1, -1]
