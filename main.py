import asyncio
import json
import time

from graia.application import GraiaMiraiApplication, Session, GroupMessage, MessageChain, Group, Member
from graia.application.group import MemberPerm
from graia.application.message.elements.internal import Plain, At
from graia.broadcast import Broadcast, ExecutionStop
from graia.broadcast.builtin.decoraters import Depend

import plains
from plains import *
from function import is_superman, contains, is_in_user_cd, update_user_cd, is_in_cd, update_cd, sort_dict, \
    create_dict_pic

loop = asyncio.get_event_loop()

bcc = Broadcast(loop=loop)
gapp = GraiaMiraiApplication(
    broadcast=bcc,
    connect_info=Session(
        host=config.server_addr,  # 填入 httpapi 服务运行的地址
        authKey=config.auth_key,  # 填入 authKey
        account=config.bot_id,  # 你的机器人的 qq 号
        websocket=True  # Graia 已经可以根据所配置的消息接收的方式来保证消息接收部分的正常运作.
    ),
    enable_chat_log=False
)

debug_mode = True


def judge_debug_mode(group: Group):
    if judge_debug_mode:
        if not group.id == 907274961:
            raise ExecutionStop()


def judge_at_bot(message: MessageChain):
    at_bot = False
    if At in message:
        at_data = message.get(At)[0].dict()
        at_target = at_data['target']
        at_bot = at_target == config.bot_id
    if not at_bot:
        raise ExecutionStop()


def judge_at_others(message: MessageChain):
    at_others = False
    if At in message:
        at_data = message.get(At)[0].dict()
        at_target: int = at_data['target']
        at_others: bool = not at_target == config.bot_id
    if not at_others:
        raise ExecutionStop()


def judge_manager(member: Member):
    manager = member.permission == MemberPerm.Administrator or \
              member.permission == MemberPerm.Owner or \
              is_superman(member.id)
    if not manager:
        raise ExecutionStop()


#   判断是否是超管
def judge_superman(member: Member):
    if not is_superman(member.id):
        raise ExecutionStop()


# At了机器人的群消息监听器
@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode),
    Depend(judge_at_bot)
])
async def group_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    text = message.asDisplay().replace(" ", "").lower()
    if contains("使用说明", "help", text):
        await app.sendGroupMessage(group, plains.user_manual())

    if contains("说话", "语音", text):
        if is_in_user_cd(member.id, "voice"):
            return
        voice_file = random.choice(os.listdir(os.path.join('resource', 'voice')))
        with open(os.path.join('resource', 'voice', voice_file), 'rb')as voice_bin_file:
            voice = await app.uploadVoice(voice_bin_file)
        await app.sendGroupMessage(group, MessageChain.create([
            voice
        ]))
        update_user_cd(member.id, "voice", 30)
        return

    if contains("统计次数", "次数统计", text):
        if is_in_cd(group.id, "replyHelpCD"):
            return
        update_cd(group.id, "replyHelpCD")
        sorted_keyword_list = sort_dict(json.loads(r.hget("COUNT", group.id)))
        create_dict_pic(sorted_keyword_list, f'{group.id}_count', '次数', sort_by_value=True)
        await app.sendGroupMessage(group, MessageChain.create([
            Image.fromLocalFile(os.path.join(config.temp_path, f'{group.id}_count.png'))
        ]))
        return


# At了除机器人外的任意成员的监听器
@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode),
    Depend(judge_at_others)
])
async def group_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group):
    at_data = message.get(At)[0].dict()
    at_target: int = at_data['target']

    await app.sendGroupMessage(group, MessageChain.create([
        Plain(f'At target: {at_target}')
    ]))


# Manager的群消息监听器
@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode),
    Depend(judge_manager)
])
async def group_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group):
    await app.sendGroupMessage(group, MessageChain.create([
        Plain('Manager Message')
    ]))


# 常规消息处理器
@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode)
])
async def group_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group):
    await app.sendGroupMessage(group, MessageChain.create([
        Plain('Normal Handler')
    ]))


# 超管处理器
@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode),
    Depend(judge_superman)
])
async def group_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group):
    await app.sendGroupMessage(group, MessageChain.create([
        Plain('Superman')
    ]))


if __name__ == "__main__":
    try:
        gapp.launch_blocking()
    except KeyboardInterrupt:
        print('Terminating App...')
