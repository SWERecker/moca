import json
import os
import random
import time

import pymongo
import redis
from graia.application import MessageChain
from graia.application.message.elements.internal import Plain, Image
from pypinyin import lazy_pinyin
from PIL import Image as ImageLib
from PIL import ImageDraw, ImageFont
from prettytable import PrettyTable
import global_var as gol

if not os.path.isfile('config.py'):
    import config_template as config
else:
    import config

client = pymongo.MongoClient(host='localhost', port=27017)
db1 = client['moca']
gcf = db1['group_config']
ucf = db1['user_config']
gkw = db1['group_keyword']
gc = db1['group_count']

cache_pool = redis.ConnectionPool(host='localhost', port=6379, db=3, decode_responses=True)
rc = redis.Redis(connection_pool=cache_pool)


def init_group(group_id: int):
    """
    初始化群
    :param group_id: 群号
    :return:
    """
    if not gol.value_exist(f"KEYWORD_{group_id}"):
        print(f'=========初始化 {group_id}=========')
        with open(
                os.path.join(config.resource_path, "template", "key_template.json"),
                'r',
                encoding='utf-8'
        )as key_template_file:
            key_template = json.load(key_template_file)
        key_template["group"] = group_id
        gkw.insert_one(key_template)
        gol.set_value(f"KEYWORD_{group_id}", key_template['keyword'])

        with open(
                os.path.join(config.resource_path, "template", "config_template.json"),
                'r',
                encoding='utf-8'
        )as config_template_file:
            config_template = json.load(config_template_file)
        config_template["group"] = group_id
        gcf.insert_one(config_template)


def init_mocabot():
    """
    初始化机器人.

    :return: None
    """
    # 初始化所有群的关键词列表到内存
    d = gkw.find({}, {"_id": 0})
    for n in d:
        gol.set_value(f"KEYWORD_{n['group']}", n['keyword'])


def update_config(group_id: int, arg: str, value):
    """
    向数据库中更新某参数.

    :param group_id: QQ群号
    :param arg: 参数名称
    :param value: 参数值
    :return: 新参数值
    """
    # 更新数据库中Config
    query = {"group": group_id}
    new_value = {"$set": {arg: value}}
    gcf.update_one(query, new_value)

    return value


def fetch_config(group_id: int, arg: str):
    """
    从数据库中查询某参数.

    :param group_id: QQ群号 (int)
    :param arg: 参数名称 (str)
    :return: 参数值 (any), 若存在config但查询的参数不存在返回-2，若不存在config即群组config未初始化返回-1
    """
    res = gcf.find({"group": group_id}, {arg: 1})
    try:
        value = res[0].get(arg)
        if value is None:
            return -2
        else:
            return value
    except IndexError:
        return -1


def update_cd(group_id: int, cd_type: str, cd_time=0):
    """
    更新群组的某类cd.

    :param group_id: QQ群号(int)
    :param cd_type: 参数名称(str)
    :param cd_time: cd时间（可选，如不指定则从数据库中查找）
    :return: None
    """
    if not cd_time == 0:
        gol.set_value(f'in_{cd_type}_cd_{group_id}', get_timestamp() + cd_time)
    else:
        group_cd = fetch_config(group_id, cd_type)
        gol.set_value(f'in_{cd_type}_cd_{group_id}', get_timestamp() + group_cd)


def update_user_cd(user_id: int, cd_type: str, cd_time: int = 0):
    """
    更新用户的某类cd.

    :param user_id: QQ号(int)
    :param cd_type: 参数名称(str)
    :param cd_time: cd时间
    :return: None
    """
    gol.set_value(f'in_{cd_type}_user_cd_{user_id}', get_timestamp() + cd_time)


def is_in_cd(group_id: int, cd_type: str) -> bool:
    """
    判断是否在cd中.

    :param group_id: QQ群号
    :param cd_type: 要查询的cd类型
    :return: True/False
    """
    if gol.value_exist(f'in_{cd_type}_cd_{group_id}'):
        if get_timestamp() > gol.get_value(f'in_{cd_type}_cd_{group_id}'):
            return False
        else:
            return True
    else:
        return False


