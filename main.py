import asyncio
import platform
import sys

from graia.application.event.mirai import MemberJoinEvent, BotInvitedJoinGroupRequestEvent, BotJoinGroupEvent, \
    MemberLeaveEventKick

from function import *
from graia.application import GraiaMiraiApplication, Session, GroupMessage, MessageChain, Group, Member
from graia.application.group import MemberPerm
from graia.application.message.elements.internal import Plain, At, Image
from graia.broadcast import Broadcast, ExecutionStop
from graia.broadcast.builtin.decoraters import Depend

from functions.baidu_trans import baidu_translate
from functions.draw import draw_lot
from functions.pan import pan_change, buy_pan, eat_pan, twice_lp
from functions.random_song import random_song
from functions.signin import user_signin
debug_mode = os.path.isfile("debug")
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


TWICE_LP_PAN_AMOUNT = 3
UPLOAD_PHOTO_PAN_AMOUNT = 1


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

    if cfg_enabled(group.id, "pan"):
        #   语音
        #   权限：成员
        #   是否At机器人：是
        if contains("说话", "语音", text):
            if is_in_user_cd(member.id, "voice"):
                return
            result = pan_change(member.id, -1)
            if result[0]:
                voice_file = random.choice(os.listdir(os.path.join('resource', 'voice')))
                with open(os.path.join('resource', 'voice', voice_file), 'rb')as voice_bin_file:
                    voice = await app.uploadVoice(voice_bin_file)
                await app.sendGroupMessage(group, MessageChain.create([voice]))
                update_user_cd(member.id, "voice", 10)
            else:
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain("要~给~摩~卡~酱~面~包~才~跟~你~说~话~哦~")
                ]))
            set_group_flag(group.id)
            return


# At了除机器人外的任意成员的监听器
@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode),
    Depend(judge_at_others)
], priority=3)
async def group_at_others_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if get_group_flag(group.id):
        return

    at_data = message.get(At)[0].dict()
    at_target: int = at_data['target']

    text = message.asDisplay().replace(' ', '').lower()

    if contains("换lp次数", text.replace("老婆", "lp")):
        clp_times = fetch_clp_times(at_target)
        if clp_times == 0:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"{member.name} 还没有换过lp呢~")
            ]))
        else:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"{member.name} 换了{clp_times}次lp了哦~")
            ]))
        set_group_flag(group.id)
        return


# Manager的群消息监听器
@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode),
    Depend(judge_manager)
], priority=4)
async def group_manager_message_handler(
        app: GraiaMiraiApplication,
        message: MessageChain,
        group: Group,
        member: Member
):
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
                    Plain(f"错误：最短图片cd 5秒")
                ]))
                return
            update_config(group.id, "replyCD", sec)
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"当前图片cd：{sec}秒")
            ]))
        except ValueError:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("错误：参数错误\n示例【设置图片cd20秒】")
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
                    Plain(f"错误：最短复读cd 120秒")
                ]))
                return
            update_config(group.id, "repeatCD", sec)
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"当前复读cd：{sec}秒")
            ]))
        except ValueError:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("错误：参数错误\n示例【设置复读cd20秒】")
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
                Plain("错误：参数错误\n示例【设置复读概率25%】")
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
                Plain("错误：参数错误\n示例【添加关键词志崎樺音，来点non酱】")
            ]))
            return

        if check_para(paras[0]) or check_para(paras[1]):
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("错误：参数中禁止含有特殊符号!")
            ]))
            return

        await app.sendGroupMessage(group, append_keyword(group.id, paras))
        set_group_flag(group.id)
        return

    #   删除关键词
    #   权限：管理员/群主
    #   是否At机器人：否
    if text.startswith("删除关键词"):
        paras = text[5:].replace('，', ',').split(',')
        if not len(paras) == 2:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("错误：参数错误\n示例【删除关键词志崎樺音，来点non酱】")
            ]))
            return

        await app.sendGroupMessage(group, remove_keyword(group.id, paras))
        set_group_flag(group.id)
        return

    #   查看当前参数
    #   权限：管理员/群主
    #   是否At机器人：否
    if text == "查看当前参数":
        to_reply_text = "当前参数：\n" \
                        f"图片cd：{fetch_config(group.id, 'replyCD')}秒\n" \
                        f"复读cd：{fetch_config(group.id, 'repeatCD')}秒\n" \
                        f"复读概率：{fetch_config(group.id, 'repeatChance')}%"
        await app.sendGroupMessage(group, MessageChain.create([
            Plain(to_reply_text)
        ]))
        set_group_flag(group.id)
        return

    #   打开/关闭功能
    #   权限：管理员/群主
    #   是否At机器人：否
    if text.startswith("打开") or text.startswith("关闭"):
        op = True if text[:2] == "打开" else False
        if text[2:] == "实验功能":
            update_config(group.id, "exp", int(op))
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"{group.id}已{text[:2]}实验功能")
            ]))
            set_group_flag(group.id)
            return

        if text[2:] == "面包功能":
            update_config(group.id, "pan", int(op))
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"{group.id} 已{text[:2]}面包功能")
            ]))
            set_group_flag(group.id)
            return

        if text[2:] == "随机选歌":
            update_config(group.id, "random", int(op))
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"{group.id} 已{text[:2]}随机选歌功能")
            ]))
            set_group_flag(group.id)
            return

        if text[2:] == "翻译功能":
            update_config(group.id, "trans", int(op))
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"{group.id} 已{text[:2]}翻译功能")
            ]))
            set_group_flag(group.id)
            return

    # 超管管理指令
    if is_superman(member.id):
        pass


