from typing import Literal

from pydantic import BaseModel


class BaseEvent(BaseModel):
    """事件基类"""
    post_type: str
    event_name: str
    server_name: str
    sub_type: str


class BasePlayer(BaseModel):
    """玩家信息基类"""
    nickname: str


class BaseMessageEvent(BaseEvent):
    """消息事件基类"""
    post_type: Literal["message"]
    player: BasePlayer
    message: str


class BaseChatEvent(BaseMessageEvent):
    """玩家聊天事件基类"""
    sub_type: Literal["chat"]


class BasePlayerCommandEvent(BaseMessageEvent):
    """玩家执行命令事件基类"""
    sub_type: Literal["player_command"]


class BaseDeathEvent(BaseMessageEvent):
    """玩家死亡事件基类"""
    sub_type: Literal["death"]


class BaseNoticeEvent(BaseEvent):
    """通知事件基类"""
    post_type: Literal["notice"]
    player: BasePlayer


class BaseJoinEvent(BaseNoticeEvent):
    """玩家加入事件基类"""
    sub_type: Literal["join"]


class BaseQuitEvent(BaseNoticeEvent):
    """玩家退出事件基类"""
    sub_type: Literal["quit"]
