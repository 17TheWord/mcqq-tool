import json
import contextlib
from typing import List, Union, Tuple

from aiomcrcon import (
    Client as RconClient,
    ClientNotConnectedError,
    RCONConnectionError,
    IncorrectPasswordError
)
from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.drivers.websockets import WebSocketClosed
from nonebot_plugin_guild_patch import GuildMessageEvent

from .common import get_member_nickname, _send_msg_to_qq_common, plugin_config
from .config import Client, CLIENTS


async def send_msg_to_mc(bot: Bot, event: Union[GroupMessageEvent, GuildMessageEvent]):
    """
    发送消息到 MC
    :param bot: Bot
    :param event: 事件
    """
    # 处理来自QQ的消息
    if client_list := await _get_clients(event=event):
        for client in client_list:
            if client:
                # 先判断是否有Rcon进行发送
                if client.rcon:
                    rcon_text_msg, msg_cmd = await _msg_process_to_cmd(bot=bot, event=event)
                    try:
                        await client.rcon.send_cmd(msg_cmd)
                        logger.success(f"[MC_QQ_Rcon]丨发送至 [server:{client.server_name}] 的消息 \"{rcon_text_msg}\"")
                    except ClientNotConnectedError as e:
                        logger.error(f"[MC_QQ_Rcon]丨发送至 [Server:{client.server_name}] 的过程中出现了错误：{e}")
                        await remove_client(client.server_name)
                elif client.websocket:
                    text_msg, msg_json = await _msg_process_to_json(bot=bot, event=event)
                    try:
                        await client.websocket.send(msg_json)
                        logger.success(f"[MC_QQ]丨发送至 [server:{client.server_name}] 的消息 \"{text_msg}\"")
                    except WebSocketClosed as e:
                        logger.error(f"[MC_QQ]丨发送至 [Server:{client.server_name}] 的过程中出现了错误：{e}")
                        await remove_client(client.server_name)
                else:
                    logger.error(f"[MC_QQ]丨发送至 [Server:{client.server_name}] 的过程中出现了错误：该服务器没有连接")
                    await remove_client(client.server_name)


async def send_cmd_to_mc(bot: Bot, event: Union[GroupMessageEvent, GuildMessageEvent], cmd: str):
    """
    发送命令到 MC
    :param bot: Bot
    :param event: 事件
    :param cmd: 命令
    """
    # 处理来自QQ的消息
    if client_list := await _get_clients(event=event):
        for client in client_list:
            if client:
                # 先判断是否有Rcon进行发送
                if client.rcon:
                    try:
                        back_msg = await client.rcon.send_cmd(cmd)
                        await bot.send(event=event, message=f"服务器返回：{back_msg[0]}")
                        logger.success(f"[MC_QQ_Rcon]丨发送至 [server:{client.server_name}] 的消息 \"{cmd}\"")
                    except ClientNotConnectedError as e:
                        logger.error(f"[MC_QQ_Rcon]丨发送至 [Server:{client.server_name}] 的过程中出现了错误：{e}")
                        await remove_client(client.server_name)
                elif client.websocket:
                    cmd_list = {"message": [{"msgType": "command", "msgData": cmd}]}
                    await client.websocket.send_text(str(cmd_list))
                else:
                    logger.error(f"[MC_QQ]丨发送至 [Server:{client.server_name}] 的过程中出现了错误：该客户端没有连接")
                    await remove_client(client.server_name)


async def _get_clients(event: Union[GroupMessageEvent, GuildMessageEvent]) -> List[Client]:
    """
    获取 服务器名、ws客户端, 返回client列表
    :param event: 事件
    :return: client列表
    """
    res: List[Client] = []
    for per_server in plugin_config.mc_qq_server_list:
        if isinstance(event, GroupMessageEvent):
            if event.group_id in per_server.group_list:
                res.append(CLIENTS.get(per_server.server_name))
        if isinstance(event, GuildMessageEvent):
            for per_guild in per_server.guild_list:
                if per_guild.guild_id == event.guild_id and per_guild.channel_id == event.channel_id:
                    res.append(CLIENTS.get(per_server.server_name))
    return res


async def remove_client(server_name: str):
    """
    移除客户端
    :param server_name: 服务器名
    """
    if client := CLIENTS.get(server_name):
        if client.websocket:
            with contextlib.suppress(Exception):
                await client.websocket.close()
        if client.rcon:
            await client.rcon.close()
        del CLIENTS[server_name]


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


