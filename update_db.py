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


def update_txt():
    f = open(os.path.join(pic_path, 'index.txt'), 'a', encoding='utf-8')
    for (root, dirs, files) in walks:
        for file in files:
            if not file == "index.txt":
                cats, file_new_name = file.split('_', 1)
                cats = cats.split('_')[0].split(',')
                cat = ""
                file_with_path = os.path.join(root, file)
                new_file_with_path = os.path.join(root, file_new_name).lstrip(pic_path).replace("\\", "/")
                os.rename(file_with_path, new_file_with_path)
                for c in cats:
                    cat += c + " "
                cat = cat.strip()
                f.write(f"{new_file_with_path}|{cat}\n")
    f.close()


if __name__ == "__dmain__":
    r.flushdb()
    with open(os.path.join(pic_path, 'index.txt'),
              'r', encoding='utf-8')as f:
        for record in f.readlines():
            record = record.strip().split('|')
            file_path = os.path.join(pic_path, file_path)
            cats = record[1].strip().split(' ')
            for cat in cats:
                r.sadd(cat, file_path)

    str_time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
    with open(os.path.join('log', 'db_update.log'), 'a', encoding='utf-8')as db_log:
        db_log.write(f'[{str_time_now}] Updated file list, keys: \n')


if __name__ == "__main__":
    update_txt()
