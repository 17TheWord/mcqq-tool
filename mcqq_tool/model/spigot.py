from typing import Optional
from .basemodel import BasePlayer, BaseChatEvent, BaseDeathEvent, BaseJoinEvent, BaseQuitEvent


class SpigotPlayer(BasePlayer):
    """玩家信息"""
    uuid: str
    display_name: str
    player_list_name: str
    is_health_scaled: bool
    address: Optional[str] = None
    is_sprinting: bool
    walk_speed: float
    fly_speed: float
    is_sneaking: bool
    level: int
    is_flying: bool
    ping: Optional[int] = None
    """Spigot API 1.12.2 Player 无 ping 属性"""
    allow_flight: bool
    locale: str
    health_scale: float
    player_time_offset: int
    exp: float
    total_exp: int
    player_time: int
    is_player_time_relative: bool


class AsyncPlayerChatEvent(BaseChatEvent):
    """Spigot API AsyncPlayerChatEvent"""
    event_name = "AsyncPlayerChatEvent"
    player: SpigotPlayer


class PlayerJoinEvent(BaseJoinEvent):
    """Spigot API PlayerJoinEvent"""
    event_name = "PlayerJoinEvent"
    player: SpigotPlayer


class PlayerQuitEvent(BaseQuitEvent):
    """Spigot API PlayerQuitEvent"""
    event_name = "PlayerQuitEvent"
    player: SpigotPlayer


class PlayerDeathEvent(BaseDeathEvent):
    """Spigot API PlayerDeathEvent"""
    event_name = "PlayerDeathEvent"
    player: SpigotPlayer
