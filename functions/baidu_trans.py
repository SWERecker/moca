import hashlib
import json
import random
import urllib

import requests
from graia.application import MessageChain
from graia.application.message.elements.internal import Plain
from functions.fun_cfg import cfg

trans_url = 'http://api.fanyi.baidu.com/api/trans/vip/translate'

lang_dict = {
    "zh": "中文",
    "en": "英语",
    "yue": "粤语",
    "wyw": "文言文",
    "jp": "日语",
    "kor": "韩语",
    "fra": "法语",
    "spa": "西班牙语",
    "th": "泰语",
    "ara": "阿拉伯语",
    "ru": "俄语",
    "pt": "葡萄牙语",
    "de": "德语",
    "it": "意大利语",
    "el": "希腊语",
    "nl": "荷兰语",
    "pl": "波兰语",
    "bul": "保加利亚语",
    "est": "爱沙尼亚语",
    "dan": "丹麦语",
    "fin": "芬兰语",
    "cs": "捷克语",
    "rom": "罗马尼亚语",
    "slo": "斯洛文尼亚语",
    "swe": "瑞典语",
    "hu": "匈牙利语",
    "cht": "繁体中文",
    "vie": "越南语"
}

error_dict = {
    "52001": "请求超时",
    "52002": "系统错误",
    "54003": "API访问频率受限",
    "54004": "账户余额不足"
}


async def baidu_translate(message: MessageChain) -> MessageChain:
    text = message.asDisplay()
    if len(text) > 2:
        if cfg["appid"] == "appid" or cfg["secret_key"] == "key":
            return MessageChain.create([
                Plain("错误：未设置AppID或SecretKey\n请联系开发者")
            ])
        try:
            trans_content = message.asDisplay()[message.asDisplay().index('翻译') + 2:]
            from_lang = 'auto'
            to_lang = 'zh'
            salt = random.randint(32768, 65536)
            sign = cfg["appid"] + trans_content + str(salt) + cfg["secret_key"]
            sign = hashlib.md5(sign.encode()).hexdigest()
            api_url = f'{trans_url}?appid={cfg["appid"]}&q={urllib.parse.quote(trans_content)}' \
                      f'&from={from_lang}&to={to_lang}&salt={salt}&sign={sign}'
            res = requests.get(api_url)
            dict_res = json.loads(res.text)
            if 'error_code' in dict_res:
                return MessageChain.create([
                    Plain(f'错误：{dict_res.get("error_code")}|{error_dict.get(dict_res.get("error_code"))}')
                ])
            detect_from_lang = lang_dict.get(dict_res.get("from"))
            if not detect_from_lang:
                detect_from_lang = "未知"
            result = f'百度翻译 源语言：{detect_from_lang}\n'
            trans_data = dict_res.get('trans_result')
            for data in trans_data:
                result += f"{data.get('dst')}\n"
            return MessageChain.create([
                Plain(result)
            ])
        except Exception as e:
            return MessageChain.create([
                Plain(f'错误：{repr(e)}')
            ])
