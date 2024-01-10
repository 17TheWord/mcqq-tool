import json
from typing import Union, Optional

from nonebot.adapters.minecraft import (
    Message,
    TextColor,
    ClickEvent,
    HoverEvent,
    HoverAction,
    ClickAction,
    RconSendBody,
    BaseComponent,
    RconHoverEvent,
    MessageSegment,
    RconClickEvent,
    RconTextComponent,
    ChatImageModComponent
)
from nonebot.adapters.onebot.v11 import Bot as OneBot, GroupMessageEvent as OneBotGroupMessageEvent
from nonebot.adapters.qq import (
    Bot as QQBot,
    GuildMessageEvent as QQGuildMessageEvent,
    GroupAtMessageCreateEvent as QQGroupAtMessageCreateEvent,
)
from nonebot_plugin_guild_patch import GuildMessageEvent as OneBotGuildMessageEvent

from .config import plugin_config


async def __get_group_or_nick_name(
        bot: Union[QQBot, OneBot],
        event: Union[
            QQGuildMessageEvent, QQGroupAtMessageCreateEvent, OneBotGroupMessageEvent, OneBotGuildMessageEvent
        ],
        user_id: Optional[str] = None
) -> str:
    """
    获取群昵称或者昵称
    :param bot: 平台Bot实例
    :param event: 事件
    :param user_id: 用户ID
    :return: 昵称
    """
    temp_text = "未知昵称" if user_id is None else "[未知群聊]"
    if isinstance(event, OneBotGroupMessageEvent) and isinstance(bot, OneBot):
        if user_id:
            if event.user_id == int(user_id):
                # 如果群名片为空，则发送昵称
                temp_text = event.sender.card or event.sender.nickname
                # 如果获取其他人的昵称
            else:
                temp_text = (
                    await bot.get_group_member_info(group_id=event.group_id, user_id=int(user_id), no_cache=True)
                )["nickname"]
        else:
            temp_text = f'[{(await bot.get_group_info(group_id=event.group_id))["group_name"]}]'

    elif isinstance(event, OneBotGuildMessageEvent) and isinstance(bot, OneBot):
        if user_id:
            if event.user_id == user_id:
                temp_text = event.sender.nickname
            else:
                temp_text = (
                    await bot.get_guild_member_profile(guild_id=event.guild_id, user_id=user_id)
                )["nickname"]
        else:
            temp_text = ""
            if plugin_config.mc_qq_send_guild_name:
                guild_name = (await bot.get_guild_meta_by_guest(guild_id=event.guild_id))["guild_name"]
                temp_text = f"[{guild_name}]"
            if plugin_config.mc_qq_send_channel_name:
                for per_channel in await bot.get_guild_channel_list(
                        guild_id=event.guild_id, no_cache=True
                ):
                    if str(event.channel_id) == per_channel["channel_id"]:
                        channel_name = per_channel["channel_name"]

                        if plugin_config.mc_qq_send_guild_name:
                            temp_text = temp_text.replace("]", f"丨{channel_name}]")
                        else:
                            temp_text = f"[{channel_name}]"
                        break
    elif isinstance(event, QQGuildMessageEvent) and isinstance(bot, QQBot):
        if user_id:
            if event.author.id == user_id:
                temp_text = event.member.nick or event.author.username
            else:
                member = await bot.get_member(guild_id=event.guild_id, user_id=user_id)
                temp_text = member.nick or member.user.username
        else:
            temp_text = ""
            if plugin_config.mc_qq_send_guild_name:
                guild = await bot.get_guild(guild_id=event.guild_id)
                temp_text = f"[{guild.name}]"
            if plugin_config.mc_qq_send_channel_name:
                channel = await bot.get_channel(channel_id=event.channel_id)
                if plugin_config.mc_qq_send_guild_name:
                    temp_text = temp_text.replace("]", f"丨{channel.name}]")
                else:
                    temp_text = f"[{channel.name}]"
    elif isinstance(event, QQGroupAtMessageCreateEvent) and isinstance(bot, QQBot):
        # TODO 等待QQ机器人完善API
        temp_text = event.author.member_openid if user_id else event.group_openid
    return temp_text


def __get_hover_event_component(temp_text):
    """
    获取HoverEvent组件
    :param temp_text:
    :return:
    """
    return HoverEvent(
        action=HoverAction.SHOW_TEXT,
        contents=[BaseComponent(text=temp_text)]
    )


def __get_click_event_component(img_url):
    """
    获取ClickEvent组件
    :param img_url:
    :return:
    """
    return ClickEvent(
        action=ClickAction.OPEN_URL,
        value=img_url
    )