# 常规消息处理器
@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode)
], priority=5)
async def group_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if get_group_flag(group.id):
        return

    text = message.asDisplay().replace(' ', '')

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

        if contains("谁", "?", lp_name.replace("？", "?")):
            lp_name = fetch_user_lp(member.id, group.id)
            if lp_name == "NOT_SET" or lp_name == "NOT_FOUND":
                await app.sendGroupMessage(group, MessageChain.create([
                    At(target=member.id),
                    Plain(f" 你还没有设置lp或者你的lp没在这个群呢~")
                ]))
            else:
                await app.sendGroupMessage(group, MessageChain.create([
                    At(target=member.id),
                    Plain(f" 你设置的lp是：{lp_name}")
                ]))
            set_group_flag(group.id)
            return

        res = user_set_lp(member.id, group.id, lp_name)
        if res[0]:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"用户{member.name}设置lp为：{res[1]}")
            ]))
        else:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("az，这个群没有找到你lp呢...")
            ]))
        set_group_flag(group.id)
        return

    #   发送lp
    #   权限：成员
    #   是否At机器人：否
    if not is_in_cd(group.id, "replyCD"):
        if ("来点" in text) and ("lp" in text.replace("老婆", "lp")):
            en_twice_lp = text.startswith("多")
            lp_name = fetch_user_lp(member.id, group.id)

            if lp_name == "NOT_SET":
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain("az，似乎你还没有设置lp呢~\n用【wlp是xxx】来设置一个吧~\n发送【@モカ 关键词】来查看可以设置的列表哦~")
                ]))
                return

            if lp_name == "NOT_FOUND":
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain("az，这个群似乎看不了你lp呢...")
                ]))
                return

            pic_num = 1
            res_text = ""
            if en_twice_lp:
                res = twice_lp(group.id, member.id)
                pic_num = res[0]
                if not res[1] == -1:
                    res_text = f"摩卡吃掉了3个面包，你还剩{res[1]}个面包哦~"
                else:
                    res_text = "呜呜呜，面包不够吃啦~"
                    en_twice_lp = False
            d = [Image.fromLocalFile(e) for e in rand_pic(lp_name, pic_num)]
            if en_twice_lp:
                d.insert(0, Plain(res_text))
            await app.sendGroupMessage(group, MessageChain.create(d))
            update_count(group.id, lp_name)
            set_group_flag(group.id)
            return

        #   提交图片
        #   权限：成员
        #   是否At机器人：否
        if text.startswith('提交图片') and len(text) > 4:
            res = await upload_photo(group.id, message)
            await app.sendGroupMessage(group, res)
            set_group_flag(group.id)
            return

        #   随机选歌
        #   权限：成员
        #   是否At机器人：否
        #   关联Group Config中的"random"参数
        if text.startswith('随机选歌'):
            if cfg_enabled(group.id, "random"):
                res = await random_song(member.id, text.lower())
                await app.sendGroupMessage(group, res)
                set_group_flag(group.id)
                return

        #   翻译
        #   权限：成员
        #   是否At机器人：否
        #   关联Group Config中的"trans"参数
        if text.startswith('翻译'):
            if cfg_enabled(group.id, "trans"):
                res = await baidu_translate(message)
                await app.sendGroupMessage(group, res)
                set_group_flag(group.id)
                return

        #   青年大学习
        #   权限：成员
        #   是否At机器人：否
        if contains("青年大学习", text):
            try:
                with open(os.path.join(config.resource_path, "qndxx.txt"), "r", encoding="utf-8")as f:
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f.read())
                    ]))
            except FileNotFoundError:
                pass
            set_group_flag(group.id)
            return

        #   换lp次数
        #   权限：成员
        #   是否At机器人：否
        if contains("换lp次数", text.replace("老婆", "lp")):
            clp_times = fetch_clp_times(member.id)
            if clp_times == 0:
                await app.sendGroupMessage(group, MessageChain.create([
                    At(target=member.id),
                    Plain(f" 你还没有换过lp呢~")
                ]))
            else:
                await app.sendGroupMessage(group, MessageChain.create([
                    At(target=member.id),
                    Plain(f" 你换了{clp_times}次lp了哦~")
                ]))
            set_group_flag(group.id)
            return

    #   遍历查询是否在关键词列表中并发送图片
    #   权限：成员
    #   是否At机器人：否
    #   关联Group Config中的"pan"参数
    if not is_in_cd(group.id, "replyCD"):
        group_keywords = fetch_group_keyword(group.id)
        en_twice_lp = text.startswith("多")
        req_name = ""
        res_text = ""
        pic_num = 1
        key_found = False
        text = text.lstrip("多")

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
            if en_twice_lp:
                res = twice_lp(group.id, member.id)
                pic_num = res[0]
                if not res[1] == -1:
                    res_text = f"摩卡吃掉了3个面包，你还剩{res[1]}个面包哦~"
                else:
                    res_text = "呜呜呜，面包不够吃啦~"
            file_list = rand_pic(req_name, pic_num)
            d = [Image.fromLocalFile(e) for e in file_list]
            if en_twice_lp:
                d.insert(0, Plain(res_text))
            await app.sendGroupMessage(group, MessageChain.create(d))
            update_count(group.id, req_name)
            set_group_flag(group.id)
            update_cd(group.id, "replyCD")
            return

    # 面包功能开启
    # 关联Group Config中的"pan"参数
    if cfg_enabled(group.id, "pan"):
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

        #   喂面包
        #   权限：成员
        #   是否At机器人：否
        if text == '喂面包':
            pass
            set_group_flag(group.id)
            return

        #   签到
        #   权限：成员
        #   是否At机器人：否
        if text == "签到":
            res = await user_signin(member.id)
            await app.sendGroupMessage(group, res)
            set_group_flag(group.id)
            return

        #   抽签
        #   权限：成员
        #   是否At机器人：是
        if text == "抽签":
            res = await draw_lot(group.id, member.id)
            await app.sendGroupMessage(group, res)
            set_group_flag(group.id)
            return


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
            callback = await app.sendGroupMessage(group, MessageChain.create([
                Image.fromLocalFile(os.path.join(config.resource_path, "fudu", "fudu.jpg"))
            ]))
            while callback is None:
                pass
            time.sleep(0.8)
            await app.sendGroupMessage(group, message.asSendable())
            await app.sendGroupMessage(group, message.asSendable())
        else:
            await app.sendGroupMessage(group, message.asSendable())
        update_cd(group.id, "repeatCD")


