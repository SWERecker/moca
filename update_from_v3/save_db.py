# -*- coding:utf-8 -*-
import json

import redis
import pymongo

client = pymongo.MongoClient(host='localhost', port=27017)
db1 = client['moca']
ucf = db1['user_config']
gkw = db1['group_keyword']
gc = db1['group_count']
gcf = db1['group_config']

r = redis.Redis(db=0, decode_responses=True)

signin_data = r.hgetall("SIGNIN")
lp_data = r.hgetall('LPLIST')
clp_data = r.hgetall('CLPTIME')
key_data = r.hgetall('KEYWORDS')
group_count_data = r.hgetall('COUNT')
group_config_data = r.hgetall('CONFIG')

to_update_data = {}
# if __name__ == "__main__":

    # convert user_config
    # for qq in signin_data:
    #     to_update_data = json.loads(signin_data[qq])
    #     to_update_data['qq'] = int(qq)
    #     if qq in lp_data:
    #         to_update_data['lp'] = lp_data[qq]
    #     if qq in clp_data:
    #         to_update_data['clp_time'] = int(clp_data[qq])
    # ucf.insert_one(to_update_data)

    # for group in group_config_data:
    #     if not group == "config_template":
    #         to_update_data = json.loads(group_config_data[group])
    #         to_update_data['group'] = int(group)
    #         gcf.insert_one(to_update_data)
#
#     for qq in lp_data:
#         query = {"qq": int(qq)}
#         d = ucf.find_one(query)
#         if d is None:
#             if clp_data.get(qq) is None:
#                 clp_times = -1
#             else:
#                 clp_times = int(clp_data[qq])
#             data = {
#                 "time": -1,
#                 "pan": -1,
#                 "sum_day": -1,
#                 "last_buy_time": -1,
#                 "qq": int(qq),
#                 "lp": lp_data[qq],
#                 "clp_time": clp_times
#             }
#             ucf.insert_one(data)


# if __name__ == "__main__":
#     # for group in key_data:
#     #     if not group == "key_template":
#     #         key = json.loads(key_data[group])
#     #         try:
#     #             temp = key['hina.gif']
#     #             del key['hina.gif']
#     #             key['hina_gif'] = temp
#     #         except:
#     #             pass
#     #         d = {"keyword": key, "group": int(group)}
#     #         gkw.insert_one(d)
#     #         print("converting", group)
#
#     res = gkw.find({"group": 27786700})
#     print(res[0]['keyword'])

if __name__ == "__main__":
    with open('backup\\lp_data.json', 'w', encoding='utf-8')as lp_data_file:
        lp_data_file.write(json.dumps(lp_data, ensure_ascii=False))
    with open('backup\\clp_data.json', 'w', encoding='utf-8')as clp_data_file:
        clp_data_file.write(json.dumps(clp_data, ensure_ascii=False))
    with open('backup\\key_data_file.json', 'w', encoding='utf-8')as key_data_file:
        key_data_file.write(json.dumps(key_data, ensure_ascii=False))
    with open('backup\\group_count_file.json', 'w', encoding='utf-8')as group_count_file:
        group_count_file.write(json.dumps(group_count_data, ensure_ascii=False))
    with open('backup\\group_signin_file.json', 'w', encoding='utf-8')as group_signin_file:
        group_signin_file.write(json.dumps(signin_data, ensure_ascii=False))
    with open('backup\\group_config_file.json', 'w', encoding='utf-8')as group_config_file:
        group_config_file.write(json.dumps(group_config_data, ensure_ascii=False))

#     for group in group_count_data:
#         group_data = json.loads(group_count_data[group])
#         try:
#             temp = group_data['hina.gif']
#             del group_data['hina.gif']
#             group_data['hina_gif'] = temp
#         except:
#             pass
#         data = {'group': int(group)}
#         data.update(group_data)
#         gc.insert_one(data)

