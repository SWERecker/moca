import asyncio
import re
from function import *
from graia.application import GraiaMiraiApplication, Session, GroupMessage, MessageChain, Group, Member
from graia.application.group import MemberPerm
from graia.application.message.elements.internal import Plain, At, Image
from graia.broadcast import Broadcast, ExecutionStop
from graia.broadcast.builtin.decoraters import Depend

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
TWICE_LP_PAN_AMOUNT = 3


#   判断是否开启Debug模式
def judge_debug_mode(group: Group):
    if debug_mode:
        if not group.id == 907274961:
            raise ExecutionStop()


#   判断是否@机器人
def judge_at_bot(message: MessageChain):
    at_bot = False
    if At in message:
        at_data = message.get(At)[0].dict()
        at_target: int = at_data['target']
        at_bot: bool = at_target == config.bot_id
    if not at_bot:
        raise ExecutionStop()


#   判断是否是普通成员
def judge_at_others(message: MessageChain):
    at_others = False
    if At in message:
        at_data = message.get(At)[0].dict()
        at_target: int = at_data['target']
        at_others: bool = not at_target == config.bot_id
    if not at_others:
        raise ExecutionStop()


#   判断是否是管理员
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


@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode)
], priority=1)
async def group_init_handler(group: Group):
    init_group(group.id)


# At了机器人的群消息监听器
@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode),
    Depend(judge_at_bot)
], priority=1)
async def group_at_bot_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if get_group_flag(group.id):
        return
    text = message.asDisplay().replace(" ", "").lower()

    if contains("说话", "语音", text):
        if is_in_user_cd(member.id, "voice"):
            return
        voice_file = random.choice(os.listdir(os.path.join('resource', 'voice')))
        with open(os.path.join('resource', 'voice', voice_file), 'rb')as voice_bin_file:
            voice = await app.uploadVoice(voice_bin_file)
        await app.sendGroupMessage(group, MessageChain.create([voice]))
        update_user_cd(member.id, "voice", 10)
        set_group_flag(group.id)
        return

    if contains("统计次数", "次数统计", text):
        if is_in_cd(group.id, "replyHelpCD"):
            return
        update_cd(group.id, "replyHelpCD")
        sorted_keyword_list = sort_dict(fetch_group_count(group.id))
        create_dict_pic(sorted_keyword_list, f'{group.id}_count', '次数', sort_by_value=True)
        await app.sendGroupMessage(group, MessageChain.create([
            Image.fromLocalFile(os.path.join(config.temp_path, f'{group.id}_count.png'))
        ]))
        set_group_flag(group.id)
        return


# Manager的群消息监听器
@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode),
    Depend(judge_manager)
], priority=2)
async def group_manager_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group):
    if get_group_flag(group.id):
        return
    print('Manager Message')