def is_in_user_cd(user_id: int, cd_type: str) -> bool:
    """
    判断用户是否在cd中.

    :param user_id: QQ号
    :param cd_type: 要查询的cd类型
    :return: True/False
    """
    if gol.value_exist(f'in_{cd_type}_user_cd_{user_id}'):
        if get_timestamp() > gol.get_value(f'in_{cd_type}_user_cd_{user_id}'):
            return False
        else:
            return True
    else:
        return False


def get_timestamp() -> int:
    """
    获取秒级的时间戳

    :return: 秒级时间戳
    """
    return int(time.time())


def is_superman(member_id: int) -> bool:
    """
    判断是否是特权阶级.

    :param member_id: 用户QQ

    :return: True/False
    """
    if not os.path.isfile('superman.json'):
        with open('superman.json', 'w+')as superman_file:
            init_data = {"superman": [0]}
            superman_file.write(json.dumps(init_data, indent=4))
    with open('superman.json', 'r')as superman_file:
        data = json.load(superman_file)
    if member_id in data["superman"]:
        return True
    else:
        return False


def contains(*arg: str) -> bool:
    """
    检查多个字符串是否在另一个字符串中出现

    :param arg: 任意数量的参数，检查前面的参数是否在最后一个参数中出现
    :return:
    """
    target = arg[-1]
    for text in arg[:-1]:
        if text in target:
            return True
    return False


def fetch_group_keyword(group: int) -> dict:
    """
    获取群关键词列表.

    :param group: 群号

    :return: 关键词列表(dict)
    """
    return gol.get_value(f"KEYWORD_{group}")


def fetch_group_count(group: int) -> dict:
    """
    获取群关键词列表.

    :param group: 群号

    :return: 统计次数列表(dict)
    """
    try:
        res = gc.find({"group": group})
        data = res[0]
        del data['_id']
        del data['group']
        return data
    except IndexError:
        return {}


def sort_dict(origin_dict: dict) -> dict:
    """
    对dict进行排序

    :param origin_dict: 原字典

    :return: 排序后的字典
    """
    result = {}
    temp = sorted(origin_dict.keys(), key=lambda char: lazy_pinyin(char)[0][0])
    for og in temp:
        result[og] = origin_dict.get(og)
    return result


def create_dict_pic(data: dict, group_id_with_type: str, title: str, sort_by_value=False):
    """
    将json转换为图片文件.

    :param data: Dict
    :param group_id_with_type: 群号_文件类型
    :param title: 表格第二列的标题
    :param sort_by_value: 是否按照值从大到小排序
    :return: None, 写入{temp_path}/{名称}.png
    """
    tab = PrettyTable(border=False, header=True, header_style='title')
    font_file = os.path.join(config.resource_path, "font", "PingFang.ttf")
    bg_file = os.path.join(config.resource_path, "template", "bg.png")
    new_img_file = os.path.join(config.temp_path, f"{group_id_with_type}.png")
    # 设置表头
    tab.field_names = ["名称", title]
    tab.align["名称"] = "l"
    # 表格内容插入
    tab.add_row(["", ""])
    if sort_by_value:
        for item in sorted(data.items(), key=lambda d: d[1], reverse=True):
            tab.add_row([item[0], item[1]])
    else:
        for item in data.items():
            tab.add_row([item[0], item[1]])
    tab_info = str(tab).replace("[", "").replace("]", "").replace(",", ", ").replace("'", " ")
    space = 50
    # PIL模块中，确定写入到图片中的文本字体
    font = ImageFont.truetype(font_file, 20, encoding='utf-8')
    # Image模块创建一个图片对象
    im = ImageLib.new('RGB', (10, 10), (255, 255, 255, 0))
    # ImageDraw向图片中进行操作，写入文字或者插入线条都可以
    draw = ImageDraw.Draw(im, "RGB")
    # 根据插入图片中的文字内容和字体信息，来确定图片的最终大小
    img_size = draw.multiline_textsize(tab_info, font=font)
    # 图片初始化的大小为10-10，现在根据图片内容要重新设置图片的大小
    im_new = im.resize((img_size[0] + int(space * 2), img_size[1] + int(space * 2)))
    del draw
    del im
    draw = ImageDraw.Draw(im_new, 'RGB')
    img = ImageLib.open(bg_file)
    im_new.paste(img, (0, 0))
    img_x, img_y = im_new.size
    bg_x, bg_y = img.size
    if bg_y < img_y:
        pos_y = 0
        while pos_y < img_y:
            im_new.paste(img, (0, pos_y))
            pos_y += bg_y
    if bg_x < img_x:
        pos_x = 0
        pos_y = 0
        while pos_y < img_y:
            while pos_x < img_x:
                im_new.paste(img, (pos_x, pos_y))
                pos_x += bg_x
            pos_x = 0
            pos_y += bg_y
    draw.multiline_text((space, space), tab_info, fill=(0, 0, 0), font=font)
    im_new.save(new_img_file, "png")
    del draw


