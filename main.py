import asyncio
import platform
import re

from graia.application.event.mirai import MemberJoinEvent, BotInvitedJoinGroupRequestEvent, BotJoinGroupEvent, \
    MemberLeaveEventKick

from function import *
from graia.application import GraiaMiraiApplication, Session, GroupMessage, MessageChain, Group, Member
from graia.application.group import MemberPerm
from graia.application.message.elements.internal import Plain, At, Image
from graia.broadcast import Broadcast, ExecutionStop
from graia.broadcast.builtin.decoraters import Depend

from functions.pan import pan_change, buy_pan, eat_pan
from functions.signin import user_signin

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


#   判断是否At了除机器人外任意成员
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
], priority=2)
async def group_at_bot_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if get_group_flag(group.id):
        return
    text = message.asDisplay().replace(" ", "").lower()

    #   语音
    #   权限：成员
    #   是否At机器人：是
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

    #   统计次数
    #   权限：成员
    #   是否At机器人：是
    if contains("统计次数", "次数统计", text):
        if is_in_cd(group.id, "replyHelpCD"):
            return
        update_cd(group.id, "replyHelpCD")
        sorted_keyword_list = sort_dict(fetch_group_count(group.id))
        pic_path = create_dict_pic(sorted_keyword_list, f'{group.id}_count', '次数', sort_by_value=True)
        await app.sendGroupMessage(group, MessageChain.create([
            Image.fromLocalFile(pic_path)]
        ))
        set_group_flag(group.id)
        return

    #   统计lp排行
    #   权限：成员
    #   是否At机器人：是
    if contains("lp排行", text.replace("老婆", "lp")):
        if is_in_cd(group.id, "replyHelpCD"):
            return
        update_cd(group.id, "replyHelpCD")
        lp_list_dict = lp_list_rank()
        pic_path = create_dict_pic(lp_list_dict, 'lp_list_rank', '人数（前十）')
        await app.sendGroupMessage(group, MessageChain.create([
            Image.fromLocalFile(pic_path)]
        ))
        set_group_flag(group.id)
        return

    #   查看关键词列表
    #   权限：成员
    #   是否At机器人：是
    if "关键词" in text:
        if is_in_cd(group.id, "replyHelpCD"):
            return
        update_cd(group.id, "replyHelpCD")
        sorted_keyword_list = sort_dict(fetch_group_keyword(group.id))
        pic_path = create_dict_pic(sorted_keyword_list, f'{group.id}_key', '关键词')
        await app.sendGroupMessage(group, MessageChain.create([
            Image.fromLocalFile(pic_path)
        ]))
        set_group_flag(group.id)
        return

    #   查看图片数量
    #   权限：成员
    #   是否At机器人：是
    if "图片数量" in text:
        if is_in_cd(group.id, "replyHelpCD"):
            return
        update_cd(group.id, "replyHelpCD")
        count_list = sort_dict(fetch_picture_count(group.id))
        pic_path = create_dict_pic(count_list, f'{group.id}_piccount', '图片数量', sort_by_value=True)
        await app.sendGroupMessage(group, MessageChain.create([
            Image.fromLocalFile(pic_path)
        ]))
        set_group_flag(group.id)
        return

    #   签到
    #   权限：成员
    #   是否At机器人：是
    if contains("签到", text) and exp_enabled(group.id):
        res = await user_signin(member.id)
        await app.sendGroupMessage(group, res)
        set_group_flag(group.id)
        return


