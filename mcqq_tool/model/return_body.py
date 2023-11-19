"""
返回体
"""

from __future__ import annotations

import json
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class ActionEvent(BaseModel):
    """
    点击事件
    """
    click_event_url: Optional[str] = None
    hover_event_text: Optional[str] = None


class TextColor(Enum):
    """
    颜色枚举
    """
    BLACK = "black"
    DARK_BLUE = "dark_blue"
    DARK_GREEN = "dark_green"
    DARK_AQUA = "dark_aqua"
    DARK_RED = "dark_red"
    DARK_PURPLE = "dark_purple"
    GOLD = "gold"
    GRAY = "gray"
    DARK_GRAY = "dark_gray"
    BLUE = "blue"
    GREEN = "green"
    AQUA = "aqua"
    RED = "red"
    LIGHT_PURPLE = "light_purple"
    YELLOW = "yellow"
    WHITE = "white"


class MessageItem(BaseModel):
    """
    消息体
    """
    msg_text: Optional[str] = None
    color: Optional[TextColor] = None
    action_event: Optional[ActionEvent] = None


class WebSocketSendBody(BaseModel):
    """
    websocket 发送消息的body
    """
    message: List[MessageItem] = []


class ChatImageModel(BaseModel):
    """
    ChatImage Mod 图片
    """
    url: Optional[str] = None
    name: Optional[str] = None

    def __str__(self):
        return f"[[CICode,url={self.url}]]"


"""
Rcon
"""


class RconClickEventEnum(Enum):
    """
    点击事件枚举
    """
    OPEN_URL = "open_url"
    OPEN_FILE = "open_file"
    RUN_COMMAND = "run_command"
    SUGGEST_COMMAND = "suggest_command"
    CHANGE_PAGE = "change_page"  # 仅用于书翻页
    COPY_TO_CLIPBOARD = "copy_to_clipboard"


class RconHoverEventEnum(Enum):
    """
    悬停事件枚举
    """
    SHOW_TEXT = "show_text"
    SHOW_ITEM = "show_item"
    SHOW_ENTITY = "show_entity"


class RconFontEnum(Enum):
    """
    字体枚举
    """
    DEFAULT = "minecraft:default"


class RconClickEvent(BaseModel):
    """
    点击事件
    """
    action: Optional[RconClickEventEnum] = None
    value: Optional[str] = None


class RconBaseComponent(BaseModel):
    """
    基本组件
    """
    text: Optional[str] = None
    color: Optional[TextColor] = None
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underlined: Optional[bool] = None
    strikethrough: Optional[bool] = None
    obfuscated: Optional[bool] = None
    insertion: Optional[str] = None
    font: Optional[RconFontEnum] = None
    score: Optional[dict] = None
    selector: Optional[str] = None
    block: Optional[str] = None
    translate: Optional[str] = None


class RconHoverEvent(BaseModel):
    """
    悬停事件
    """
    action: Optional[RconHoverEventEnum] = None
    contents: Optional[List[RconBaseComponent]] = None


class RconTextComponent(RconBaseComponent):
    """
    文本组件
    """
    click_event: Optional[RconClickEvent] = None
    hover_event: Optional[RconHoverEvent] = None


class RconSendBody(BaseModel):
    """
    rcon 发送消息的body
    """
    message: List[RconTextComponent] = []

    def get_tellraw(self) -> str:
        """
        获取tellraw命令
        :return:
        """
        # 将body中包含None的字段删除
        body_list = json.loads(self.json()).get("message")
        for i in body_list:
            for k, v in list(i.items()):
                if v is None:
                    del i[k]
        # 在首位置添加一个空字符串
        return f"tellraw @a {json.dumps(body_list)}"
