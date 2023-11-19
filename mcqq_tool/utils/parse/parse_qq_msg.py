"""
格式化频道消息
"""

from typing import Union

from nonebot.adapters.onebot.v11 import Bot as OneBot, GroupMessageEvent
from nonebot.adapters.qq.models import Member, Guild, Channel
from nonebot_plugin_guild_patch import GuildMessageEvent
from nonebot.adapters.qq import Bot as QQBot, MessageCreateEvent

from ...model.return_body import *
from ...config import plugin_config


async def _get_onebot_member_nickname(
        bot: OneBot,
        event: Union[GroupMessageEvent, GuildMessageEvent],
        user_id: Union[int, str]
) -> str:
    """
    获取 OneBot 群/频道成员昵称
    :param bot: OneBot
    :param event: 事件
    :param user_id: 成员QQ号/频道ID
    :return: 成员昵称
    """
    # 判断从 群/频道 获取成员信息
    if isinstance(event, GroupMessageEvent):
        # 如果获取发送者的昵称
        if event.user_id == int(user_id):
            # 如果群名片为空，则发送昵称
            return event.sender.card or event.sender.nickname
        # 如果获取其他人的昵称
        else:
            return (await bot.get_group_member_info(
                group_id=event.group_id,
                user_id=user_id,
                no_cache=True
            ))['nickname']
    elif isinstance(event, GuildMessageEvent):
        # 返回频道成员昵称
        if event.user_id == user_id:
            return event.sender.nickname
        else:
            return (await bot.get_guild_member_profile(
                guild_id=event.guild_id,
                user_id=user_id))['nickname']


async def get_qq_member_nickname(
        bot: QQBot,
        event: MessageCreateEvent,
        user_id: str
) -> str:
    """
    获取 QQ 群/频道成员昵称
    :return: 成员昵称
    """
    # 判断事件发送者是否为本人
    if event.author.id == user_id:
        return event.member.nick or event.author.username
    else:
        member: Member = await bot.get_member(guild_id=event.guild_id, user_id=user_id)
        return member.nick or member.user.username


async def parse_onebot_msg_to_basemodel(
        bot: OneBot,
        event: Union[GroupMessageEvent, GuildMessageEvent]
) -> WebSocketSendBody:
    """
    :param bot: OneBot
    :param event: 事件
    :return: WebSocketSendBody
    """
    websocket_send_body = WebSocketSendBody()
    websocket_send_body.message = []

    # 发送群聊名称
    if plugin_config.mc_qq_send_group_name:
        group_name = MessageItem()
        group_name.color = TextColor.GREEN
        if isinstance(event, GroupMessageEvent):
            group_name.msg_text = (await bot.get_group_info(group_id=event.group_id))['group_name']
        elif isinstance(event, GuildMessageEvent):
            guild_name = (await bot.get_guild_meta_by_guest(guild_id=event.guild_id))['guild_name']
            for per_channel in (await bot.get_guild_channel_list(guild_id=event.guild_id, no_cache=True)):
                if str(event.channel_id) == per_channel['channel_id']:
                    channel_name = per_channel['channel_name']
                    group_name.msg_text = f"{guild_name}丨{channel_name}"
                    break
        websocket_send_body.message.append(group_name)

    member_nickname = await _get_onebot_member_nickname(bot, event, event.user_id)

    sender_name = MessageItem()
    sender_name.msg_text = member_nickname + " "
    sender_name.color = TextColor.WHITE
    websocket_send_body.message.append(sender_name)

    sender_say = MessageItem()
    sender_say.msg_text = "说："
    sender_say.color = TextColor.GOLD
    websocket_send_body.message.append(sender_say)

    for msg in event.message:
        per_msg = MessageItem()
        per_msg.action_event = ActionEvent()

        # 文本
        if msg.type == "text":
            per_msg.msg_text = msg.data['text'].replace("\r", "").replace("\n", "\n * ")
            per_msg.color = TextColor.WHITE
        # 图片
        elif msg.type == "image":
            if plugin_config.mc_qq_chat_image_enable:
                per_msg.msg_text = str(ChatImageModel(url=msg.data['url'], name="图片"))
            else:
                per_msg.msg_text = "[图片]"
                per_msg.action_event.click_event_url = msg.data['url']
                per_msg.action_event.hover_event_text = "[查看图片]"
            per_msg.color = TextColor.AQUA
        # 表情
        elif msg.type == "face":
            per_msg.msg_text = '[表情]'
            per_msg.color = TextColor.YELLOW
        # 语音
        elif msg.type == "record":
            per_msg.msg_text = '[语音]'
            per_msg.color = TextColor.GREEN
        # 视频
        elif msg.type == "video":
            per_msg.msg_text = '[视频]'
            per_msg.action_event.click_event_url = msg.data['url']
            per_msg.action_event.hover_event_text = "[查看视频]"
            per_msg.color = TextColor.LIGHT_PURPLE
        # @
        elif msg.type == "at":
            # 获取被@ 群/频道 昵称
            at_member_nickname = await _get_onebot_member_nickname(bot, event, msg.data['qq'])
            per_msg.msg_text = f"@{at_member_nickname} "
            per_msg.color = TextColor.GREEN
        # share
        elif msg.type == "share":
            per_msg.msg_text = "[分享]"
            per_msg.action_event.click_event_url = msg.data['url']
            per_msg.action_event.hover_event_text = "[查看分享]"
            per_msg.color = TextColor.YELLOW
        # forward
        elif msg.type == "forward":
            # TODO 将合并转发消息拼接为字符串
            # 获取合并转发 await bot.get_forward_msg(message_id=event.message_id)
            per_msg.msg_text = '[合并转发]'
        else:
            per_msg.msg_text = f"[{msg.type}]"
            per_msg.color = TextColor.WHITE
        websocket_send_body.message.append(per_msg)
    return websocket_send_body


