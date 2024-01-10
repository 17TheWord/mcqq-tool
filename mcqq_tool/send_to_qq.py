from nonebot import logger, get_bots
from nonebot.adapters.onebot.v11 import Bot as OneBot
from nonebot.adapters.qq import Bot as QQBot, AuditException

from .config import plugin_config


async def send_mc_msg_to_qq(server_name: str, msg_result: str):
    if server := plugin_config.mc_qq_server_dict.get(server_name):
        if plugin_config.mc_qq_display_server_name:
            msg_result = f"[{server_name}] {msg_result}"

        for group in server.group_list:
            if bot := get_bots().get(group.bot_id):
                if group.adapter == "onebot":
                    bot: OneBot
                    await bot.send_group_msg(group_id=int(group.group_id), message=msg_result)
                elif group.adapter == "qq":
                    bot: QQBot
                    # TODO: 未实现，一个月主动就四条，还是算了吧。
                    # await bot.send_to_c2c(openid=group.group_id, message=msg_result)
                    logger.debug(f"[MC_QQ]丨未实现的适配器: {group.adapter}，发送至群聊 {group.group_id}失败：一个月主动就四条，还是算了吧。")
                else:
                    logger.error(f"[MC_QQ]丨未知的适配器: {group.adapter}")

        for guild in server.guild_list:
            if bot := get_bots().get(guild.bot_id):
                if guild.adapter == "onebot":
                    bot: OneBot
                    await bot.send_guild_channel_msg(
                        guild_id=guild.guild_id,
                        channel_id=guild.channel_id,
                        message=msg_result
                    )
                elif guild.adapter == "qq":
                    try:
                        bot: QQBot
                        await bot.send_to_channel(channel_id=guild.channel_id, message=msg_result)
                    except AuditException as e:
                        logger.debug(f"[MC_QQ]丨发送至子频道 {guild.channel_id} 的消息：{msg_result} 正在审核中")
                        audit_result = await e.get_audit_result(3)
                        logger.debug(f"[MC_QQ]丨审核结果：{audit_result.get_event_name()}")
    else:
        logger.error(f"未知的服务器: {server_name}")


__all__ = [
    "send_mc_msg_to_qq"
]
