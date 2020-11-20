import os
import time

import redis
pic_path = 'D:\\PhotoTag\\Photos'
# pic_path = '/usr/local/moca/pic'

walks = os.walk(pic_path)
abs_path = pic_path
db = {}
r = redis.Redis(db=3, decode_responses=True)

if __name__ == "__main__":
    r.flushdb()
    for (root, dirs, files) in walks:
        for file in files:
            categories = file.split('.')[0].split('_')[0].split(',')

            for cat in categories:
                if cat not in db:
                    db[cat] = []
                file_path = os.path.join(abs_path, root, file)
                db[cat].append(file_path)
    print(db.keys())
    print(len(db.keys()))
    for cat, files in db.items():
        for file in files:
            r.sadd(cat, file)
    str_time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
    with open(os.path.join('log', 'db_update.log'), 'a', encoding='utf-8')as db_log:
        db_log.write(f'[{str_time_now}] Updated file list, keys: {len(db.keys())}\n')
