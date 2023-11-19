"""
发送消息
"""

from typing import Union

from nonebot import logger, get_bot
from nonebot.adapters.onebot.v11 import Bot as OneBot
from nonebot.adapters.qq import Bot as QQBot
from nonebot.exception import FinishedException


def _get_available_bot(bot_id: str, server_name: str) -> Union[OneBot, QQBot]:
    """
    获取可用 Bot
    :param bot_id: Bot ID
    :param server_name: 服务器名
    :return: Bot
    """
    try:
        bot = get_bot(bot_id)
    except KeyError as e:
        logger.warning(
            f"[MC_QQ]丨Server: {server_name} 的 Bot {bot_id} 不存在，将尝试使用其他Bot发送信息"
        )
        try:
            bot = get_bot()
        except ValueError as e:
            logger.warning(
                f"[MC_QQ]丨当前无其他Bot可用，将跳过发送 Server: {server_name} 的信息"
            )
            raise FinishedException
    except ValueError as e:
        logger.warning(
            f"[MC_QQ]丨当前无其他Bot可用，将跳过发送 Server: {server_name} 的信息"
        )
        raise FinishedException
    return bot


async def send_msg_to_onebot_group(bot_id: str, group_id: int, server_name: str, message: str):
    """
    发送消息到 OneBot 适配器群聊
    :param server_name: 服务器名
    :param bot_id: Bot ID
    :param group_id: 群号
    :param message: 消息
    :return:
    """
    bot: OneBot = _get_available_bot(bot_id=bot_id, server_name=server_name)
    await bot.send_group_msg(
        group_id=group_id,
        message=message
    )
    logger.info(f"[MC_QQ]丨from [{server_name}] to [群:{group_id}] \"{message}\"")


async def send_msg_to_onebot_guild(bot_id: str, guild_id: int, channel_id: int, server_name: str, message: str):
    """
    发送消息到 OneBot 适配器频道
    :param server_name:
    :param channel_id:
    :param bot_id:
    :param guild_id:
    :param message:
    :return:
    """
    bot: OneBot = _get_available_bot(bot_id=bot_id, server_name=server_name)
    await bot.send_guild_channel_msg(
        guild_id=guild_id,
        channel_id=channel_id,
        message=message
    )
    logger.info(
        f"[MC_QQ]丨from [{server_name}] to [频道:{guild_id}/{channel_id}] \"{message}\""
    )


async def send_msg_to_qq_guild(bot_id: str, channel_id: str, server_name: str, message: str):
    """
     发送消息到 QQ 适配器频道
    :param server_name: 服务器名
    :param bot_id: Bot ID
    :param channel_id: 频道号
    :param message: 消息
    :return:
    """
    bot = _get_available_bot(bot_id=bot_id, server_name=server_name)
    await bot.send_to_channel(
        channel_id=channel_id,
        message=message
    )
    logger.info(
        f"[MC_QQ]丨from [{server_name}] to [频道:{channel_id}] \"{message}\""
    )