# 常规消息处理器
@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode)
], priority=3)
async def group_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if get_group_flag(group.id):
        return

    text = message.asDisplay().replace(' ', '').lower()

    if contains("使用说明", "help", text):
        await app.sendGroupMessage(group, user_manual())
        set_group_flag(group.id)

    #   遍历查询是否在关键词列表中并发送图片
    #   权限：成员
    #   是否At机器人：否
    if not is_in_cd(group.id, "replyCD"):
        group_keywords = fetch_group_keyword(group.id)
        twice_lp = text.startswith("多")

        if twice_lp:
            pass
            pic_num = 2
        else:
            pic_num = 1

            # 判断面包是否足够
            # if not enough:
            #     return  # not enough
            # else:
            #     # 面包-3,获取剩余面包

        for name, key_regex in group_keywords.items():
            p = re.fullmatch(key_regex, text)
            if p:
                file_list = rand_pic(name, pic_num)
                d = [Image.fromLocalFile(e) for e in file_list]
                await app.sendGroupMessage(group, MessageChain.create(d))
                update_count(group.id, name)
                set_group_flag(group.id)
                return

        for name, key_regex in group_keywords.items():
            p = re.findall(key_regex, text)
            if p:
                file_list = rand_pic(name, pic_num)
                d = [Image.fromLocalFile(e) for e in file_list]
                await app.sendGroupMessage(group, MessageChain.create(d))
                update_count(group.id, name)
                set_group_flag(group.id)
                return

    # for keys in group_keywords:  # 在字典中遍历查找
    #     for e in range(len(group_keywords[keys])):  # 遍历名称
    #         if text == group_keywords[keys][e]:  # 若命中名称
    #             if not is_in_cd(group.id, "replyCD") or is_superman(member.id):  # 判断是否在回复图片的cd中
    #                 pic_name = rand_pic(keys)
    #                 await app.sendGroupMessage(group, MessageChain.create([
    #                     Image.fromLocalFile(os.path.join(config.pic_path, keys, pic_name))
    #                 ]))
    #                 # await update_count(group.id, keys)  # 更新统计次数
    #                 update_cd(group.id, "replyCD")  # 更新cd
    #             return
    #
    # for keys in group_keywords:  # 在字典中遍历查找
    #     for e in range(len(group_keywords[keys])):  # 遍历名称
    #         if group_keywords[keys][e] in text:  # 若命中名称
    #             if not is_in_cd(group.id, "replyCD") or is_superman(member.id):  # 判断是否在回复图片的cd中
    #                 twice_lp = text.startswith("多")
    #                 if not exp_enabled(group.id):
    #                     twice_lp = False
    #                 if twice_lp:
    #                     # status = consume_pan(member.id, r, twice_lp_pan_amount, PAN_TWICE_LP_CONSUME)
    #                     status = False, False
    #                     if status[0]:
    #                         pics = [rand_pic(keys), rand_pic(keys)]
    #                         await app.sendGroupMessage(group, MessageChain.create([
    #                             Plain(f"你吃掉了{twice_lp_pan_amount}个面包，还剩{status[1]}个面包哦~"),
    #                             Image.fromLocalFile(os.path.join(config.pic_path, keys, pics[0])),
    #                             Image.fromLocalFile(os.path.join(config.pic_path, keys, pics[1]))
    #                         ]))
    #                     else:
    #                         if status[1] == 0:
    #                             stat_text = "你没有面包了呢~"
    #                         else:
    #                             stat_text = f"只剩{status[1]}个面包了呢~"
    #                         await app.sendGroupMessage(group, MessageChain.create([
    #                             Plain(f"呜呜呜，面包不够了~你需要{twice_lp_pan_amount}个面包，但是{stat_text}")
    #                         ]))
    #                 else:
    #                     pic_name = rand_pic(keys)
    #                     await app.sendGroupMessage(group, MessageChain.create([
    #                         Image.fromLocalFile(os.path.join(config.pic_path, keys, pic_name))
    #                     ]))
    #                 # await update_count(group.id, keys)  # 更新统计次数
    #                 update_cd(group.id, "replyCD")  # 更新cd
    #             return


# 超管处理器
@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode),
    Depend(judge_superman)
], priority=4)
async def group_superman_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group):
    if get_group_flag(group.id):
        return
    print('Superman')


# At了除机器人外的任意成员的监听器
@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode),
    Depend(judge_at_others)
], priority=5)
async def group_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group):
    if get_group_flag(group.id):
        return
    at_data = message.get(At)[0].dict()
    at_target: int = at_data['target']

    await app.sendGroupMessage(group, MessageChain.create([
        Plain(f'At target: {at_target}')
    ]))


@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode)
], priority=16)
async def flag_handler(group: Group):
    # Reset group flag
    gol.set_value(f'group_{group.id}_processed', False)


if __name__ == "__main__":
    try:
        init_mocabot()
        gapp.launch_blocking()
    except KeyboardInterrupt:
        print('Terminating App...')
