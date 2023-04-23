from pydantic import BaseModel


class BaseEvent(BaseModel):
    """事件基类"""
    post_type: str
    event_name: str
    server_name: str


class BasePlayer(BaseModel):
    """玩家信息基类"""
    nickname: str


class BaseMessageEvent(BaseEvent):
    """消息事件基类"""
    post_type = "message"
    player: BasePlayer


class BaseChatEvent(BaseMessageEvent):
    """玩家聊天事件基类"""
    sub_type = "chat"
    message: str


class BaseDeathEvent(BaseMessageEvent):
    """玩家死亡事件基类"""
    sub_type = "death"
    death_message: str


class BaseNoticeEvent(BaseEvent):
    """通知事件基类"""
    post_type = "notice"
    player: BasePlayer


class BaseJoinEvent(BaseNoticeEvent):
    """玩家加入事件基类"""
    sub_type = "join"


class BaseQuitEvent(BaseNoticeEvent):
    """玩家退出事件基类"""
    sub_type = "quit"
