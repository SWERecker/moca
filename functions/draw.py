import random
import time

from graia.application import MessageChain
from graia.application.message.elements.internal import Plain, At, Image

from function import fetch_user_lp, rand_pic, get_timestamp_today_start, get_timestamp_today_end, fetch_user_config, \
    update_user_config, get_timestamp_now
from functions.pan import pan_change, pan_log


async def draw_lot(group: int, qq: int) -> MessageChain:
    """
    抽签.

    :param group: 群号
    :param qq: QQ号
    :return: 抽签结果.
    """
    draw_time: int = fetch_user_config(qq, "cqtime")
    if get_timestamp_today_start() < draw_time <= get_timestamp_today_end():
        str_draw_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(draw_time))
        today_luck = fetch_user_config(qq, "luck")
        today_lucky_num = "今日幸运数字：" + str(fetch_user_config(qq, "lucky_num"))
        return MessageChain.create([
            At(target=qq),
            Plain(f"\n你已经在今天的{str_draw_time}抽过签了哦~\n"
                  f"一天只能抽一次签哦~\n{today_luck}\n{today_lucky_num}")
        ])
    result = pan_change(qq, -1)
    pan_log(qq, -1, "抽签")
    if result[0]:
        rand_num = random.randint(1, 100)
        if rand_num < 20:
            # 大吉
            res_text = "今日运势：大~吉~"
        elif 20 <= rand_num < 50:
            # 吉
            res_text = "今日运势：吉~"
        elif 50 <= rand_num < 70:
            # 中吉
            res_text = "今日运势：中~吉~"
        elif 70 <= rand_num < 85:
            # 小吉
            res_text = "今日运势：小~吉~"
        else:
            # 凶
            res_text = "今日运势：凶！？..."
        lucky_num = random.randint(1, 10)
        draw_result = [
            At(target=qq),
            Plain("\n"),
            Plain(res_text),
            Plain("\n"),
            Plain(f"今天的幸运数字是：{lucky_num}")
        ]
        user_lp = fetch_user_lp(qq, group)
        if not(user_lp == "NOT_SET" or user_lp == "NOT_FOUND"):
            file = rand_pic(user_lp, 1)[0]
            draw_result.append(Image.fromLocalFile(file))
        update_user_config(qq, "cqtime", get_timestamp_now())
        update_user_config(qq, "luck", res_text)
        update_user_config(qq, "lucky_num", lucky_num)
        return MessageChain.create(draw_result)
    else:
        return MessageChain.create([
            Plain("呜呜呜，面包不够了呢，抽不了签了...")
        ])
