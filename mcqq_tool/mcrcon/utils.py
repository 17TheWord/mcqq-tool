import json
from typing import Union, List, Optional

import aiomcrcon
from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot_plugin_guild_patch import GuildMessageEvent
from .data_model import RconClient, RconCLIENTS
from ..common import get_member_nickname, send_msg_to_qq_common


async def get_rcon_clients(
        event: Union[GroupMessageEvent, GuildMessageEvent],
        server_list: list
) -> List[RconClient]:
    """获取 服务器名、ws客户端、Rcon连接"""
    res: List[RconClient] = []
    for per_client in RconCLIENTS:
        for per_server in server_list:
            # 如果 服务器名 == ws客户端中记录的服务器名，且ws客户端存在
            if per_server.server_name == per_client.server_name and per_client.rcon:
                if isinstance(event, GroupMessageEvent):
                    if event.group_id in per_server['group_list']:
                        res.append(per_client)
                if isinstance(event, GuildMessageEvent):
                    for per_guild in per_server.guild_list:
                        if per_guild.guild_id == event.guild_id and per_guild.channel_id == event.channel_id:
                            res.append(per_client)
    return res


async def remove_rcon_client(server_name: str):
    """移除 Rcon 客户端"""
    for client in RconCLIENTS:
        if client.server_name == server_name:
            await client.rcon.close()
            RconCLIENTS.remove(client)
            logger.error(f"[MC_QQ_Rcon]丨[Server:{server_name}] 的 WebSocket、Rcon 连接已断开")


async def rcon_send_msg_to_qq(
        bot: Bot,
        message: str,
        server_list: list,
        display_server_name: Optional[bool] = False

):
    await send_msg_to_qq_common(
        bot=bot,
        message=message,
        server_list=server_list,
        display_server_name=display_server_name,
        plugin_name="MC_QQ_Rcon"
    )


async def rcon_connect(client: aiomcrcon.Client, server_name: str):
    """连接 Rcon"""
    try:
        await client.connect()
    except aiomcrcon.RCONConnectionError as e:
        logger.error(f"[MC_QQ_Rcon]丨[Server:{server_name}] 的Rcon连接失败：{str(e)}")
    except aiomcrcon.IncorrectPasswordError as e:
        logger.error(f"[MC_QQ_Rcon]丨[Server:{server_name}] 的Rcon密码错误：{str(e)}")
    else:
        logger.success(f"[MC_QQ_Rcon]丨[Server:{server_name}] 的Rcon连接成功")


