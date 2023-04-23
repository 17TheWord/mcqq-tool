from .basemodel import BasePlayer, BaseChatEvent, BaseJoinEvent, BaseQuitEvent


class MineCraftPlayer(BasePlayer):
    """原版 玩家信息"""


class MinecraftPlayerChatEvent(BaseChatEvent):
    """原版 玩家聊天事件"""
    event_name = "MinecraftPlayerChatEvent"
    player: MineCraftPlayer


class MinecraftPlayerJoinEvent(BaseJoinEvent):
    """原版 玩家加入事件"""
    event_name = "MinecraftPlayerJoinEvent"
    player: MineCraftPlayer


class MinecraftPlayerQuitEvent(BaseQuitEvent):
    """原版 玩家退出事件"""
    event_name = "MinecraftPlayerQuitEvent"
    player: MineCraftPlayer
