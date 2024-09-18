from typing import Union

from nonebot.permission import SUPERUSER
from nonebot.adapters.qq import Bot as QQBot
from nonebot.internal.matcher import Matcher
from nonebot.internal.permission import Permission
from nonebot.adapters.onebot.v11 import Bot as OneBot
from nonebot.adapters.qq import GUILD_ADMIN as QQ_GUILD_ADMIN
from nonebot.adapters.qq import GUILD_OWNER as QQ_GUILD_OWNER
from nonebot.adapters.minecraft import Event as MinecraftEvent
from nonebot.adapters.qq import GuildMessageEvent as QQGuildMessageEvent
from nonebot_plugin_guild_patch import GUILD_ADMIN as ONEBOT_GUILD_ADMIN
from nonebot_plugin_guild_patch import GUILD_OWNER as ONEBOT_GUILD_OWNER
from nonebot.adapters.onebot.v11 import GROUP_ADMIN as ONEBOT_GROUP_ADMIN
from nonebot.adapters.onebot.v11 import GROUP_OWNER as ONEBOT_GROUP_OWNER
from nonebot_plugin_guild_patch import GuildMessageEvent as OneBotGuildMessageEvent
from nonebot.adapters.onebot.v11 import GroupMessageEvent as OneBotGroupMessageEvent
from nonebot.adapters.qq import GroupAtMessageCreateEvent as QQGroupAtMessageCreateEvent

from .config import plugin_config
from .model import (
    QQ_GROUP_ID_LIST,
    QQ_GUILD_ID_LIST,
    ONEBOT_GROUP_ID_LIST,
    ONEBOT_GUILD_ID_LIST,
)


def __qq_msg_rule(event: Union[QQGroupAtMessageCreateEvent, QQGuildMessageEvent]):
    """
    检测是否为 QQ 适配器 群聊消息
    :param event: GroupAtMessageCreateEvent | GuildMessageEvent
    :return: bool
    """
    if isinstance(event, QQGroupAtMessageCreateEvent):
        return event.group_id in QQ_GROUP_ID_LIST
    elif isinstance(event, QQGuildMessageEvent):
        return event.channel_id in QQ_GUILD_ID_LIST
    return False


def __onebot_msg_rule(event: Union[OneBotGroupMessageEvent, OneBotGuildMessageEvent]):
    """
    检测是否为 OneBot 适配器 群聊消息
    :param event: GroupAtMessageCreateEvent | GuildMessageEvent
    :return: bool
    """
    if isinstance(event, OneBotGroupMessageEvent):
        return str(event.group_id) in ONEBOT_GROUP_ID_LIST and not (event.self_id == event.user_id)
    elif isinstance(event, OneBotGuildMessageEvent):
        return f"{event.guild_id}:{event.channel_id}" in ONEBOT_GUILD_ID_LIST
    return False


def mc_msg_rule(event: MinecraftEvent):
    return event.server_name in plugin_config.server_dict.keys()


def all_msg_rule(
        event: Union[
            QQGroupAtMessageCreateEvent, OneBotGroupMessageEvent, OneBotGuildMessageEvent, QQGuildMessageEvent
        ]
):
    """
    检测是否为 OneBot 适配器 群聊消息，同时过滤掉 本插件命令头 开头的消息
    :param event: GroupAtMessageCreateEvent | GuildMessageEvent
    :return: bool
    """
    if str(event.get_message())[0] in plugin_config.ignore_message_header:
        return False
    return __onebot_msg_rule(event) or __qq_msg_rule(event)


async def __onebot_guild_role_admin(bot: OneBot, event: OneBotGuildMessageEvent):
    """
    检测是否为 OneBot 适配器 频道管理员
    :param bot: Bot
    :param event: GuildMessageEvent
    :return: bool
    """
    roles = {
        role["role_name"]
        for role in (
            await bot.get_guild_member_profile(
                guild_id=event.guild_id, user_id=event.user_id
            )
        )["roles"]
    }
    return bool(roles & set(plugin_config.guild_admin_roles))


async def __qq_guild_role_admin(bot: QQBot, event: QQGuildMessageEvent):
    """
    检测是否为 QQ适配器 频道管理员
    :param bot: Bot
    :param event: GuildMessageEvent
    :return: bool
    """
    guild_roles = await bot.get_guild_roles(guild_id=event.guild_id)
    tem_roles = []
    for role in guild_roles.roles:
        if role.name in plugin_config.guild_admin_roles:
            tem_roles.append(role.id)
    return bool(set(event.member.roles) & set(tem_roles))


ONEBOT_GUILD_ROLE_ADMIN = Permission(__onebot_guild_role_admin)
"""OneBot 适配器 频道管理身份组"""
QQ_GUILD_ROLE_ADMIN = Permission(__qq_guild_role_admin)
"""QQ 适配器 频道管理身份组"""


async def permission_check(
        matcher: Matcher,
        bot: Union[OneBot, QQBot],
        event: Union[OneBotGroupMessageEvent, OneBotGuildMessageEvent, QQGroupAtMessageCreateEvent, QQGuildMessageEvent]
):
    """
    权限检查
    :param matcher: Matcher
    :param bot: OneBot or QQBot
    :param event: OneBotGroupMessageEvent or OneBotGuildMessageEvent or QQGroupAtMessageCreateEvent or QQGuildMessageEvent
    :return: None
    """
    if (
            (isinstance(event, OneBotGroupMessageEvent) and isinstance(bot, OneBot) and
             not await (ONEBOT_GROUP_ADMIN | ONEBOT_GROUP_OWNER | SUPERUSER)(bot, event))
            or
            (isinstance(event, OneBotGuildMessageEvent) and isinstance(bot, OneBot) and
             not await (ONEBOT_GUILD_ADMIN | ONEBOT_GUILD_OWNER | ONEBOT_GUILD_ROLE_ADMIN | SUPERUSER)(bot, event))
            or
            (isinstance(event, QQGuildMessageEvent) and isinstance(bot, QQBot) and
             not await (QQ_GUILD_ADMIN | QQ_GUILD_OWNER | SUPERUSER | QQ_GUILD_ROLE_ADMIN)(bot, event))
            or
            (isinstance(event, QQGroupAtMessageCreateEvent) and isinstance(bot, QQBot) and
             not await SUPERUSER(bot, event))
    ):
        await matcher.finish("你没有权限使用此命令")
