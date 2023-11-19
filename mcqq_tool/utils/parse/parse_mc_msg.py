"""
格式化MC消息
"""

import json

from nonebot import logger
from nonebot.adapters.qq import ActionFailed

from ..send import (
    send_msg_to_onebot_group,
    send_msg_to_onebot_guild,
    send_msg_to_qq_guild
)
from ...config import Server, plugin_config
from ...event import (
    event_dict,
    BaseEvent,
    BaseChatEvent,
    BaseDeathEvent,
    BaseJoinEvent,
    BaseQuitEvent,
    BasePlayerCommandEvent
)


def _msg_to_qq_process(event: BaseEvent) -> str:
    """处理来自MC的消息，并返回处理后的消息"""
    if isinstance(event, BaseChatEvent):
        return f"{event.player.nickname} 说：{event.message}"
    elif isinstance(event, BaseDeathEvent):
        return f"{event.player.nickname} {event.message}"
    elif isinstance(event, BaseJoinEvent):
        return f"{event.player.nickname} 加入了游戏"
    elif isinstance(event, BaseQuitEvent):
        return f"{event.player.nickname} 离开了游戏"
    elif isinstance(event, BasePlayerCommandEvent):
        # return f"{event.player.nickname} 执行了命令：{event.message}"
        # logger.info(f"[MC_QQ]丨from [{event.server_name}] {event.player.nickname} 执行了命令：{event.message}")
        return ""
    else:
        return ""


async def send_msg_from_mc_common(message: str):
    """处理来自MC的消息，并准备发送"""
    json_msg = json.loads(message)
    event = event_dict[json_msg["event_name"]].parse_obj(json_msg)

    if not (msg := _msg_to_qq_process(event_dict[json_msg["event_name"]].parse_obj(json_msg))):
        return

    if plugin_config.mc_qq_display_server_name:
        msg = f"[{event.server_name}] {msg}"

    # 从服务器字典中获取服务器对应的群聊信息并发送
    if per_server := plugin_config.mc_qq_server_dict.get(event.server_name):
        per_server: Server  # 标记类型
        for per_group in per_server.group_list:
            # 判断发送的目标群聊是否为 OneBot适配器
            if per_group.adapter == "onebot":
                await send_msg_to_onebot_group(
                    bot_id=str(per_group.bot_id),
                    group_id=per_group.group_id,
                    server_name=event.server_name,
                    message=msg
                )
            # TODO 判断发送的目标群聊是否为 QQ适配器，群私域 Bot 暂未开放
            # elif per_group.adapter == "qq":
            #     await bot.send_private_msg(
            #         user_id=per_group,
            #         message=msg
            #     )
            #     logger.info(f"[MC_QQ]丨from [{event.server_name}] to [群:{per_group}] \"{msg}\"")
        # 判断是否发送到频道
        for per_guild in per_server.guild_list:
            # 判断发送的目标频道是否为 OneBot适配器
            if per_guild.adapter == "onebot":
                await send_msg_to_onebot_guild(
                    server_name=event.server_name,
                    bot_id=str(per_guild.bot_id),
                    guild_id=per_guild.guild_id,
                    channel_id=per_guild.channel_id,
                    message=msg
                )
            elif per_guild.adapter == "qq":
                try:
                    await send_msg_to_qq_guild(
                        server_name=event.server_name,
                        bot_id=str(per_guild.bot_id),
                        channel_id=str(per_guild.channel_id),
                        message=msg
                    )
                except ActionFailed as e:
                    logger.debug(f"[MC_QQ]丨发送到频道的消息在审核中")
