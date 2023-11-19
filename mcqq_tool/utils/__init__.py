"""
工具包
"""
from typing import Union

from aiomcrcon import (
    Client as RconClient,
    RCONConnectionError,
    IncorrectPasswordError
)
from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot as OneBot, GroupMessageEvent
from nonebot.adapters.qq import Bot as QQBot, MessageCreateEvent
from nonebot_plugin_guild_patch import GuildMessageEvent

from .parse import (
    parse_qq_msg_to_basemodel,
    parse_onebot_rcon_msg_to_basemodel,
    parse_onebot_msg_to_basemodel,
    parse_qq_rcon_msg_to_basemodel
)
from .send import (
    send_common_to_mc_by_ws,
    send_common_cmd_to_mc,
    send_common_cmd_to_mc_by_rcon
)
from ..config import Client, CLIENTS, plugin_config
from ..model.return_body import *


async def send_msg_to_mc(
        bot: Union[OneBot, QQBot],
        event: Union[GroupMessageEvent, GuildMessageEvent, MessageCreateEvent],
):
    """
    发送消息到 MC 服务器
    :param bot:
    :param event: 事件
    """
    if client_list := await get_clients(event=event):
        for client in client_list:
            if client:
                server = plugin_config.mc_qq_server_dict.get(client.server_name)

                # 先判断是否有Rcon进行发送
                if client.rcon and server.rcon_msg:
                    if isinstance(event, MessageCreateEvent):
                        message = await parse_qq_rcon_msg_to_basemodel(event=event, bot=bot)
                        if len(message.get_tellraw()) > 256:
                            return "消息过长，无法发送"
                    else:
                        message = await parse_onebot_rcon_msg_to_basemodel(event=event, bot=bot)
                        if len(message.get_tellraw()) > 256:
                            return "消息过长，无法发送"
                    await send_common_cmd_to_mc_by_rcon(client=client, cmd=message.get_tellraw())
                else:
                    if isinstance(event, MessageCreateEvent):
                        message = (await parse_qq_msg_to_basemodel(event=event, bot=bot)).json(ensure_ascii=False)
                    else:
                        message = (await parse_onebot_msg_to_basemodel(event=event, bot=bot)).json(ensure_ascii=False)
                    await send_common_to_mc_by_ws(client=client, message=message)
    return None


async def send_cmd_to_mc(
        event: Union[GroupMessageEvent, GuildMessageEvent, MessageCreateEvent],
        cmd: str
) -> str:
    """
    发送命令到 MC 服务器
    :param event: 事件
    :param cmd: 命令
    :return: 返回信息
    """
    back_msg = ""
    if client_list := await get_clients(event=event):
        if len(client_list) == 1:
            back_msg = await send_common_cmd_to_mc(client=client_list[0], cmd=cmd)
        else:
            for client in client_list:
                if back_info := await send_common_cmd_to_mc_by_rcon(client=client, cmd=cmd):
                    back_msg += f"{client.server_name} {back_info}"
    return back_msg


async def get_clients(event: Union[GroupMessageEvent, GuildMessageEvent, MessageCreateEvent]) -> List[Client]:
    """
    获取 服务器名、ws客户端, 返回client列表
    :param event: 事件
    :return: client列表
    """
    res: List[Client] = []
    for per_server_name, per_server in plugin_config.mc_qq_server_dict.items():
        if isinstance(event, GroupMessageEvent):
            for per_group in per_server.group_list:
                if per_group.group_id == event.group_id:
                    res.append(CLIENTS.get(per_server_name))
        elif isinstance(event, GuildMessageEvent | MessageCreateEvent):
            for per_guild in per_server.guild_list:
                if str(per_guild.guild_id) == str(event.guild_id) and str(per_guild.channel_id) == str(
                        event.channel_id):
                    res.append(CLIENTS.get(per_server_name))
    return res


async def rcon_connect(rcon_client: RconClient, server_name: str):
    """
    连接 Rcon
    :param rcon_client: Rcon 客户端
    :param server_name: 服务器名
    """
    try:
        await rcon_client.connect()
        logger.success(f"[MC_QQ]丨[Server:{server_name}] 的Rcon连接成功")
    except RCONConnectionError as e:
        logger.error(f"[MC_QQ]丨[Server:{server_name}] 的Rcon连接失败：{str(e)}")
    except IncorrectPasswordError as e:
        logger.error(f"[MC_QQ]丨[Server:{server_name}] 的Rcon密码错误：{str(e)}")