async def send_msg_to_qq(
        bot: Bot,
        message: str
):
    """
    发送消息到 QQ
    :param bot: Bot
    :param message: 消息
    """
    await _send_msg_to_qq_common(
        bot=bot,
        message=message
    )


async def _msg_process_to_json(bot: Bot, event: Union[GroupMessageEvent, GuildMessageEvent]) -> Tuple[str, str]:
    """
    消息处理为 JSON
    :param bot: Bot
    :param event: 事件
    :return: text_msg, msgJson
    """
    # 获取昵称
    member_nickname = await get_member_nickname(bot, event, event.user_id)

    # 初始化消息
    text_msg = member_nickname + "说："

    # 初始化消息字典
    message_list = []

    # 发送群聊名称
    if plugin_config.mc_qq_send_group_name:
        group_name = {'msgType': "group_name"}
        if isinstance(event, GroupMessageEvent):
            group_name['msgData'] = (await bot.get_group_info(group_id=event.group_id))['group_name']
        elif isinstance(event, GuildMessageEvent):
            guild_name = (await bot.get_guild_meta_by_guest(guild_id=event.guild_id))['guild_name']
            for per_channel in (await bot.get_guild_channel_list(guild_id=event.guild_id, no_cache=True)):
                if str(event.channel_id) == per_channel['channel_id']:
                    channel_name = per_channel['channel_name']
                    group_name['msgData'] = f"{guild_name}丨{channel_name}"
                    break
        message_list.append({"msgType": "group_name", "msgData": group_name})

    # 将群成员昵称装入消息列表
    message_list.append({"msgType": "senderName", "msgData": member_nickname})

    for msg in event.message:
        per_msg = {'msgType': msg.type}
        # 文本
        if msg.type == "text":
            msgData = msg.data['text'].replace("\r", "").replace("\n", "\n * ")
            text_msg += msgData
        # 图片
        elif msg.type == "image":
            msgData = msg.data['url']
            text_msg += '[图片]'
        # 表情
        elif msg.type == "face":
            msgData = '[表情]'
            text_msg += '[表情]'
        # 语音
        elif msg.type == "record":
            msgData = '[语音]'
            text_msg += '[语音]'
        # 视频
        elif msg.type == "video":
            msgData = msg.data['url']
            text_msg += '[视频]'
        # @
        elif msg.type == "at":
            # 获取被@ 群/频道 昵称
            at_member_nickname = await get_member_nickname(bot, event, msg.data['qq'])
            msgData = f"@{at_member_nickname}"
            text_msg += msgData
        # share
        elif msg.type == "share":
            msgData = msg.data['url']
            text_msg += '[分享：' + msg.data['title'] + ']'
        # forward
        elif msg.type == "forward":
            # TODO 将合并转发消息拼接为字符串
            # 获取合并转发 await bot.get_forward_msg(message_id=event.message_id)
            msgData = '[合并转发]'
            text_msg = msgData
        else:
            msgData = msg.type
            text_msg += '[' + msg.type + '] '

        text_msg += " "

        # 装入消息数据
        per_msg['msgData'] = msgData
        # 放入消息列表
        message_list.append(per_msg)

    return text_msg, str({"message": message_list})


async def _msg_process_to_cmd(bot: Bot, event: Union[GroupMessageEvent, GuildMessageEvent]) -> Tuple[str, str]:
    """
    消息处理为 命令
    :param bot: Bot
    :param event: 事件
    :return: text_msg, command_msg
    """
    # 获取昵称
    member_nickname = await get_member_nickname(bot, event, event.user_id)

    # 初始化日志消息
    text_msg = member_nickname + " 说："

    command_msg = "tellraw @a "

    message_list = [
        {"text": "[MC_QQ] ", "color": "yellow"},
    ]
    if plugin_config.mc_qq_send_group_name:
        if isinstance(event, GroupMessageEvent):
            message_list.append(
                {"text": (await bot.get_group_info(group_id=event.group_id))['group_name'] + " ", "color": "aqua"})
        elif isinstance(event, GuildMessageEvent):
            guild_name = (await bot.get_guild_meta_by_guest(guild_id=event.guild_id))['guild_name']
            for per_channel in (await bot.get_guild_channel_list(guild_id=event.guild_id, no_cache=True)):
                if str(event.channel_id) == per_channel['channel_id']:
                    message_list.append(
                        {"text": guild_name + "丨" + per_channel['channel_name'] + " ", "color": "aqua"})
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
                        "hoverEvent": {"action": "show_text",
                                       "contents": [{"text": "查看视频", "color": "dark_purple"}]}
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
