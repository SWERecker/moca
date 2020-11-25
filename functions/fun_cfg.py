import json
import os

cfg = {}
if os.path.isfile(os.path.join(os.path.dirname(os.path.abspath("__main__")), "functions", "config.json")):
    with open(os.path.join(os.path.dirname(os.path.abspath("__main__")), "functions", "config.json"),
              'r',
              encoding='utf-8')as cfg_file:
        cfg = json.load(cfg_file)
else:
    cfg = {
        "BUY_PAN_INTERVAL": 3600,
        "SIGNIN_PAN": 5,
        "BUY_PAN_MIN": 1,
        "BUY_PAN_MAX": 10,
        "EAT_PAN_AMOUNT": 1,
        "appid": "appid",
        "secret_key": "key"
    }
