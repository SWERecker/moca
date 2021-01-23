import json
import os
import time

import requests
from graia.application import MessageChain
from graia.application.message.elements.internal import Plain, At, Image

from function import moca_log

random_url = 'https://api.mocabot.cn/api'

dictionary = {
    "band": {
        "ro": "Roselia",
        "ppp": "Poppin'Party",
        "pp": "Pastel*Palettes",
        "ag": "Afterglow",
        "hhw": "Hello, Happy World",
        "ras": "RAISE A SUILEN",
        "mo": "Morfonica",
        "rimi": "牛込りみ",
        "saaya": "山吹沙綾",
        "arisa": "市ヶ谷有咲",
        "otae": "花園たえ",
        "ayaxmocaxlisaxkanonxtsugu": "彩×モカ×リサ×花音×つぐみ",
        "pppxykn": "Poppin'Party×友希那",
        "ksmxranxayaxyknxkkr": "香澄×蘭×彩×友希那×こころ",
        "hhwxranxaya": "ハロハピ×蘭×彩",
        "roxran": "Roselia×蘭",
        "agxkkr": "Afterglow×こころ",
        "pppxgg": "Poppin‘Party × Glitter*Green",
        "ksmxag": "香澄×Afterglow",
        "pppxayaxkkr": "Poppin'Party×彩×こころ",
        "other": "Others"
    },
    "level": {
        "ex": "EXPERT",
        "sp": "SPECIAL",
        "full": "FULL"
    },
    "type": {
        "og": "原创",
        "co": "翻唱"
    },
    "diff": ["24", "25", "26", "27", "28", "29"]
}

query_conditions = {
    "band": ["ro", "ppp", "pp", "ag", "hhw", "ras", "mo", "other"],
    "diff": ["24", "25", "26", "27", "28", "29"],
    "level": ["ex", "sp", "full"]
}


async def random_song(member: int, text: str) -> MessageChain:
    """
    随机选歌.

    :param member: QQ号码
    :param text: 选歌参数
    :return:
    """
    p_text = text.replace("；", ";").replace("，", ",").replace(" ", "")
    if text[4:] == "格式":
        return MessageChain.create([
            Image.fromLocalFile(os.path.join
                                (os.path.dirname(os.path.abspath("__main__")), "resource", "song", "song.gif"))
        ])
    timestamp = int(round(time.time() * 1000))
    para = {"mode": "random", "time": timestamp}
    query = {"band": "空", "diff": "空", "level": "空"}

    paras = p_text[4:].split(',')

    for p in paras:

        if p in query_conditions['band']:
            if "band" not in para.keys():
                para["band"] = ""

            if query["band"] == "空":
                query["band"] = ""

            para["band"] += p + ","
            query["band"] += str(dictionary["band"].get(p)) + "|"

        elif p in query_conditions['diff']:
            if "diff" not in para.keys():
                para["diff"] = ""

            if query["diff"] == "空":
                query["diff"] = ""

            para["diff"] += p + ","
            query["diff"] += str(p) + "|"

        elif p in query_conditions['level']:
            if "level" not in para.keys():
                para["level"] = ""

            if query["level"] == "空":
                query["level"] = ""

            para["level"] += p + ","
            query["level"] += str(dictionary["level"].get(p)) + "|"

    if para.get("band"):
        para["band"] = para["band"].strip(',')
        query["band"] = query["band"].strip('|')

    if para.get("diff"):
        para["diff"] = para["diff"].strip(',')
        query["diff"] = query["diff"].strip('|')

    if para.get("level"):
        para["level"] = para["level"].strip(',')
        query["level"] = query["level"].strip('|')

    res = requests.get(random_url, params=para)
    result = json.loads(res.text)
    if result.get("msg") == "error":
        return MessageChain.create([
            At(target=member),
            Plain(f"\n有效筛选条件：乐队：{query['band']}  难度：{query['diff']}  类型：{query['level']}\n"
                  "请检查所选的条件下是否存在歌曲\n"
                  "发送【随机选歌格式】来查看选歌格式")
        ])
    result_song = result.get('result')[0]
    result_name = result_song.get('name')
    result_band = dictionary['band'].get(result_song.get('band'))
    result_level = dictionary['level'].get(result_song.get('level'))
    result_diff = result_song.get('diff')
    result_type = dictionary['type'].get(result_song.get('type'))
    result_str = f'\n有效筛选条件：乐队：{query["band"]} 难度：{query["diff"]} 类型：{query["level"]}\n' \
                 f'选歌结果：\n{result_name} - {result_band}\n{result_level} {result_diff} {result_type}曲'\
        .replace("None", "无")

    moca_log(result_str, qq=member)
    return MessageChain.create([
        At(target=member),
        Plain(result_str)
    ])