async def parse_qq_msg_to_basemodel(
        bot: QQBot,
        event: MessageCreateEvent
) -> WebSocketSendBody:
    """
    格式化 QQ频道 消息为 WebSocketSendBody
    :param bot:
    :param event:
    :return: WebSocketSendBody
    """
    websocket_send_body = WebSocketSendBody()
    websocket_send_body.message = []

    # 发送群聊名称
    if plugin_config.mc_qq_send_group_name:
        group_name = MessageItem()
        group_name.color = TextColor.GREEN
        guild: Guild = await bot.get_guild(guild_id=event.guild_id)
        channel: Channel = await bot.get_channel(channel_id=event.channel_id)
        group_name.msg_text = f"{guild.name}丨{channel.name}"
        websocket_send_body.message.append(group_name)

    member_nickname = await get_qq_member_nickname(bot, event, event.author.id)

    sender_name = MessageItem()
    sender_name.msg_text = member_nickname + " "
    sender_name.color = TextColor.WHITE
    websocket_send_body.message.append(sender_name)

    sender_say = MessageItem()
    sender_say.msg_text = "说："
    sender_say.color = TextColor.GOLD
    websocket_send_body.message.append(sender_say)

    for msg in event.get_message():
        per_msg = MessageItem()
        per_msg.action_event = ActionEvent()

        # 文本
        if msg.type == "text":
            per_msg.msg_text = msg.data['text'].replace("\r", "").replace("\n", "\n * ")
            per_msg.color = TextColor.WHITE
        # 表情
        elif msg.type == "emoji":
            per_msg.msg_text = '[表情]'
            per_msg.color = TextColor.YELLOW
        # @用户
        elif msg.type == "mention_user":
            per_msg.msg_text = f"@{await get_qq_member_nickname(bot, event, msg.data['user_id'])} "
            per_msg.color = TextColor.GREEN
        # @频道
        elif msg.type == "mention_channel":
            per_msg.msg_text = f"@{(await bot.get_channel(channel_id=event.channel_id)).name} "
            per_msg.color = TextColor.GREEN
        # @全体成员
        elif msg.type == "mention_everyone":
            per_msg.msg_text = f"@全体成员 "
            per_msg.color = TextColor.GREEN
        # 图片
        elif msg.type == "image" or "attachment":
            per_msg.color = TextColor.AQUA
            if plugin_config.mc_qq_chat_image_enable:
                img_url = msg.data['url'] if msg.data['url'].startswith("http") else f"http://{msg.data['url']}"
                per_msg.msg_text = str(ChatImageModel(url=img_url, name="图片"))
            else:
                per_msg.msg_text = "[图片]"
                per_msg.action_event.click_event_url = msg.data['url']
                per_msg.action_event.hover_event_text = "[查看图片]"
        # 视频
        else:
            per_msg.msg_text = f"[{msg.type}]"
            per_msg.color = TextColor.WHITE
        websocket_send_body.message.append(per_msg)
    return websocket_send_body


