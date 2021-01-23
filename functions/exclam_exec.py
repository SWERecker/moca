import random

from graia.application import MessageChain
from graia.application.message.elements.internal import Plain


# noinspection PyBroadException
def exclam_exec_processor(_data: str) -> MessageChain:
    if _data == "":
        return
    _paras = _data.split()
    command = _paras[0]
    if len(_paras) > 1:
        paras = _paras[1:]
    else:
        paras = []

    if command == "r" and bool(paras):
        chosen = random_thing(paras)
        if not chosen == "PARA_NOT_ENOUGH":
            return MessageChain.create([
                Plain(f"那当然是{chosen}啦~")
            ])
        else:
            return MessageChain.create([
                Plain("错误：参数数量不足\n例子：!r 吃饭 睡觉")
            ])

    if command == "rd":
        try:
            if len(paras) == 0:
                return MessageChain.create([
                    Plain("掷1个1~6的色子\n"
                          f"结果为：{do_dice()[0]}")
                ])
            paras = [int(n) for n in paras]
            if len(paras) == 3:
                result = ""
                res = do_dice(paras[1], paras[2], paras[0])
                for n in res[1]:
                    result += str(n) + ", "
                result = result.strip().strip(',')
                return MessageChain.create([
                    Plain(f"掷{res[0]}个{paras[1]}~{paras[2]}的色子\n"
                          f"结果为：{result}")
                ])
            else:
                return MessageChain.create([
                    Plain(f"错误：参数数量错误\n例子：!rd 1 1 6")
                ])
        except Exception as e:
            return MessageChain.create([
                Plain(f"错误：{repr(e)}")
            ])

    if command == "c":
        try:
            if len(paras) == 1:
                return MessageChain.create([
                    Plain(f"{paras[0]}为：{random.randint(0, 100)}")
                ])
        except Exception as e:
            return MessageChain.create([
                Plain(f"错误：{repr(e)}")
            ])


def random_thing(things: list) -> str:
    if len(things) > 1:
        return str(random.choice(things))
    else:
        return "PARA_NOT_ENOUGH"


def do_dice(_min=1, _max=6, _count=1) -> list:
    _count = 10 if _count > 10 else _count
    result = []
    for _ in range(_count):
        result.append(random.randint(_min, _max))
    return _count, result