# 重置群组标志位/每300秒更新一次图片列表
@bcc.receiver(GroupMessage, headless_decoraters=[
    Depend(judge_debug_mode)
], priority=16)
async def flag_handler(group: Group):
    # update files list
    if get_timestamp_now() - gol.get_value('file_list_update_time') > 60:
        print("updating file list")
        gol.set_value('file_list_update_time', get_timestamp_now())
        if platform.system() == 'Windows':
            pass
            # os.system('start python update_db.py')
        else:
            pass
            # os.system('python update_db.py &')
        init_mocabot()

    # Reset group flag
    gol.set_value(f'group_{group.id}_processed', False)


@bcc.receiver(MemberJoinEvent, headless_decoraters=[
    Depend(judge_debug_mode)
])
async def group_welcome_join_handler(app: GraiaMiraiApplication, group: Group, member: Member):
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
        Plain(f'大家好，我是moca\n使用说明：http://mocabot.cn/\n请仔细查看使用说明并按照格式使用哦！')
    ]))


@bcc.receiver(MemberLeaveEventKick, headless_decoraters=[
    Depend(judge_debug_mode)
])
async def superman_kick_from_group(
        app: GraiaMiraiApplication,
        group: Group,
        event: MemberLeaveEventKick
):
    # superman被踢自动退出
    if is_superman(event.member.id):
        print(f"Superman leaving {group.id}, Quitting")
        await app.quit(group)


if __name__ == "__main__":
    try:
        init_mocabot()
        gapp.launch_blocking()
    except KeyboardInterrupt:
        print('Terminating App...')
        sys.exit()
