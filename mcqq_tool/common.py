import json
from typing import Union, Optional, List

from nonebot import logger, get_driver
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.internal.permission import Permission
from nonebot_plugin_guild_patch import GuildMessageEvent
from pydantic import BaseModel

from .model import event_dict
from .model.basemodel import BaseEvent, BaseChatEvent, BaseDeathEvent, BaseJoinEvent, BaseQuitEvent


class RoleConfig(BaseModel):
    # MC_QQ 频道管理员身份组
    mc_qq_guild_admin_roles: Optional[List[str]] = ["频道主", "管理员"]


role_config: RoleConfig = RoleConfig.parse_obj(get_driver().config)


async def _guild_admin(
        bot: Bot,
        event: GuildMessageEvent,
):
    """检测是否为频道管理员"""
    roles = set(
        role["role_name"]
        for role in (
            await bot.get_guild_member_profile(
                guild_id=event.guild_id, user_id=event.user_id
            )
        )["roles"]
    )
    return bool(roles & set(role_config.mc_qq_guild_admin_roles))


GUILD_ADMIN: Permission = Permission(_guild_admin)
"""频道管理员权限"""


async def msg_to_qq_process(event: BaseEvent) -> str:
    """处理来自MC的消息，并返回处理后的消息"""
    if isinstance(event, BaseChatEvent):
        return f"{event.player.nickname} 说：{event.message}"
    elif isinstance(event, BaseDeathEvent):
        return f"{event.player.nickname} {event.death_message}"
    elif isinstance(event, BaseJoinEvent):
        return f"{event.player.nickname} 加入了游戏"
    elif isinstance(event, BaseQuitEvent):
        return f"{event.player.nickname} 离开了游戏"
    else:
        return "未知消息"


async def send_msg_to_qq_common(
        bot: Bot,
        message: str,
        server_list: list,
        display_server_name: Optional[bool] = False,
        plugin_name: Optional[str] = "MC_QQ"
):
    """发送消息到 QQ"""
    json_msg = json.loads(message)
    event = event_dict[json_msg["event_name"]].parse_obj(json_msg)

    msg = await msg_to_qq_process(event)
    if display_server_name:
        msg = f"[{event.server_name}] {msg}"
    # 循环服务器列表并发送消息
    if mc_qq_servers_list := server_list:
        for per_server in mc_qq_servers_list:
            # 判断服务器名称是否相同
            if per_server.server_name == event.server_name:
                # 判断是否发送到群聊
                if group_list := per_server.group_list:
                    for per_group in group_list:
                        logger.success(
                            f"[{plugin_name}]丨from [{event.server_name}] to [群:{per_group}] \"{msg}\"")
                        await bot.send_group_msg(
                            group_id=per_group,
                            message=msg
                        )
                # 判断是否发送到频道
                if guild_list := per_server.guild_list:
                    for per_guild in guild_list:
                        logger.success(
                            f"[{plugin_name}]丨from [{event.server_name}] to [频道:{per_guild.guild_id}/{per_guild.channel_id}] \"{msg}\"")
                        await bot.send_guild_channel_msg(
                            guild_id=per_guild.guild_id,
                            channel_id=per_guild.channel_id,
                            message=msg
                        )


async def get_member_nickname(
        bot: Bot,
        event: Union[GroupMessageEvent, GuildMessageEvent],
        user_id: Union[int, str]
) -> str:
    """获取昵称"""
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