async def parse_onebot_rcon_msg_to_basemodel(
        bot: OneBot,
        event: Union[GroupMessageEvent, GuildMessageEvent]
) -> RconSendBody:
    """
    :param bot: OneBot
    :param event: 事件
    :return: RconSendBody
    """
    rcon_send_body = RconSendBody()

    prefix_component = RconTextComponent()
    prefix_component.text = "[MC_QQ] "
    prefix_component.color = TextColor.YELLOW
    rcon_send_body.message.append(prefix_component)

    if plugin_config.mc_qq_send_group_name:
        group_name_component = RconTextComponent()
        group_name_component.color = TextColor.AQUA

        if isinstance(event, GroupMessageEvent):
            group_name_component.text = f"[{(await bot.get_group_info(group_id=event.group_id))['group_name']}] "
        elif isinstance(event, GuildMessageEvent):
            guild_name = (await bot.get_guild_meta_by_guest(guild_id=event.guild_id))['guild_name']
            for per_channel in (await bot.get_guild_channel_list(guild_id=event.guild_id, no_cache=True)):
                if str(event.channel_id) == per_channel['channel_id']:
                    channel_name = per_channel['channel_name']
                    group_name_component.text = f"[{guild_name}/{channel_name}] "
                    break
        rcon_send_body.message.append(group_name_component)

    member_nickname = await _get_onebot_member_nickname(bot, event, event.user_id) + " "
    sender_component = RconTextComponent()
    sender_component.text = member_nickname
    sender_component.color = TextColor.WHITE
    rcon_send_body.message.append(sender_component)

    sender_say_component = RconTextComponent()
    sender_say_component.text = "说："
    sender_say_component.color = TextColor.YELLOW
    rcon_send_body.message.append(sender_say_component)

    for msg in event.message:
        text_component = RconTextComponent()
        if msg.type == "text":
            text_component.text = msg.data['text'].replace("\r", "").replace("\n", "\n * ")
            text_component.color = TextColor.WHITE
        elif msg.type == "image":
            text_component.text = "[图片]"
            text_component.color = TextColor.AQUA
            if plugin_config.mc_qq_rcon_click_action_enable:
                text_component.clickEvent = RconClickEvent(
                    action=RconClickEventEnum.OPEN_URL,
                    value=msg.data['url']
                )
            if plugin_config.mc_qq_rcon_hover_event_enable:
                text_component.hover_event = RconHoverEvent(
                    action=RconHoverEventEnum.SHOW_TEXT,
                    contents=[RconTextComponent(text="查看图片", color=TextColor.GOLD)]
                )
        elif msg.type == "face":
            text_component.text = '[表情]'
            text_component.color = TextColor.YELLOW
        elif msg.type == "record":
            text_component.text = '[语音]'
            text_component.color = TextColor.GREEN
        elif msg.type == "video":
            text_component.text = '[视频]'
            text_component.color = TextColor.LIGHT_PURPLE
            if plugin_config.mc_qq_rcon_click_action_enable:
                text_component.clickEvent = RconClickEvent(
                    action=RconClickEventEnum.OPEN_URL,
                    value=msg.data['url']
                )
            if plugin_config.mc_qq_rcon_hover_event_enable:
                text_component.hover_event = RconHoverEvent(
                    action=RconHoverEventEnum.SHOW_TEXT,
                    contents=[RconTextComponent(text="查看视频", color=TextColor.DARK_PURPLE)]
                )
        elif msg.type == "at":
            at_member_nickname = await _get_onebot_member_nickname(bot, event, msg.data['qq'])
            text_component.text = f"@{at_member_nickname} "
            text_component.color = TextColor.GREEN
        elif msg.type == "share":
            text_component.text = "[分享]"
            text_component.color = TextColor.YELLOW
        elif msg.type == "forward":
            # TODO 将合并转发消息拼接为字符串
            # 获取合并转发 await bot.get_forward_msg(message_id=event.message_id)
            text_component.text = '[合并转发]'
        else:
            text_component.text = f"[{msg.type}]"
            text_component.color = TextColor.WHITE

        rcon_send_body.message.append(text_component)
    return rcon_send_body


