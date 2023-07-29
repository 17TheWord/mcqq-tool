from .basemodel import BasePlayer, BaseChatEvent, BaseDeathEvent, BaseJoinEvent, BaseQuitEvent


class ForgePlayer(BasePlayer):
    """玩家信息"""
    nickname: str
    uuid: str
    ipAddress: str
    level: str
    """地图？"""
    speed: float


class ForgeServerChatEvent(BaseChatEvent):
    """Forge API ServerChatEvent"""
    event_name = "ServerChatEvent"
    player: ForgePlayer


class ForgePlayerLoggedInEvent(BaseJoinEvent):
    """Forge API PlayerLoggedInEvent"""
    event_name = "ForgePlayerLoggedInEvent"
    player: ForgePlayer


class ForgePlayerLoggedOutEvent(BaseQuitEvent):
    """Forge API PlayerLoggedOutEvent"""
    event_name = "ForgePlayerLoggedOutEvent"
    player: ForgePlayer


class ForgePlayerRespawnEvent(BaseDeathEvent):
    """Forge API ForgePlayerRespawnEvent"""
    event_name = "ForgePlayerRespawnEvent"
    player: ForgePlayer