def __get_action_event_component(rcon_mode: bool, img_url: str, temp_text: str, color: TextColor = TextColor.WHITE):
    """
    获取HoverEvent和ClickEvent组件
    :param rcon_mode:
    :param img_url:
    :param temp_text:
    :param color:
    :return:
    """
    hover_event = None
    click_event = None
    if rcon_mode:
        if plugin_config.mc_qq_rcon_hover_event_enable:
            hover_event = __get_rcon_hover_event_component(temp_text.replace("[", "[查看"), color)
        if plugin_config.mc_qq_rcon_click_action_enable:
            click_event = __get_rcon_click_event_component(img_url)
    else:
        hover_event = __get_hover_event_component(temp_text)
        click_event = __get_click_event_component(img_url)
    return hover_event, click_event


async def __get_common_qq_msg_parsing(
        bot: Union[QQBot, OneBot],
        event: Union[
            QQGuildMessageEvent, QQGroupAtMessageCreateEvent, OneBotGroupMessageEvent, OneBotGuildMessageEvent],
        rcon_mode: bool = False
) -> tuple[list[str], str]:
    """
    获取QQ消息解析后的消息列表和日志文本
    :param bot: Bot对象
    :param event: 事件对象
    :param rcon_mode: 是否为RCON模式
    :return: 消息列表和日志文本
    """
    log_text = ""

    message_list = []

    # 消息内容
    for msg in event.get_message():
        click_event = None
        hover_event = None
        temp_color = TextColor.WHITE
        if msg.type == "text":
            temp_text = msg.data["text"].replace("\r", "").replace("\n", "\n * ")
            temp_color = TextColor.WHITE

        elif msg.type in ["image", "attachment"]:
            temp_text = "[图片]"
            temp_color = TextColor.AQUA
            img_url = msg.data["url"] if msg.data["url"].startswith("http") else f"https://{msg.data['url']}"
            if plugin_config.mc_qq_chat_image_enable and msg.type in ["image", "attachment"]:
                temp_text = str(ChatImageModComponent(url=img_url, name=temp_text))
            else:
                hover_event, click_event = __get_action_event_component(rcon_mode, img_url, temp_text, TextColor.BLUE)
        elif msg.type == "video":
            temp_text = "[视频]"
            temp_color = TextColor.LIGHT_PURPLE
            img_url = msg.data["url"] if msg.data["url"].startswith("http") else f"https://{msg.data['url']}"
            hover_event, click_event = __get_action_event_component(rcon_mode, img_url, temp_text,
                                                                    TextColor.DARK_PURPLE)
        elif msg.type == "share":
            temp_text = "[分享]"
            temp_color = TextColor.GOLD
            img_url = msg.data["url"] if msg.data["url"].startswith("http") else f"https://{msg.data['url']}"
            hover_event, click_event = __get_action_event_component(rcon_mode, img_url, temp_text, TextColor.YELLOW)

        # @用户 OneBot
        elif msg.type == "at":
            temp_text = f"@{__get_group_or_nick_name(bot, event, msg.data['qq'])} "
            temp_color = TextColor.GREEN

        # @用户 QQ
        elif msg.type == "mention_user":
            temp_text = (
                f"@{await __get_group_or_nick_name(bot, event, msg.data['user_id'])} "
            )
            temp_color = TextColor.GREEN

        # @子频道
        elif msg.type == "mention_channel":
            temp_text = f"@{(await bot.get_channel(channel_id=event.channel_id)).name} "
            temp_color = TextColor.GREEN

        # @全体成员
        elif msg.type in ["mention_everyone", "all"]:
            temp_text = "@全体成员"
            temp_color = TextColor.GREEN

        elif msg.type in ["face", "emoji"]:
            temp_text = "[表情]"
            temp_color = TextColor.GREEN

        elif msg.type == "record":
            temp_text = "[语音]"
            temp_color = TextColor.GOLD
        else:
            temp_text = "[未知消息类型]"

        # 消息内容
        temp_component = RconTextComponent(
            text=temp_text,
            color=temp_color,
            hover_event=hover_event,
            click_event=click_event
        ) if rcon_mode else MessageSegment.text(
            text=temp_text,
            color=temp_color,
            hover_event=hover_event,
            click_event=click_event
        )
        log_text += temp_text
        if plugin_config.mc_qq_rcon_text_component_status == 2:
            message_list.append(temp_component.get_component().removeprefix('"').removesuffix('"'))
        else:
            message_list.append(str(temp_component))

    return message_list, log_text


async def parse_qq_msg_to_base_model(
        bot: Union[QQBot, OneBot],
        event: Union[
            QQGuildMessageEvent,
            QQGroupAtMessageCreateEvent,
            OneBotGroupMessageEvent,
            OneBotGuildMessageEvent
        ]
) -> Message:
    """
    解析 QQ 消息，转为 WebSocketBody 模型
    :param bot: 聊天平台Bot实例
    :param event: 所有事件
    :return: Message
    """

    message_list = Message(MessageSegment.text(text="[MC_QQ] ", color=TextColor.YELLOW))

    # 是否发送群聊名称
    if plugin_config.mc_qq_send_group_name or (
            plugin_config.mc_qq_send_guild_name or plugin_config.mc_qq_send_channel_name
    ):
        temp_group_name = await __get_group_or_nick_name(bot, event)
        message_list.append(MessageSegment.text(text=f"{temp_group_name} ", color=TextColor.GREEN))

    # 消息发送者昵称
    sender_nickname_text = await __get_group_or_nick_name(bot, event, str(event.get_user_id()))
    message_list.append(MessageSegment.text(text=f"{sender_nickname_text} ", color=TextColor.GREEN))

    # 消息 '说：'
    message_list.append(MessageSegment.text(text="说：", color=TextColor.WHITE))

    # 消息内容
    message_list += await __get_common_qq_msg_parsing(bot, event, False)
    return message_list