# Manager的群消息监听器
@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode),
    Depend(judge_manager),
    Depend(judge_superman)
], priority=3)
async def group_manager_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group):
    if get_group_flag(group.id):
        return

    text = message.asDisplay().replace(" ", "").lower()

    #   设置图片cd
    #   权限：管理员/群主
    #   是否At机器人：否
    if text.startswith("设置图片cd") and len(text) > 6:
        paras = text[6:]
        try:
            sec = int(paras.rstrip("秒").rstrip("s"))
            if sec < 5:
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain(f"错误：最短图片cd5秒")
                ]))
                return
            update_config(group.id, "replyCD", sec)
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"当前图片cd：{sec}秒")
            ]))
        except ValueError:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("错误：参数错误\n示例：设置图片cd20秒")
            ]))
        set_group_flag(group.id)
        return

    #   设置复读cd
    #   权限：管理员/群主
    #   是否At机器人：否
    if text.startswith("设置复读cd") and len(text) > 6:
        paras = text[6:]
        try:
            sec = int(paras.rstrip("秒").rstrip("s"))
            if sec < 120:
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain(f"错误：最短复读cd120秒")
                ]))
                return
            update_config(group.id, "repeatCD", sec)
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"当前复读cd：{sec}秒")
            ]))
        except ValueError:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("错误：参数错误\n示例：设置复读cd20秒")
            ]))
        set_group_flag(group.id)
        return

    #   设置复读概率
    #   权限：管理员/群主
    #   是否At机器人：否
    if text.startswith("设置复读概率") and len(text) > 6:
        paras = text[6:]
        try:
            chance = int(paras.rstrip("%"))
            if not 0 <= chance <= 100:
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain(f"错误：概率应在0%-100%范围内")
                ]))
                return
            update_config(group.id, "repeatChance", chance)
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"当前复读概率：{chance}%")
            ]))
        except ValueError:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("错误：参数错误\n示例：设置复读概率25%")
            ]))
        set_group_flag(group.id)
        return

    #   添加关键词
    #   权限：管理员/群主
    #   是否At机器人：否
    if (text.startswith("增加关键词") or text.startswith("添加关键词")) and len(text) > 5:
        paras = text[5:].replace('，', ',').split(',')
        if not len(paras) == 2:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("错误：参数错误\n示例：添加关键词志崎樺音，来点non酱")
            ]))
            return

        if check_para(paras[0]) and check_para(paras[1]):
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("错误：参数中禁止含有特殊符号!")
            ]))
            return

        res = append_keyword(group.id, paras)
        if res == 0:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"向{paras[0]}中添加了关键词：{paras[1]}")
            ]))
        elif res == -1:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"错误：关键词列表中未找到{paras[0]}")
            ]))
        elif res == -2:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"错误：{paras[0]}的关键词列表中已存在能够识别 {paras[1]} 的关键词了")
            ]))
        set_group_flag(group.id)
        return

    #   删除关键词
    #   权限：管理员/群主
    #   是否At机器人：否
    if text.startswith("删除关键词"):
        paras = text[5:].replace('，', ',').split(',')
        if not len(paras) == 2:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("错误：参数错误\n示例：删除关键词志崎樺音，来点non酱")
            ]))
            return

        res = remove_keyword(group.id, paras)
        if res == 0:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"删除了{paras[0]}中的关键词：{paras[1]}")
            ]))
        elif res == -1:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"错误：关键词列表中未找到{paras[0]}")
            ]))
        elif res == -2:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"错误：{paras[0]}的关键词列表中未找到关键词 {paras[1]}")
            ]))
        set_group_flag(group.id)
        return

    #   查看当前参数
    #   权限：管理员/群主
    #   是否At机器人：否
    if text == "查看当前参数":
        to_reply_text = f"""当前参数：
图片cd：{fetch_config(group.id, "replyCD")}秒
复读cd：{fetch_config(group.id, "repeatCD")}秒
复读概率：{fetch_config(group.id, "repeatChance")}%"""
        await app.sendGroupMessage(group, MessageChain.create([
            Plain(to_reply_text)
        ]))
        set_group_flag(group.id)
        return


# 常规消息处理器
@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode)
], priority=4)
async def group_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if get_group_flag(group.id):
        return

    text = message.asDisplay().replace(' ', '').lower()

    #   查询使用说明
    #   权限：成员
    #   是否At机器人：否
    if contains("使用说明", "help", text):
        await app.sendGroupMessage(group, user_manual())
        set_group_flag(group.id)
        return

    #   设置lp
    #   权限：成员
    #   是否At机器人：否
    if text.replace("我", "w").replace("老婆", "lp").startswith("wlp是"):
        if not len(text) > 4:
            return
        lp_name = text[4:]
        res = user_set_lp(member.id, group.id, lp_name)
        if res[0]:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"用户{member.name}设置lp为：{res[1]}")
            ]))
        else:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("az，这个群没有找到你lp呢...")
            ]))

    #   发送lp
    #   权限：成员
    #   是否At机器人：否
    if not is_in_cd(group.id, "replyCD"):
        if ("来点" in text) and ("lp" in text.replace("老婆", "lp")):
            twice_lp = text.startswith("多")
            lp_name = fetch_user_lp(member.id, group.id)

            if lp_name == "NOT_SET":
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain("az，似乎你还没有设置lp呢~\n用”wlp是xxx“来设置一个吧~\n发送 @モカ 关键词 来查看可以设置的列表哦~")
                ]))
                return

            if lp_name == "NOT_FOUND":
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain("az，这个群似乎看不了你lp呢...")
                ]))
                return

            pic_num = 1
            res_text = ""
            if twice_lp:
                res = pan_change(member.id, -TWICE_LP_PAN_AMOUNT)
                if res[0]:
                    pic_num = 2
                    res_text = f"面包-{TWICE_LP_PAN_AMOUNT}，还剩{res[1]}个面包~"
                else:
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain("az，你的面包不够了呢QAQ")
                    ]))
                    return

            file_list = rand_pic(lp_name, pic_num)
            d = [Image.fromLocalFile(e) for e in file_list]
            if twice_lp:
                d.insert(0, Plain(res_text))
            await app.sendGroupMessage(group, MessageChain.create(d))
            update_count(group.id, lp_name)
            set_group_flag(group.id)
            return

    #   遍历查询是否在关键词列表中并发送图片
    #   权限：成员
    #   是否At机器人：否
    if not is_in_cd(group.id, "replyCD"):
        group_keywords = fetch_group_keyword(group.id)
        twice_lp = text.startswith("多")
        pic_num = 1
        res_text = ""
        if twice_lp:
            res = pan_change(member.id, -TWICE_LP_PAN_AMOUNT)
            if res[0]:
                pic_num = 2
                res_text = f"面包-{TWICE_LP_PAN_AMOUNT}，还剩{res[1]}个面包~"
            else:
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain("az，你的面包不够了呢QAQ")
                ]))
                return

        req_name = ""
        key_found = False

        for name, key_regex in group_keywords.items():
            if not key_regex == '':
                p = re.fullmatch(key_regex, text)
                if p:
                    key_found = True
                    req_name = name
                    break

        if not key_found:
            for name, key_regex in group_keywords.items():
                if not key_regex == '':
                    p = re.findall(key_regex, text)
                    if p:
                        key_found = True
                        req_name = name
                        break

        if key_found:
            file_list = rand_pic(req_name, pic_num)
            d = [Image.fromLocalFile(e) for e in file_list]
            if twice_lp:
                d.insert(0, Plain(res_text))
            await app.sendGroupMessage(group, MessageChain.create(d))
            update_count(group.id, req_name)
            set_group_flag(group.id)
            update_cd(group.id, "replyCD")
            return

    # 实验功能
    if exp_enabled(group.id):
        #   买面包
        #   权限：成员
        #   是否At机器人：否
        if text == '买面包' or text == '来点面包':
            res = await buy_pan(member.id)
            await app.sendGroupMessage(group, res)
            set_group_flag(group.id)
            return

        #   吃面包
        #   权限：成员
        #   是否At机器人：否
        if text == '吃面包' or text == '恰面包':
            res = await eat_pan(member.id)
            await app.sendGroupMessage(group, res)
            set_group_flag(group.id)
            return


