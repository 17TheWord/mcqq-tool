import json
from typing import Union

from nonebot import logger, get_bot
from nonebot.adapters.minecraft import Bot
from nonebot.adapters.qq import Bot as QQBot
from nonebot.adapters.qq import Message as QQMessage
from nonebot.adapters.onebot.v11 import Bot as OneBot
from nonebot.adapters.minecraft.utils import DataclassEncoder
from nonebot.adapters.onebot.v11 import Message as OneBotMessage
from nonebot.adapters.qq import GuildMessageEvent as QQGuildMessageEvent
from nonebot_plugin_guild_patch import GuildMessageEvent as OneBotGuildMessageEvent
from nonebot.adapters.onebot.v11 import GroupMessageEvent as OneBotGroupMessageEvent
from nonebot.adapters.qq import GroupAtMessageCreateEvent as QQGroupAtMessageCreateEvent

from .config import plugin_config
from .utils import get_title, get_rcon_result
from .parse_qq_msg import parse_qq_msg_to_base_model, parse_qq_msg_to_rcon_model
from .model import (
    QQ_GROUP_ID_LIST,
    QQ_GUILD_ID_LIST,
    ONEBOT_GROUP_ID_LIST,
    ONEBOT_GUILD_ID_LIST,
)


def get_mc_bot(server_name: str) -> Union[Bot, None]:
    """
    获取服务器 Bot
    :param server_name: 服务器名称
    :return: 服务器 Bot
    """
    try:
        return get_bot(server_name)
    except KeyError:
        logger.warning(f"[MC_QQ]丨未找到服务器 {server_name} 的 Bot")
    except ValueError:
        logger.warning(f"[MC_QQ]丨{server_name} 无可用 Bot")
    return None


def get_server_list(
        event: Union[
            QQGuildMessageEvent, QQGroupAtMessageCreateEvent, OneBotGroupMessageEvent, OneBotGuildMessageEvent
        ]
):
    if isinstance(event, QQGroupAtMessageCreateEvent):
        return QQ_GROUP_ID_LIST.get(event.group_id)
    elif isinstance(event, QQGuildMessageEvent):
        return QQ_GUILD_ID_LIST.get(event.channel_id)
    elif isinstance(event, OneBotGroupMessageEvent):
        return ONEBOT_GROUP_ID_LIST.get(str(event.group_id))
    else:
        return ONEBOT_GUILD_ID_LIST.get(f"{event.guild_id}:{event.channel_id}")


async def send_actionbar_to_target_server(
        event: Union[
            QQGuildMessageEvent, QQGroupAtMessageCreateEvent, OneBotGroupMessageEvent, OneBotGuildMessageEvent
        ],
        action_bar
):
    """
    发送actionbar到目标服务器
    :param event: 事件
    :param action_bar: actionbar
    :return: 去除末尾换行符的结果
    """
    result_log_text = "返回结果：\n"
    if server_list := get_server_list(event):
        for server_name in server_list:
            mc_bot = get_mc_bot(server_name)
            if not mc_bot:
                result_log_text += f"服务器 {server_name} 未连接\n"
                continue
            result_log_text += f"发送至服务器 {server_name} 的命令结果：\n"
            if server_config := plugin_config.server_dict.get(server_name):
                if mc_bot.rcon and server_config.rcon_cmd:
                    result = await mc_bot.send_rcon_cmd(command=f'title @a actionbar ["{action_bar.strip()}"]')
                    result_log_text += result[0]
                elif not mc_bot.rcon and server_config.rcon_msg:
                    result_log_text += "选择了Rcon发送命令，但Rcon未配置，无法发送ActionBar\n"
                else:
                    await mc_bot.send_actionbar(message=action_bar)
                    result_log_text += "结果：成功\n"
    return result_log_text.removesuffix("\n")


