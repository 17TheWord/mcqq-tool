from .minecraft import MineCraftPlayerChatEvent, MinecraftPlayerJoinEvent, MinecraftPlayerQuitEvent
from .spigot import AsyncPlayerChatEvent, PlayerDeathEvent, PlayerJoinEvent, PlayerQuitEvent

event_dict = {
    # 原版
    "MinecraftPlayerJoinEvent": MinecraftPlayerJoinEvent,
    "MinecraftPlayerQuitEvent": MinecraftPlayerQuitEvent,
    "MineCraftPlayerChatEvent": MineCraftPlayerChatEvent,
    # Spigot
    "AsyncPlayerChatEvent": AsyncPlayerChatEvent,
    "PlayerDeathEvent": PlayerDeathEvent,
    "PlayerJoinEvent": PlayerJoinEvent,
    "PlayerQuitEvent": PlayerQuitEvent,
}
