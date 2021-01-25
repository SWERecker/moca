import asyncio
import sys

from graia.application import GraiaMiraiApplication, Session, FriendMessage, Friend, MessageChain
from graia.application.event.mirai import NewFriendRequestEvent
from graia.application.message.elements.internal import Plain, Image
from graia.broadcast import Broadcast

from function import contains, user_manual, config, rand_pic, moca_log, update_count, gkw, ucf
from functions.pan import twice_lp

loop = asyncio.get_event_loop()
bcc = Broadcast(loop=loop)

gapp = GraiaMiraiApplication(
    broadcast=bcc,
    connect_info=Session(
        host=config.get("server_addr"),  # 填入 httpapi 服务运行的地址
        authKey=config.get("auth_key"),  # 填入 authKey
        account=config.get("bot_id"),  # 你的机器人的 qq 号
        websocket=True  # Graia 已经可以根据所配置的消息接收的方式来保证消息接收部分的正常运作.
    ),
    enable_chat_log=False
)

private_keyword = {}


def is_in_user_cd(_qq: int, _type: str) -> bool:
    return False


def init_dm():
    global private_keyword
    d = gkw.find({"group": 0}, {"_id": 0})
    for n in d:
        private_keyword = n['keyword']


def pri_fetch_user_lp(qq: int) -> str:
    """
    获取用户设置的lp.

    :param qq: QQ号
    :return: lp_name, 未设置：NOT_SET, 未找到: NOT_FOUND
    """
    global private_keyword
    res = ucf.find_one({"qq": qq}, {"lp": 1})
    try:
        lp_name = res['lp']
        if lp_name in private_keyword:
            return lp_name
        else:
            return "NOT_FOUND"
    except TypeError:
        return "NOT_SET"
    except KeyError:
        return "NOT_SET"


@bcc.receiver(FriendMessage)
async def friend_message_handler(app: GraiaMiraiApplication, friend: Friend, message: MessageChain):
    text = message.asDisplay().strip()
    if contains("使用说明", "help", text):
        await app.sendFriendMessage(friend, user_manual())
        return

    #   发送lp
    #   权限：成员
    #   是否At机器人：否
    if not is_in_user_cd(friend.id, "replyCD"):
        if ("来点" in text) and ("lp" in text.replace("老婆", "lp")):
            en_twice_lp = text.startswith("多")
            lp_name = pri_fetch_user_lp(friend.id)

            if lp_name == "NOT_SET":
                await app.sendFriendMessage(friend, MessageChain.create([
                    Plain("az，似乎你还没有设置lp呢~\n用【wlp是xxx】来设置一个吧~\n发送【关键词列表】可以查看可以设置的列表哦~")
                ]))
                return

            if lp_name == "NOT_FOUND":
                await app.sendFriendMessage(friend, MessageChain.create([
                    Plain("az，这里似乎看不了你lp呢...")
                ]))
                return

            pic_num = 1
            res_text = ""
            if en_twice_lp:
                res = twice_lp(0, friend.id, is_private=True)
                pic_num = res[0]
                if not res[1] == -1:
                    res_text = f"摩卡吃掉了3个面包，你还剩{res[1]}个面包哦~"
                else:
                    res_text = "呜呜呜，面包不够吃啦~"
                    en_twice_lp = False
            d = [Image.fromLocalFile(e) for e in rand_pic(lp_name, pic_num)]
            if en_twice_lp:
                d.insert(0, Plain(res_text))
            await app.sendFriendMessage(friend, MessageChain.create(d))
            moca_log(f"发送图片：{str(d)}", group=0, qq=friend.id)
            update_count(0, lp_name)
            return


@bcc.receiver(NewFriendRequestEvent)
async def new_friend_handler(event: NewFriendRequestEvent):
    print("New friend:", event.supplicant)
    await event.accept(message="Hello, I am moca.")


if __name__ == "__main__":
    try:
        init_dm()
        gapp.launch_blocking()
    except KeyboardInterrupt:
        print('Terminating App...')
        sys.exit()