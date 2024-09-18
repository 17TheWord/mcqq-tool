from typing import List, Tuple, Union, Optional

from nonebot.adapters.qq import Bot as QQBot
from nonebot.adapters.minecraft.utils import zip_dict
from nonebot.adapters.onebot.v11 import Bot as OneBot
from nonebot.adapters.minecraft import Message, MessageSegment
from nonebot.adapters.qq import GuildMessageEvent as QQGuildMessageEvent
from nonebot_plugin_guild_patch import GuildMessageEvent as OneBotGuildMessageEvent
from nonebot.adapters.onebot.v11 import GroupMessageEvent as OneBotGroupMessageEvent
from nonebot.adapters.qq import GroupAtMessageCreateEvent as QQGroupAtMessageCreateEvent
from nonebot.adapters.minecraft.model import (
    TextColor,
    ClickEvent,
    HoverEvent,
    ClickAction,
    HoverAction,
    BaseComponent,
    RconTextComponent,
    ChatImageModComponent,
)

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
            if plugin_config.send_guild_name:
                guild_name = (await bot.get_guild_meta_by_guest(guild_id=event.guild_id))["guild_name"]
                temp_text = f"[{guild_name}]"
            if plugin_config.send_channel_name:
                for per_channel in await bot.get_guild_channel_list(
                        guild_id=event.guild_id, no_cache=True
                ):
                    if str(event.channel_id) == per_channel["channel_id"]:
                        channel_name = per_channel["channel_name"]

                        if plugin_config.send_guild_name:
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
            if plugin_config.send_guild_name:
                guild = await bot.get_guild(guild_id=event.guild_id)
                temp_text = f"[{guild.name}]"
            if plugin_config.send_channel_name:
                channel = await bot.get_channel(channel_id=event.channel_id)
                if plugin_config.send_guild_name:
                    temp_text = temp_text.replace("]", f"丨{channel.name}]")
                else:
                    temp_text = f"[{channel.name}]"
    elif isinstance(event, QQGroupAtMessageCreateEvent) and isinstance(bot, QQBot):
        # TODO 等待QQ机器人完善API
        temp_text = event.author.member_openid if user_id else event.group_openid
    return temp_text


def __get_action_event_component(rcon_model: bool, img_url: str, temp_text: str):
    """
    获取HoverEvent和ClickEvent组件
    :param img_url: 图片链接
    :param temp_text: 文本
    :return: HoverEvent和ClickEvent组件
    """
    temp_text = temp_text.replace("[", "[查看")
    if rcon_model:
        return None, None
    hover_event = HoverEvent(
        action=HoverAction.SHOW_TEXT,
        text=[BaseComponent(text=temp_text, color=TextColor.DARK_PURPLE)]
    )
    click_event = ClickEvent(
        action=ClickAction.OPEN_URL,
        value=img_url
    )
    return hover_event, click_event


async def __get_common_qq_msg_parsing(
        bot: Union[QQBot, OneBot],
        event: Union[
            QQGuildMessageEvent, QQGroupAtMessageCreateEvent, OneBotGroupMessageEvent, OneBotGuildMessageEvent],
        rcon_mode: bool = False
):
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
        temp_color = None
        if msg.type == "text":
            temp_text = msg.data["text"].replace("\r", "").replace("\n", "\n * ") + " "
            log_text += temp_text
            message_list.append(temp_text)
            continue

        elif msg.type in ["image", "attachment"]:
            temp_text = "[图片]"
            temp_color = TextColor.LIGHT_PURPLE
            img_url = msg.data["url"] if msg.data["url"].startswith("http") else f"https://{msg.data['url']}"
            if plugin_config.chat_image_enable:
                temp_text = str(ChatImageModComponent(url=img_url))
                log_text += "[CICode:图片]"
                message_list.append(temp_text)
                continue
            else:
                hover_event, click_event = __get_action_event_component(rcon_mode, img_url, temp_text)
        elif msg.type == "video":
            temp_text = "[视频]"
            temp_color = TextColor.LIGHT_PURPLE
            img_url = msg.data["url"] if msg.data["url"].startswith("http") else f"https://{msg.data['url']}"
            hover_event, click_event = __get_action_event_component(rcon_mode, img_url, temp_text)
        elif msg.type == "share":
            temp_text = "[分享]"
            temp_color = TextColor.GOLD
            img_url = msg.data["url"] if msg.data["url"].startswith("http") else f"https://{msg.data['url']}"
            hover_event, click_event = __get_action_event_component(rcon_mode, img_url, temp_text)

        # @用户 OneBot
        elif msg.type == "at":
            if msg.data["qq"] == "all":
                temp_text = "@全体成员"
            else:
                temp_text = f"@{await __get_group_or_nick_name(bot, event, msg.data['qq'])}"
            temp_color = TextColor.GREEN

        # @用户 QQ
        elif msg.type == "mention_user":
            temp_text = (
                f"@{await __get_group_or_nick_name(bot, event, msg.data['user_id'])}"
            )
            temp_color = TextColor.GREEN

        # @子频道
        elif msg.type == "mention_channel":
            temp_text = f"@{(await bot.get_channel(channel_id=event.channel_id)).name}"
            temp_color = TextColor.GREEN

        # @全体成员
        elif msg.type == "mention_everyone":
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

        temp_text = temp_text.strip() + " "

        log_text += temp_text

        if rcon_mode:
            temp_component = RconTextComponent(
                text=temp_text,
                color=temp_color
            )
            message_list.append(zip_dict(temp_component))
        else:
            temp_component = MessageSegment.text(
                text=temp_text,
                color=temp_color,
                hover_event=hover_event,
                click_event=click_event
            )
            message_list.append(temp_component)

    return message_list, log_text


