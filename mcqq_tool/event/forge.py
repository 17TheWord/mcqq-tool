from typing import Optional, Literal

from .base import (
    BasePlayer,
    BaseChatEvent,
    BaseDeathEvent,
    BaseJoinEvent,
    BaseQuitEvent
)


class Player(BasePlayer):
    """玩家信息"""
    nickname: Optional[str] = None
    uuid: Optional[str] = None
    ipAddress: Optional[str] = None
    level: Optional[str] = None
    """地图？"""
    speed: Optional[float] = None


class ForgeServerChatEvent(BaseChatEvent):
    """Forge API ServerChatEvent"""
    event_name: Literal["ForgeServerChatEvent"]
    player: Player


class ForgePlayerLoggedInEvent(BaseJoinEvent):
    """Forge API PlayerLoggedInEvent"""
    event_name: Literal["ForgePlayerLoggedInEvent"]
    player: Player


class ForgePlayerLoggedOutEvent(BaseQuitEvent):
    """Forge API PlayerLoggedOutEvent"""
    event_name: Literal["ForgePlayerLoggedOutEvent"]
    player: Player


class ForgePlayerRespawnEvent(BaseDeathEvent):
    """Forge API ForgePlayerRespawnEvent"""
    event_name: Literal["ForgePlayerRespawnEvent"]
    player: Player
