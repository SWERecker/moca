import difflib
import json
import os
import random
import re
import time
import datetime

import pymongo
import redis
import requests
from graia.application import MessageChain
from graia.application.message.elements.internal import Plain, Image, ImageType
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

forbidden_signs = "/[]-^?*.$\\|"


def init_group(group: int):
    """
    初始化群

    :param group: 群号
    :return: None
    """
    if not gol.value_exist(f"KEYWORD_{group}"):
        print(f'=========初始化 {group}=========')
        with open(
                os.path.join(config.resource_path, "template", "key_template.json"),
                'r',
                encoding='utf-8'
        )as key_template_file:
            key_template = json.load(key_template_file)
        key_template["group"] = group
        gkw.insert_one(key_template)
        gol.set_value(f"KEYWORD_{group}", key_template['keyword'])

        with open(
                os.path.join(config.resource_path, "template", "config_template.json"),
                'r',
                encoding='utf-8'
        )as config_template_file:
            config_template = json.load(config_template_file)
        config_template["group"] = group
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


def update_config(group: int, arg: str, value):
    """
    向数据库中更新某参数.

    :param group: QQ群号
    :param arg: 参数名称
    :param value: 参数值
    :return: 新参数值
    """
    gcf.update_one({"group": group}, {"$set": {arg: value}})
    return value


def fetch_config(group: int, arg: str):
    """
    从数据库中查询某参数.

    :param group: QQ群号 (int)
    :param arg: 参数名称 (str)
    :return: 参数值 (any), 若存在config但查询的参数不存在返回-2，若不存在config即群组config未初始化返回-1
    """
    res = gcf.find({"group": group}, {arg: 1})
    try:
        value = res[0].get(arg)
        if value is None:
            return -2
        else:
            return value
    except IndexError:
        return -1


def fetch_user_config(qq: int, arg: str):
    """
    从数据库中查询某参数.

    :param qq: QQ号 (int)
    :param arg: 参数名称 (str)
    :return: 参数值 (any), 若存在config但查询的参数不存在返回-2，若不存在config即config未初始化返回-1
    """
    res = ucf.find({"qq": qq}, {arg: 1})
    try:
        value = res[0].get(arg)
        if value is None:
            return -2
        else:
            return value
    except IndexError:
        return -1


def update_user_config(qq: int, arg: str, value):
    """
    向user数据库中更新某参数.

    :param qq: QQ号
    :param arg: 参数名称
    :param value: 参数值
    :return: 新参数值
    """
    res = ucf.update_one({"qq": qq}, {"$set": {arg: value}})
    if res.modified_count == 0:
        ucf.insert_one({"qq": qq, arg: value})
    return value


def update_cd(group: int, cd_type: str, cd_time=0):
    """
    更新群组的某类cd.

    :param group: QQ群号(int)
    :param cd_type: 参数名称(str)
    :param cd_time: cd时间（可选，如不指定则从数据库中查找）
    :return: None
    """
    if not cd_time == 0:
        gol.set_value(f'in_{cd_type}_cd_{group}', get_timestamp_now() + cd_time)
    else:
        group_cd = fetch_config(group, cd_type)
        gol.set_value(f'in_{cd_type}_cd_{group}', get_timestamp_now() + group_cd)


def update_user_cd(user_id: int, cd_type: str, cd_time: int = 0):
    """
    更新用户的某类cd.

    :param user_id: QQ号(int)
    :param cd_type: 参数名称(str)
    :param cd_time: cd时间
    :return: None
    """
    gol.set_value(f'in_{cd_type}_user_cd_{user_id}', get_timestamp_now() + cd_time)


