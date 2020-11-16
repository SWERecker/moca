import asyncio
import re
from function import *
from graia.application import GraiaMiraiApplication, Session, GroupMessage, MessageChain, Group, Member
from graia.application.group import MemberPerm
from graia.application.message.elements.internal import Plain, At, Image
from graia.broadcast import Broadcast, ExecutionStop
from graia.broadcast.builtin.decoraters import Depend

from functions.pan import pan_change

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
            Image.fromLocalFile(os.path.join(config.temp_path, f'{group.id}_count.png'))]
        ))
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
], priority=3)
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
async def group_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
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


# 超管处理器
@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode)
], priority=15)
async def group_repeat_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group):
    if get_group_flag(group.id):
        return
    print('do repeat process')


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