async def send_title_to_target_server(
        event: Union[
            QQGuildMessageEvent, QQGroupAtMessageCreateEvent, OneBotGroupMessageEvent, OneBotGuildMessageEvent
        ],
        title_message: str,
):
    """
    发送title到目标服务器
    :param event: 事件
    :param title_message: title
    :return: 去除末尾换行符的结果
    """
    result_log_text = "返回结果：\n"
    if server_list := get_server_list(event):
        for server_name in server_list:
            mc_bot = get_mc_bot(server_name)
            if not mc_bot:
                result_log_text += f"服务器 {server_name} 未连接\n"
                continue
            result_log_text += f"发送至服务器 {server_name} 的命令结果：\n"
            if server_config := plugin_config.server_dict.get(server_name):
                title, subtitle = get_title(title_message)
                if mc_bot.rcon and server_config.rcon_cmd:
                    title_result = await mc_bot.send_rcon_cmd(command=f'title @a title ["{title.strip()}"]')
                    result_log_text += title_result[0]
                    if subtitle:
                        subtitle_result = await mc_bot.send_rcon_cmd(
                            command=f'title @a subtitle ["{subtitle.strip()}"]')
                        result_log_text += subtitle_result[0]
                elif not mc_bot.rcon and server_config.rcon_cmd:
                    result_log_text += "选择了Rcon发送命令，但Rcon未配置，无法发送Title\n"
                else:
                    await mc_bot.send_title(title=title, subtitle=subtitle)
                    result_log_text += "结果：成功\n"
    return result_log_text.removesuffix("\n")


async def send_message_to_target_server(
        bot: Union[OneBot, QQBot],
        event: Union[
            QQGuildMessageEvent,
            QQGroupAtMessageCreateEvent,
            OneBotGroupMessageEvent,
            OneBotGuildMessageEvent
        ]
):
    """
    发送消息到目标服务器
    :param bot: Bot对象
    :param event: 事件
    :return: 去除末尾换行符的结果
    """
    result_log_text = "返回结果：\n"
    if server_list := get_server_list(event):
        for server_name in server_list:
            mc_bot = get_mc_bot(server_name)
            if not mc_bot:
                result_log_text += f"服务器 {server_name} 未连接\n"
                continue
            result_log_text += f"发送至服务器 {server_name} 的命令结果：\n"
            if server_config := plugin_config.server_dict.get(server_name):
                if mc_bot.rcon and server_config.rcon_msg:
                    message, log_text = await parse_qq_msg_to_rcon_model(bot=bot, event=event)
                    msg_json_data = json.dumps(message, cls=DataclassEncoder)
                    await mc_bot.send_rcon_cmd(command=f"tellraw @a {msg_json_data}")
                    result_log_text += log_text
                elif not mc_bot.rcon and server_config.rcon_msg:
                    result_log_text += "选择了Rcon发送消息，但Rcon未配置，无法发送消息\n"
                else:
                    message, log_text = await parse_qq_msg_to_base_model(bot=bot, event=event)
                    await mc_bot.send_msg(message=message)
                    result_log_text += log_text
    logger.debug(result_log_text)


async def send_command_to_target_server(
        event: Union[
            QQGuildMessageEvent,
            QQGroupAtMessageCreateEvent,
            OneBotGroupMessageEvent,
            OneBotGuildMessageEvent
        ],
        command: str
):
    if isinstance(event, QQGuildMessageEvent) or isinstance(event, QQGroupAtMessageCreateEvent):
        result_message = QQMessage()
    else:
        result_message = OneBotMessage()
    result_log_text = "返回结果：\n"
    result_message.append("返回结果：\n")
    if server_list := get_server_list(event):
        for server_name in server_list:
            mc_bot = get_mc_bot(server_name)
            if not mc_bot:
                result_log_text += f"服务器 {server_name} 未连接\n"
                result_message.append(f"服务器 {server_name} 未连接\n")
                continue
            result_log_text += f"发送至服务器 {server_name} 的命令结果：\n"
            result_message.append(f"发送至服务器 {server_name} 的命令结果：\n")
            if server_config := plugin_config.server_dict.get(server_name):
                if server_config.rcon_cmd and mc_bot.rcon:
                    result = await mc_bot.send_rcon_cmd(command=command)
                    rcon_result = get_rcon_result(result=result[0], event=event)
                    result_message.append(rcon_result)
                    result_log_text += result[0]
                elif not mc_bot.rcon and server_config.rcon_cmd:
                    result_log_text += "选择了Rcon发送命令，但Rcon未配置，无法发送命令\n"
                    result_message.append("选择了Rcon发送命令，但Rcon未配置，无法发送命令\n")
                else:
                    result_log_text += "选择了Websocket发送命令，但Websocket未支持，无法发送命令\n"
                    result_message.append("选择了Websocket发送命令，但Websocket未支持，无法发送命令\n")
    return result_message
