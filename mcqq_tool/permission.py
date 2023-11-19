from nonebot.adapters.onebot.v11 import Bot as OneBot
from nonebot.adapters.qq import MessageCreateEvent
from nonebot.internal.permission import Permission
from nonebot_plugin_guild_patch import GuildMessageEvent

from .config import plugin_config


async def _onebot_guild_admin(
        bot: OneBot,
        event: GuildMessageEvent,
):
    """检测是否为 OneBot适配器 频道管理员"""
    roles = set(
        role["role_name"]
        for role in (
            await bot.get_guild_member_profile(
                guild_id=event.guild_id, user_id=event.user_id
            )
        )["roles"]
    )
    return bool(roles & set(plugin_config.mc_qq_guild_admin_roles))


async def _qq_guild_admin(
        event: MessageCreateEvent,
):
    """检测是否为 QQ适配器 频道管理员"""
    return bool(set(event.member.roles) & set(plugin_config.mc_qq_guild_admin_roles))


ONEBOT_GUILD_ADMIN: Permission = Permission(_onebot_guild_admin)
"""OneBot适配器 频道管理员权限"""
QQ_GUILD_ADMIN: Permission = Permission(_qq_guild_admin)
"""QQ适配器 频道管理员权限"""