def set_group_flag(group_id: int):
    """
    设置群已处理过的flag.

    :return: 使用说明
    """
    gol.set_value(f'group_{group_id}_processed', True)


def get_group_flag(group_id: int):
    """
    获取群处理flag状态.

    :return: 状态(bool)
    """
    flag = gol.get_value(f'group_{group_id}_processed')
    if flag:
        return True
    return False


def exp_enabled(group_id: int) -> bool:
    """
    检查是否启用实验功能

    :param group_id: 群号

    :return: True/False
    """
    exp_status = fetch_config(group_id, "exp")
    if exp_status is None:
        return True
    else:
        if exp_status == 0:
            return False
        else:
            return True


def rand_pic(name: str, count=1) -> list:
    """
    从图片库中随机抽取{count}张

    :param name: 名称
    :param count: 抽取的数量
    :return: 文件名列表
    """
    return rc.srandmember(name, count)


def user_manual() -> MessageChain:
    """
    返回使用说明.

    :return: 使用说明
    """
    return MessageChain.create([
        Plain("使用说明：https://mocabot.cn/"),
    ])


def random_moca_pa():
    """
    摩卡爬.

    :return:
    """
    random_file = random.choice(os.listdir(os.path.join(config.resource_path, "pa")))
    return MessageChain.create([
        Image.fromLocalFile(os.path.join(config.resource_path, 'pa', random_file))
    ])


def random_moca_keai():
    """
    摩卡可爱.

    :return:
    """
    random_file = random.choice(os.listdir(os.path.join(config.resource_path, "keai")))
    return MessageChain.create([
        Image.fromLocalFile(os.path.join(config.resource_path, 'keai', random_file))
    ])


def update_count(group: int, name: str):
    """
    更新统计次数.

    :param group: 群号
    :param name: 要+1的名称
    :return: None
    """
    query = {"group": group}
    new_value = {"$inc": {name: 1}}
    gc.update_one(query, new_value)


def user_set_lp(qq: int, group: int, lp_name: str) -> list:
    """
    用户设置lp.

    :param qq: QQ号
    :param group: QQ群号
    :param lp_name: 要设置的lp名称
    :return: [True, 设置的名称](成功), [False, ""](未找到)
    """
    group_keyword = fetch_group_keyword(group)
    # lp_name = find_lp(lp_name, group_keyword)
    if lp_name == "NOT_FOUND":
        return [False, ""]
    else:
        res = ucf.update_one({"qq": qq}, {"$set": {"lp": lp_name}})
        if res.modified_count == 0:
            ucf.insert_one({"qq": qq, "lp": lp_name})
        return [True, lp_name]


def fetch_user_lp(qq: int, group: int) -> list:
    """
    获取用户设置的lp.

    :param qq: QQ号
    :param group: QQ群号
    :return: lp_name, 未设置：NOT_SET, 未找到: NOT_FOUND
    """
    group_keyword = fetch_group_keyword(group)
    res = ucf.find_one({"qq": qq}, {"lp": 1})
    try:
        lp_name = res['lp']
        if lp_name in group_keyword:
            return lp_name
        else:
            return "NOT_FOUND"
    except TypeError:
        return "NOT_SET"
    except KeyError:
        return "NOT_SET"