async def parse_qq_rcon_msg_to_basemodel(
        bot: QQBot,
        event: MessageCreateEvent
) -> RconSendBody:
    """
    格式化 QQ频道 消息为 RconSendBody
    :param bot: QQBot
    :param event: 事件
    :return: RconSendBody
    """
    rcon_send_body = RconSendBody()

    prefix_component = RconTextComponent()
    prefix_component.text = "[MC_QQ] "
    prefix_component.color = TextColor.YELLOW
    rcon_send_body.message.append(prefix_component)

    if plugin_config.mc_qq_send_group_name:
        group_name_component = RconTextComponent()
        group_name_component.color = TextColor.AQUA

        guild: Guild = await bot.get_guild(guild_id=event.guild_id)
        channel: Channel = await bot.get_channel(channel_id=event.channel_id)
        group_name_component.text = f"[{guild.name}/{channel.name}] "

        rcon_send_body.message.append(group_name_component)

    member_nickname = await get_qq_member_nickname(bot, event, event.author.id) + " "
    sender_component = RconTextComponent()
    sender_component.text = member_nickname
    sender_component.color = TextColor.WHITE
    rcon_send_body.message.append(sender_component)

    sender_say_component = RconTextComponent()
    sender_say_component.text = "说："
    sender_say_component.color = TextColor.YELLOW
    rcon_send_body.message.append(sender_say_component)

    for msg in event.get_message():
        text_component = RconTextComponent()
        if msg.type == "text":
            text_component.text = msg.data['text'].replace("\r", "").replace("\n", "\n * ")
            text_component.color = TextColor.WHITE
        elif msg.type == "emoji":
            text_component.text = '[表情]'
            text_component.color = TextColor.YELLOW
        elif msg.type == "mention_user":
            text_component.text = f"@{await get_qq_member_nickname(bot, event, msg.data['user_id'])} "
            text_component.color = TextColor.GREEN
        elif msg.type == "mention_channel":
            text_component.text = f"@{(await bot.get_channel(channel_id=event.channel_id)).name} "
            text_component.color = TextColor.GREEN
        elif msg.type == "mention_everyone":
            text_component.text = f"@全体成员 "
            text_component.color = TextColor.GREEN
        elif msg.type == "image":
            text_component.text = "[图片]"
            text_component.color = TextColor.AQUA
            if plugin_config.mc_qq_rcon_click_action_enable:
                text_component.clickEvent = RconClickEvent(
                    action=RconClickEventEnum.OPEN_URL,
                    value=msg.data['url']
                )
            if plugin_config.mc_qq_rcon_hover_event_enable:
                text_component.hover_event = RconHoverEvent(
                    action=RconHoverEventEnum.SHOW_TEXT,
                    contents=[RconTextComponent(text="查看图片", color=TextColor.GOLD)]
                )
        else:
            text_component.text = f"[{msg.type}]"
            text_component.color = TextColor.WHITE
        rcon_send_body.message.append(text_component)
    return rcon_send_body
