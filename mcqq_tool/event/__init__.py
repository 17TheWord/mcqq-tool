"""
事件包
"""

from .base import (
    BaseEvent,
    BasePlayer,
    BaseMessageEvent,
    BaseChatEvent,
    BasePlayerCommandEvent,
    BaseNoticeEvent,
    BaseDeathEvent,
    BaseJoinEvent,
    BaseQuitEvent
)
from .forge import (
    Player as ForgePlayer,
    ForgePlayerLoggedInEvent,
    ForgePlayerLoggedOutEvent,
    ForgeServerChatEvent,
    ForgePlayerRespawnEvent
)
from .minecraft import (
    Player as MinecraftPlayer,
    MinecraftPlayerChatEvent,
    MinecraftPlayerJoinEvent,
    MinecraftPlayerQuitEvent
)
from .spigot import (
    Player as SpigotPlayer,
    AsyncPlayerChatEvent,
    PlayerDeathEvent,
    PlayerJoinEvent,
    PlayerQuitEvent,
    PlayerCommandPreprocessEvent
)

event_dict = {
    # 原版
    "MinecraftPlayerJoinEvent": MinecraftPlayerJoinEvent,
    "MinecraftPlayerQuitEvent": MinecraftPlayerQuitEvent,
    "MinecraftPlayerChatEvent": MinecraftPlayerChatEvent,
    # Spigot
    "AsyncPlayerChatEvent": AsyncPlayerChatEvent,
    "PlayerDeathEvent": PlayerDeathEvent,
    "PlayerJoinEvent": PlayerJoinEvent,
    "PlayerQuitEvent": PlayerQuitEvent,
    "PlayerCommandPreprocessEvent": PlayerCommandPreprocessEvent,
    # Forge
    "ForgeServerChatEvent": ForgeServerChatEvent,
    "ForgePlayerLoggedInEvent": ForgePlayerLoggedInEvent,
    "ForgePlayerLoggedOutEvent": ForgePlayerLoggedOutEvent,
    "ForgePlayerRespawnEvent": ForgePlayerRespawnEvent,
}