# 超管处理器
@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode),
    Depend(judge_superman)
], priority=5)
async def group_superman_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group):
    if get_group_flag(group.id):
        return
    pass


# At了除机器人外的任意成员的监听器
@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode),
    Depend(judge_at_others)
], priority=6)
async def group_at_others_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if get_group_flag(group.id):
        return

    at_data = message.get(At)[0].dict()
    at_target: int = at_data['target']

    text = message.asDisplay().replace(' ', '').lower()

    if contains("换lp次数", text):
        clp_times = fetch_clp_times(at_target)
        if clp_times == 0:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"{member.name} 还没有换过lp呢~")
            ]))
        else:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"{member.name} 换了{clp_times}次lp了哦~")
            ]))


# 复读机
@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode)
], priority=15)
async def group_repeater_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group):
    if get_group_flag(group.id):
        return
    res = moca_repeater(group.id, message)
    if res[0]:
        if res[1]:
            await app.sendGroupMessage(group, MessageChain.create([
                Image.fromLocalFile(os.path.join(config.resource_path, "fudu", "fudu.jpg"))
            ]))
        await app.sendGroupMessage(group, message.asSendable())
        update_cd(group.id, "repeatCD")


# 重置群组标志位/每300秒更新一次图片列表
@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode)
], priority=16)
async def flag_handler(group: Group):
    # update files list
    if get_timestamp_now() - gol.get_value('file_list_update_time') > 300:
        gol.set_value('file_list_update_time', get_timestamp_now())
        if platform.system() == 'Windows':
            os.system('start python update_db.py')
        else:
            os.system('python update_db.py &')

    # Reset group flag
    gol.set_value(f'group_{group.id}_processed', False)


@bcc.receiver(MemberJoinEvent, headless_decoraters=[
    Depend(judge_debug_mode)
])
async def group_welcome_join_handler(app:GraiaMiraiApplication, group: Group, member: Member):
    #   欢迎新成员加入
    if fetch_config(group.id, "welcomeNewMemberJoin") == 1:
        await app.sendGroupMessage(group, MessageChain.create([
            At(target=member.id),
            Plain(f' 欢迎加入{group.name}！')
        ]))


@bcc.receiver(BotInvitedJoinGroupRequestEvent, headless_decoraters=[
    Depend(judge_debug_mode)
])
async def superman_invite_join_group(event: BotInvitedJoinGroupRequestEvent):
    # 自动接收邀请
    if is_superman(event.supplicant):
        await event.accept("Auto accept")
    else:
        await event.reject("Auto reject")


@bcc.receiver(BotJoinGroupEvent, headless_decoraters=[
    Depend(judge_debug_mode)
])
async def bot_join_group(app: GraiaMiraiApplication, group: Group):
    # 自动发送使用说明
    await app.sendGroupMessage(group, MessageChain.create([
        Plain(f'大家好，我是mocaBot\n使用说明：http://mocabot.cn/')
    ]))


@bcc.receiver(MemberLeaveEventKick, headless_decoraters=[
    Depend(judge_debug_mode)
])
async def superman_kick_from_group(app: GraiaMiraiApplication, member: Member, group: Group):
    # superman被踢自动退出
    if is_superman(member.id):
        print(f"Superman leaving {group.id}")
        await app.quit(group)


if __name__ == "__main__":
    try:
        init_mocabot()
        gapp.launch_blocking()
    except KeyboardInterrupt:
        print('Terminating App...')