def __get_rcon_hover_event_component(text: str, color: TextColor = TextColor.GOLD) -> RconHoverEvent:
    """
    获取 Rcon HoverEvent
    :param text: 悬浮文本
    :param color: 文本颜色
    :return: 悬浮组件
    """
    return RconHoverEvent(
        action=HoverAction.SHOW_TEXT,
        contents=[RconTextComponent(text=text, color=color)],
    )


def __get_rcon_click_event_component(url: str) -> RconClickEvent:
    """
    获取 Rcon ClickEvent
    :param url:
    :return:
    """
    return RconClickEvent(
        action=ClickAction.OPEN_URL,
        url=url
    )


async def parse_qq_msg_to_rcon_model(
        bot: Union[QQBot, OneBot],
        event: Union[
            QQGuildMessageEvent,
            QQGroupAtMessageCreateEvent,
            OneBotGroupMessageEvent,
            OneBotGuildMessageEvent
        ]
):
    """
    解析 QQ 消息，转为 Rcon命令 模型
    :param bot: bot 对象
    :param event: 事件
    :return: RconSendBody
    """
    rcon_send_body = RconSendBody()
    prefix_component = "[MC_QQ] " if plugin_config.mc_qq_rcon_text_component_status == 0 else RconTextComponent(
        text="[MC_QQ] ", color=TextColor.YELLOW).get_component().removeprefix('"').removesuffix('"')
    log_text = "[MC_QQ] "

    message_list = [prefix_component]

    # 是否发送群聊名称
    if plugin_config.mc_qq_send_group_name or (
            plugin_config.mc_qq_send_guild_name or plugin_config.mc_qq_send_channel_name
    ):
        temp_group_name = await __get_group_or_nick_name(bot=bot, event=event)

        group_name_component = RconTextComponent(
            text=temp_group_name, color=TextColor.GREEN
        ) if plugin_config.mc_qq_rcon_text_component_status == 0 else temp_group_name

        message_list.append(group_name_component.get_component().removeprefix('"').removesuffix('"'))
        log_text += str(group_name_component)

    # 发送者昵称
    sender_nickname_text = await __get_group_or_nick_name(bot=bot, event=event, user_id=event.get_user_id())
    sender_nickname_component = RconTextComponent(
        text=sender_nickname_text, color=TextColor.GREEN
    ) if plugin_config.mc_qq_rcon_text_component_status == 0 else sender_nickname_text

    message_list.append(sender_nickname_component.get_component().removeprefix('"').removesuffix('"'))
    log_text += str(sender_nickname_component)

    # 说
    message_list.append("说：")
    log_text += "说："

    rcon_send_body.message = message_list
    # 消息内容
    message_body = RconSendBody()
    temp_message_list, log_msgs = await __get_common_qq_msg_parsing(bot=bot, event=event, rcon_mode=True)
    log_text += log_msgs

    message_body.message = temp_message_list

    result = message_list + temp_message_list

    parsed_result = [json.loads(item) if item.startswith('{') else item for item in result]

    return str(parsed_result), log_text


def parse_qq_screen_cmd_to_rcon_model(
        command_type: str,
        command: str
):
    """
    解析 QQ 消息，转为 Rcon命令 模型
    :param command_type: 命令类型
    :param command: 命令内容
    :return: 命令文本
    """
    if command_type == "action_bar":
        return f'title @a actionbar "{command}"'
    else:
        return f'title @a "{command}"'


def parse_qq_screen_cmd_to_base_model(
        command_type: str,
        command: str
):
    """
    解析 QQ 消息，转为 websocket消息 模型
    :param command_type: 命令类型
    :param command: 命令内容
    :return: 命令文本
    """
    if command_type == "action_bar":
        return Message(MessageSegment.actionbar(text=f"[MC_QQ] {command}", color=TextColor.YELLOW))
    elif command_type == "title":
        title, subtitle = command.split("\n") if "\n" in command else (command, "")
        return Message(MessageSegment.title(title=title, subtitle=subtitle))
    else:
        return Message(MessageSegment.text(text=f"[MC_QQ] {command}", color=TextColor.YELLOW))


__all__ = [
    "parse_qq_msg_to_rcon_model",
    "parse_qq_msg_to_base_model",
    "parse_qq_screen_cmd_to_rcon_model",
    "parse_qq_screen_cmd_to_base_model"
]