def is_in_cd(group: int, cd_type: str) -> bool:
    """
    判断是否在cd中.

    :param group: QQ群号
    :param cd_type: 要查询的cd类型
    :return: True/False
    """
    if gol.value_exist(f'in_{cd_type}_cd_{group}'):
        if get_timestamp_now() > gol.get_value(f'in_{cd_type}_cd_{group}'):
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
        if get_timestamp_now() > gol.get_value(f'in_{cd_type}_user_cd_{user_id}'):
            return False
        else:
            return True
    else:
        return False


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
    获取群统计次数.

    :param group: 群号

    :return: 统计次数列表(dict)
    """
    try:
        res = gc.find({"group": group}, {"_id": 0, "group": 0})
        data = res[0]
        return data
    except IndexError:
        return {}


def fetch_picture_count(group: int) -> dict:
    """
    获取群统计次数.

    :param group: 群号
    :return: 文件数量(dict)
    """
    result = {}
    group_keywords = fetch_group_keyword(group)
    names = group_keywords.keys()
    for name in names:
        result[name] = rc.scard(name)
    return result


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
    :return: 图片文件的目录, 写入{temp_path}/{名称}.png
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
    return new_img_file


def set_group_flag(group: int):
    """
    设置群已处理过的flag.

    :return: 使用说明
    """
    gol.set_value(f'group_{group}_processed', True)


def get_group_flag(group: int):
    """
    获取群处理flag状态.

    :return: 状态(bool)
    """
    if gol.get_value(f'group_{group}_processed'):
        return True
    return False


def cfg_enabled(group: int, para: str, bit=True) -> bool:
    """
    检查是否启用功能(默认True)

    :param group: 群号
    :param para: 参数
    :param bit: 默认状态(True)，通过此参数设置群参数未设置时返回的状态
    :return: True/False
    """
    cfg_status = fetch_config(group, para)
    if cfg_status is None:
        return bit
    else:
        if cfg_status == 0:
            return False
        else:
            return True


def random_do(chance: int) -> bool:
    """
    随机事件 {chance}% 发生.

    :param chance: 0~100,
    :return: 发生(True)，不发生(False)
    """
    if random.random() < (int(chance) / 100):
        return True
    else:
        return False


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
    res = gc.update_one({"group": group}, {"$inc": {name: 1}})
    # 若未修改任何数据说明该群组数据为空
    if res.modified_count == 0:
        gc.insert_one({"group": group, name: 1})


def user_set_lp(qq: int, group: int, lp_name: str) -> list:
    """
    用户设置lp.

    :param qq: QQ号
    :param group: QQ群号
    :param lp_name: 要设置的lp名称
    :return: [True, 设置的名称](成功), [False, ""](未找到)
    """
    lp_name = match_lp(group, lp_name)
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


def check_para(para: str) -> bool:
    """
    要检查的字符串.

    :param para: 字符串
    :return: 字符串不正常返回True，正常返回False
    """
    global forbidden_signs
    for c in para:
        if c in forbidden_signs:
            return True
    return False


def append_keyword(group: int, paras: list):
    """

    :param group: 群号
    :param paras: 参数组[要添加的对象, 关键词]
    :return: -2: 关键词已能识别; -1: 没有此对象; 0: 添加成功
    """
    try:
        group_keywords = fetch_group_keyword(group)
        name = paras[0]
        key = paras[1]

        if group_keywords[name] == '':
            group_keywords[name] = key
        else:
            p = re.findall(group_keywords[name], key)
            if p:
                return MessageChain.create([
                    Plain(f"错误：{paras[0]}的关键词列表中已存在能够识别 {paras[1]} 的关键词了")
                ])
            group_keywords[name] += f"|{key}"

        gol.set_value(f"KEYWORD_{group}", group_keywords)
        gkw.find_one_and_update({"group": group}, {"$set": {"keyword": group_keywords}})
        return MessageChain.create([
            Plain(f"向{paras[0]}中添加了关键词：{paras[1]}")
        ])
    except KeyError:
        return MessageChain.create([
            Plain(f"错误：关键词列表中未找到{paras[0]}")
        ])


def remove_keyword(group: int, paras: list):
    """
    删除关键词.

    :param group: 群号
    :param paras: 参数组[要删除的对象, 关键词]
    :return: -2: 未找到此关键词; -1: 没有此对象; 0: 删除成功
    """
    try:
        group_keywords = fetch_group_keyword(group)
        name = paras[0]
        key = paras[1]

        original_keywords = group_keywords[name].split('|')
        if key in original_keywords:
            k_index = original_keywords.index(key)
            del original_keywords[k_index]
            group_keywords[name] = ""
            for key in original_keywords:
                group_keywords[name] += f"{key}|"
            group_keywords[name] = group_keywords[name].rstrip("|")
            gol.set_value(f"KEYWORD_{group}", group_keywords)
            gkw.find_one_and_update({"group": group}, {"$set": {"keyword": group_keywords}})
            return MessageChain.create([
                Plain(f"删除了{paras[0]}中的关键词：{paras[1]}")
            ])
        else:
            return MessageChain.create([
                Plain(f"错误：{paras[0]}的关键词列表中未找到关键词 {paras[1]}")
            ])
    except KeyError:
        return MessageChain.create([
            Plain(f"错误：关键词列表中未找到{paras[0]}")
        ])


def fetch_clp_times(uid: int) -> int:
    """
    获取换lp的次数.

    :param uid: 用户QQ号
    :return: 换lp次数
    """
    try:
        res = ucf.find_one({"qq": uid}, {"clp_time": 1})
        return res['clp_time']
    except KeyError:
        return 0


def match_lp(group: int, lp_name: str) -> str:
    """
    匹配最接近的lp.

    :param group: 群组ID
    :param lp_name: 名称
    :return: 最接近的名称，若匹配不到则返回NOT_FOUND
    """
    simi_dict = {}
    keyword_list = fetch_group_keyword(group)
    for name, keys in keyword_list.items():  # 在字典中遍历查找
        key_list = keys.split('|')
        for key in key_list:
            seed = difflib.SequenceMatcher(None, str(lp_name), key).quick_ratio()
            if seed > 0.6:
                if name in simi_dict:
                    new_seed = simi_dict[name] + seed
                    simi_dict.update({name: new_seed})
                else:
                    simi_dict.update({name: seed})
    if bool(simi_dict):
        return sorted(simi_dict, key=simi_dict.__getitem__, reverse=True)[0]
    else:
        return "NOT_FOUND"


def lp_list_rank() -> dict:
    """
    统计设置为lp最多的10个.

    :return: 已从大到小排序的字典
    """
    result = {}
    lp_data = ucf.find({}, {"_id": 0, "qq": 1, "lp": 1})

    for data in lp_data:
        if 'lp' in data:
            if not result.get(data['lp']):
                result[data['lp']] = 1
            else:
                result[data['lp']] += 1
    sorted_dict = sorted(result.items(), key=lambda d: d[1], reverse=True)
    result = {}
    c = 0
    for k, v in sorted_dict:
        result[k] = v
        c += 1
        if c == 10:
            break
    return result


def get_timestamp_now() -> int:
    """
    获取当前时间戳（秒级）.

    :return: 当前时间戳（秒级）
    """
    return int(time.time())


def get_timestamp_today_start() -> int:
    """
    获取今天00：00的时间戳.

    :return: 今天00：00的时间戳
    """
    return int(time.mktime(time.strptime(str(datetime.date.today()), '%Y-%m-%d')))


def get_timestamp_today_end() -> int:
    """
    获取今天23:59:59的时间戳.

    :return: 今天23:59:59的时间戳
    """
    return int(time.mktime(time.strptime(str(datetime.date.today() + datetime.timedelta(days=1)), '%Y-%m-%d'))) - 1


def moca_repeater(group: int, message: MessageChain) -> [bool, bool]:
    """
    复读机.

    :param group: QQ群号
    :param message: 消息的MessageChain
    :return [bool: 是否复读, bool: 是否附带复读图片]
    """
    if not gol.value_exist(f"{group}_repeater"):
        gol.set_value(f"{group}_repeater", {"m_count": 0, "m_last_repeat": 'content'})

    exist_data: dict = gol.get_value(f"{group}_repeater")
    m_count = exist_data.get('m_count')
    excludeSourceMessage = re.sub(r"(?:\[mirai:source?:(.*?)?\])", "", message.asSerializationString())
    if m_count == 0:
        exist_data['m_cache_0'] = excludeSourceMessage
        exist_data['m_count'] = 1
    if m_count == 1:
        exist_data['m_cache_1'] = excludeSourceMessage
        exist_data['m_count'] = 2
    if m_count == 2:
        exist_data['m_cache_0'] = exist_data['m_cache_1']
        exist_data['m_cache_1'] = excludeSourceMessage

    gol.set_value(f"{group}_repeater", exist_data)
    # 缓存消息 ===
    if not is_in_cd(group, "repeatCD"):
        if not exist_data.get('m_last_repeat') == excludeSourceMessage:
            if exist_data.get('m_cache_0') == exist_data.get('m_cache_1'):
                if random_do(fetch_config(group, "repeatChance")):
                    exist_data['m_last_repeat'] = excludeSourceMessage
                    gol.set_value(f"{group}_repeater", exist_data)
                    if random_do(5):
                        return [True, True]
                    else:
                        return [True, False]
    return [False, False]


async def save_image(group: int, category: str, urls: list) -> MessageChain:
    """
    保存提交的图片.

    :param group: 群号
    :param urls: 图片URLs
    :param category: 图片分类
    :return: 结果MessageChain
    """
    # upload/{群号}/月-日/{imageId}.{imageType}
    success_count = 0
    failed_count = 0
    err_text = ""
    file_path = os.path.join(
        config.temp_path,
        'upload',
        str(group),
        time.strftime("%m-%d"),
        category
    )
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    for url in urls:
        # noinspection PyBroadException
        try:
            res = requests.get(url)
            content_type = res.headers.get("Content-Type")
            file_type = content_type.split('/')[-1]
            file_name = f'{url.split("/")[-2]}.{file_type}'
            save_path = os.path.join(file_path, file_name)
            with open(save_path, "wb") as image_file:
                image_file.write(res.content)
            success_count += 1
        except Exception as e:
            failed_count += 1
            err_text = repr(e)
    res_str = f'提交图片：收到{success_count}张图片'
    if not failed_count == 0:
        res_str += f'，失败{failed_count}张。\n'
        res_str += err_text
    return MessageChain.create([
        Plain(res_str)
    ])


async def upload_photo(group: int, message: MessageChain) -> MessageChain:
    """
    提交图片.

    :param group: 群号
    :param message: 消息
    :return:
    """
    text = message.asDisplay().replace(" ", "")
    data_list = []
    if not message.has(Image):
        return MessageChain.create([
            Plain("错误：你至少需要包含一张图片")
        ])
    category = text[text.index("提交图片"):].lstrip("提交图片").replace("[图片]", "")
    if category == "":
        return MessageChain.create([
            Plain("错误：请附带分类，例如：【提交图片群友b话】，再加上图片")
        ])
    if check_para(category):
        return MessageChain.create([
            Plain("错误：名称中含有非法字符，请检查")
        ])
    message_data = message.dict()['__root__']
    for index in range(len(message_data)):
        if message_data[index].get('type') == ImageType.Group:
            data_list.append(message_data[index].get("url"))
    res: MessageChain = await save_image(group, category, data_list)
    return res
