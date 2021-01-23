import os
import time

import redis
import platform

if platform.system() == "Linux":
    pic_path = '/usr/local/moca/pic'
else:
    pic_path = 'C:\\mirai\\upload'

walks = os.walk(pic_path)

r = redis.Redis(db=3, decode_responses=True)

ignore_files = ["index.txt", ".user.ini"]


if __name__ == "__main__":
    r.flushdb()
    with open(os.path.join(pic_path, 'index.txt'),
              'r', encoding='utf-8')as f:
        for record in f.readlines():
            record = record.strip().split('|')
            file_path = os.path.join(pic_path, record[0])
            cats = record[1].strip().split(' ')
            for cat in cats:
                r.sadd(cat, file_path)

    str_time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
    with open(os.path.join('log', 'db_update.log'), 'a', encoding='utf-8')as db_log:
        db_log.write(f'[{str_time_now}] Updated file list, keys: \n')