async def parse_qq_msg_to_base_model(
        bot: Union[QQBot, OneBot],
        event: Union[
            QQGuildMessageEvent,
            QQGroupAtMessageCreateEvent,
            OneBotGroupMessageEvent,
            OneBotGuildMessageEvent
        ]
) -> Tuple[Message, str]:
    """
    解析 QQ 消息，转为 WebSocketBody 模型
    :param bot: 聊天平台Bot实例
    :param event: 所有事件
    :return: Message
    """

    message_list = Message()
    log_text = ""

    # 是否发送群聊名称
    if plugin_config.send_group_name:
        temp_group_name = (await __get_group_or_nick_name(bot, event)) + " "
        message_list.append(MessageSegment.text(text=temp_group_name, color=TextColor.AQUA))
        log_text += temp_group_name

    # 消息发送者昵称
    sender_nickname_text = (await __get_group_or_nick_name(bot, event, str(event.get_user_id())))
    message_list.append(MessageSegment.text(text=sender_nickname_text, color=TextColor.GREEN))
    log_text += sender_nickname_text

    # 消息 '说：'
    message_list.append(MessageSegment.text(text=plugin_config.say_way))
    log_text += plugin_config.say_way

    # 消息内容
    temp_message_list, msg_log_text = await __get_common_qq_msg_parsing(bot, event, False)
    temp_message_list: List[MessageSegment]
    log_text += msg_log_text

    message_list += Message(temp_message_list)

    return message_list, log_text


async def parse_qq_msg_to_rcon_model(
        bot: Union[QQBot, OneBot],
        event: Union[
            QQGuildMessageEvent,
            QQGroupAtMessageCreateEvent,
            OneBotGroupMessageEvent,
            OneBotGuildMessageEvent
        ]
) -> Tuple[List[Union[str]], str]:
    """
    解析 QQ 消息，转为 Rcon命令 模型
    :param bot: bot 对象
    :param event: 事件
    :return: RconSendBody
    """

    prefix_component = RconTextComponent(text="[鹊桥] ", color=TextColor.YELLOW)
    log_text = ""

    message_list = ["", zip_dict(prefix_component)]  # Rcon 开头双引号

    # 是否发送群聊名称
    if plugin_config.send_group_name:
        temp_group_name = (await __get_group_or_nick_name(bot=bot, event=event)) + " "

        group_name_component = RconTextComponent(text=temp_group_name, color=TextColor.AQUA)

        message_list.append(zip_dict(group_name_component))
        log_text += temp_group_name

    # 发送者昵称
    sender_nickname_text = (await __get_group_or_nick_name(bot=bot, event=event, user_id=event.get_user_id()))
    log_text += sender_nickname_text

    sender_nickname_component = RconTextComponent(text=sender_nickname_text, color=TextColor.GREEN)
    message_list.append(zip_dict(sender_nickname_component))
    # 说
    message_list.append(plugin_config.say_way)
    log_text += plugin_config.say_way

    # 消息内容
    temp_message_list, log_msgs = await __get_common_qq_msg_parsing(bot=bot, event=event, rcon_mode=True)
    log_text += log_msgs

    message_list = message_list + temp_message_list

    return message_list, log_text


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
