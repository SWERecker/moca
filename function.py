import json
import os
import time

import pymongo
from graia.application import MessageChain, GraiaMiraiApplication, Group
from pypinyin import lazy_pinyin
from PIL import Image as ImageLib
from PIL import ImageDraw, ImageFont
from prettytable import PrettyTable

import config
import global_var as gol

client = pymongo.MongoClient(host='localhost', port=27017)

db = client['moca']
gcf = db['group_config']


def init_group_config(group_id: int):
    print(f'init group {group_id}')


def update_config(group_id: int, arg: str, value):
    """
    向数据库中更新某参数.

    :param group_id: QQ群号
    :param arg: 参数名称
    :param value: 参数值
    :return: 新参数值
    """
    query = {"group_id": group_id}
    new_value = {"$set": {arg: value}}
    gcf.update_one(query, new_value)
    return value


def fetch_config(group_id: int, arg: str):
    """
    从数据库中查询某参数.

    :param group_id: QQ群号 (int)
    :param arg: 参数名称 (str)
    :return: 参数值 (any), 若存在config但查询的参数不存在返回-1，若
    """
    query_config = {"group_id": group_id}
    if not gcf.count_documents(query_config) == 1:
        init_group_config(group_id)

    res = gcf.find({"group_id": group_id}, {arg: 1})
    try:
        config_data = res[0]
        value = config_data.get(arg)
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
    更新群组的某类cd.

    :param user_id: QQ号(int)
    :param cd_type: 参数名称(str)
    :param cd_time: cd时间
    :return: None
    """
    gol.set_value(f'in_{cd_type}_user_cd_{user_id}', get_timestamp() + cd_time)

    # if not cd_time == 0:
    #    gol.set_value(f'in_{cd_type}_cd_{user_id}', get_timestamp() + cd_time)
    # else:
    #    group_cd = fetch_config(user_id, cd_type)
    #    gol.set_value(f'in_{cd_type}_cd_{user_id}', get_timestamp() + group_cd)


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
    print(target)
    for text in arg[:-1]:
        print(text, "in", target, "?")
        if text in target:
            return True
    return False


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