async def msg_process_to_cmd(
        bot: Bot,
        event: Union[GroupMessageEvent, GuildMessageEvent],
        send_group_name: Optional[bool] = False
):
    """消息处理为 命令"""
    # 获取昵称
    member_nickname = await get_member_nickname(bot, event, event.user_id)

    # 初始化日志消息
    text_msg = member_nickname + " 说："

    command_msg = "tellraw @p "

    message_list = [
        {"text": "[MC_QQ] ", "color": "yellow"},
    ]
    if send_group_name:
        if isinstance(event, GroupMessageEvent):
            message_list.append(
                {"text": (await bot.get_group_info(group_id=event.group_id))['group_name'] + " ", "color": "aqua"})
        elif isinstance(event, GuildMessageEvent):
            guild_name = (await bot.get_guild_meta_by_guest(guild_id=event.guild_id))['guild_name']
            for per_channel in (await bot.get_guild_channel_list(guild_id=event.guild_id, no_cache=True)):
                if str(event.channel_id) == per_channel['channel_id']:
                    message_list.append({"text": guild_name + "丨" + per_channel['channel_name'] + " ", "color": "aqua"})
                    break
    message_list.append({"text": member_nickname, "color": "aqua"})
    message_list.append({"text": " 说：", "color": "yellow"})

    for msg in event.message:
        # 文本
        if msg.type == "text":
            msg_dict = {"text": msg.data['text'].replace("\r", "").replace("\n", "\n * ") + " ", "color": "white"}
            text_msg += msg.data['text'].replace("\r", "").replace("\n", "\n * ")
        # 图片
        elif msg.type == "image":
            msg_dict = {"text": "[图片] ", "color": "yellow",
                        "clickEvent": {"action": "open_url", "value": msg.data['url']},
                        "hoverEvent": {"action": "show_text", "contents": [{"text": "查看图片", "color": "gold"}]}
                        }
            text_msg += '[图片]'
        # 表情
        elif msg.type == "face":
            msg_dict = {"text": "[表情] ", "color": "gold"}
            text_msg += '[表情]'
        # 语音
        elif msg.type == "record":
            msg_dict = {"text": "[语音] ", "color": "light_purple"}
            text_msg += '[语音]'
        # 视频
        elif msg.type == "video":
            msg_dict = {"text": "[视频] ", "color": "light_purple",
                        "clickEvent": {"action": "open_url", "value": msg.data['url']},
                        "hoverEvent": {"action": "show_text", "contents": [{"text": "查看视频", "color": "dark_purple"}]}
                        }
            text_msg += '[视频]'
        # @
        elif msg.type == "at":
            # 获取被@ 群/频道 昵称
            at_member_nickname = await get_member_nickname(bot, event, msg.data['qq'])
            msg_dict = {"text": "@" + at_member_nickname + " ", "color": "green"}
            text_msg += f"@{at_member_nickname}"
        # share
        elif msg.type == "share":
            msg_dict = {"text": "[分享：" + msg.data['title'] + "] ", "color": "yellow",
                        "clickEvent": {"action": "open_url", "value": msg.data['url']},
                        "hoverEvent": {"action": "show_text", "contents": [{"text": "查看图片", "color": "gold"}]}
                        }
            text_msg += '[分享：' + msg.data['title'] + ']'
        # forward
        elif msg.type == "forward":
            # TODO 将合并转发消息拼接为字符串
            # 获取合并转发 await bot.get_forward_msg(message_id=event.message_id)
            msg_dict = {"text": "[合并转发] ", "color": "white"}
            text_msg += '[合并转发]'
        else:
            msg_dict = {"text": "[ " + msg.type + "] ", "color": "white"}
            text_msg += '[' + msg.type + ']'

        # 放入消息列表
        message_list.append(msg_dict)

    # 拼接完整命令
    command_msg += json.dumps(message_list)
    return text_msg, command_msg


async def rcon_send_msg_to_mc(
        bot: Bot,
        event: Union[GroupMessageEvent, GuildMessageEvent],
        server_list: list
):
    """发送消息到 Minecraft"""
    text_msg, command_msg = await msg_process_to_cmd(bot=bot, event=event)
    if client_list := await get_rcon_clients(event=event, server_list=server_list):
        for client in client_list:
            if client and client.rcon:
                try:
                    await client.rcon.send_cmd(command_msg)
                except aiomcrcon.errors.ClientNotConnectedError as e:
                    logger.error(f"[MC_QQ_Rcon]丨发送至 [Server:{client.server_name}] 的过程中出现了错误：{str(e)}")
                    # 连接关闭则移除客户端
                    await remove_rcon_client(server_name=client.server_name)
                else:
                    logger.success(f"[MC_QQ_Rcon]丨发送至 [server:{client.server_name}] 的消息 \"{text_msg}\"")


async def rcon_send_command_to_mc(
        bot: Bot,
        event: Union[GroupMessageEvent, GuildMessageEvent],
        server_list: list
):
    """发送命令到 Minecraft"""
    if client_list := await get_rcon_clients(event=event, server_list=server_list):
        for client in client_list:
            if client and client.rcon:
                try:
                    await bot.send(event, message=str(
                        (await client.rcon.send_cmd(
                            event.raw_message.strip("/").strip("mcc").strip())
                         )[0]))
                except aiomcrcon.errors.ClientNotConnectedError as e:
                    logger.error(f"[MC_QQ_Rcon]丨发送至 [Server:{client.server_name}] 的过程中出现了错误：{str(e)}")
                    # 连接关闭则移除客户端
                    await remove_rcon_client(server_name=client.server_name)
                else:
                    logger.success(
                        f"[MC_QQ_Rcon]丨发送至 [server:{client.server_name}] 的命令 \"{event.raw_message.strip('/').strip('/mcc')}\""
                    )
