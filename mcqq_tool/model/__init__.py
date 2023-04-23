from .basemodel import BaseEvent, BaseChatEvent, BaseDeathEvent, BaseJoinEvent, BaseQuitEvent
from .minecraft import MinecraftPlayerChatEvent, MinecraftPlayerJoinEvent, MinecraftPlayerQuitEvent
from .spigot import AsyncPlayerChatEvent, PlayerDeathEvent, PlayerJoinEvent, PlayerQuitEvent

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
}
