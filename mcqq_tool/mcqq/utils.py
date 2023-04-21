from typing import List, Union, Optional

import websockets
from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot_plugin_guild_patch import GuildMessageEvent
from .data_model import Client, CLIENTS
from ..common import get_member_nickname, send_msg_to_qq_common


async def send_msg_to_mc(
        bot: Bot, event: Union[GroupMessageEvent, GuildMessageEvent],
        server_list: list
):
    """发送消息到 MC"""
    # 处理来自QQ的消息
    text_msg, msgJson = await msg_process_to_json(bot=bot, event=event)
    if client_list := await get_clients(event=event, server_list=server_list):
        for client in client_list:
            if client and client.websocket:
                try:
                    await client.websocket.send(msgJson)
                except websockets.WebSocketException as e:
                    logger.error(f"[MC_QQ]丨发送至 [Server:{client.server_name}] 的过程中出现了错误：{e}")
                    CLIENTS.remove(client)
                else:
                    logger.success(f"[MC_QQ]丨发送至 [server:{client.server_name}] 的消息 \"{text_msg}\"")


async def get_clients(
        event: Union[GroupMessageEvent, GuildMessageEvent],
        server_list: list
) -> List[Client]:
    """获取 服务器名、ws客户端, 返回client列表"""
    res: List[Client] = []
    for per_client in CLIENTS:
        for per_server in server_list:
            # 如果 服务器名 == ws客户端中记录的服务器名，且ws客户端存在
            if per_server.server_name == per_client.server_name and per_client.websocket and (
                    per_client not in res):
                if isinstance(event, GroupMessageEvent):
                    if event.group_id in per_server.group_list:
                        res.append(per_client)
                if isinstance(event, GuildMessageEvent):
                    for per_guild in per_server.guild_list:
                        if per_guild.guild_id == event.guild_id and per_guild.channel_id == event.channel_id:
                            res.append(per_client)
    return res


async def remove_client(server_name: str):
    """移除客户端"""
    for client in CLIENTS:
        if client.server_name == server_name:
            await client.websocket.close()
            CLIENTS.remove(client)


async def send_msg_to_qq(
        bot: Bot,
        message: str,
        server_list: list,
        display_server_name: Optional[bool] = False,
):
    """
    发送消息到 QQ
    :param bot: Bot
    :param message: 消息
    :param server_list: 服务器列表
    :param display_server_name: 是否显示服务器名
    """
    await send_msg_to_qq_common(
        bot=bot,
        message=message,
        server_list=server_list,
        display_server_name=display_server_name,
        plugin_name="MC_QQ"
    )


async def msg_process_to_json(
        bot: Bot, event: Union[GroupMessageEvent, GuildMessageEvent],
        send_group_name: Optional[bool] = False
):
    """消息处理为 JSON"""
    # 获取昵称
    member_nickname = await get_member_nickname(bot, event, event.user_id)

    # 初始化消息
    text_msg = member_nickname + "说："

    # 初始化消息字典
    messageList = []

    # 发送群聊名称
    if send_group_name:
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
        messageList.append({"msgType": "group_name", "msgData": group_name})

    # 将群成员昵称装入消息列表
    messageList.append({"msgType": "senderName", "msgData": member_nickname})

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
        messageList.append(per_msg)

    return text_msg, str({"message": messageList})
