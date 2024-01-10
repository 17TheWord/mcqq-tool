"""
配置文件
"""

from typing import Optional, List, Dict

from nonebot import get_driver
from pydantic import BaseModel, Extra, Field


class Guild(BaseModel):
    """频道配置"""
    # 频道ID，QQ适配器不需要频道ID
    guild_id: Optional[str] = None
    # 子频道ID
    channel_id: str
    # 适配器类型
    adapter: Optional[str] = None
    # Bot ID 优先使用所选Bot发送消息
    bot_id: Optional[str] = None


class Group(BaseModel):
    """群配置"""
    # 群ID
    group_id: str
    # 适配器类型
    adapter: Optional[str] = None
    # Bot ID
    bot_id: Optional[str] = None


class Server(BaseModel):
    """服务器配置"""
    # 服务器群列表
    group_list: Optional[List[Group]] = []
    # 服务器频道列表
    guild_list: Optional[List[Guild]] = []
    # 是否开启 Rcon 消息
    rcon_msg: Optional[bool] = False
    # 是否开启 Rcon 命令
    rcon_cmd: Optional[bool] = False


class Config(BaseModel, extra=Extra.ignore):
    """配置"""
    # 是否发送群聊名称
    mc_qq_send_group_name: Optional[bool] = False
    # 是否发送频道名称
    mc_qq_send_guild_name: Optional[bool] = False
    # 是否发送子频道名称
    mc_qq_send_channel_name: Optional[bool] = False
    # 是否显示服务器名称
    mc_qq_display_server_name: Optional[bool] = False
    # 服务器列表字典
    mc_qq_server_dict: Optional[Dict[str, Server]] = Field(default_factory=dict)
    # MC_QQ 频道管理员身份组
    mc_qq_guild_admin_roles: Optional[List[str]] = ["频道主", "超级管理员"]
    # MC_QQ 启用 ChatImage MOD
    mc_qq_chat_image_enable: Optional[bool] = False
    # MC_QQ Rcon 启用 ClickAction
    mc_qq_rcon_click_action_enable: Optional[bool] = False
    # MC_QQ Rcon 启用 HoverEvent
    mc_qq_rcon_hover_event_enable: Optional[bool] = False
    # MC_QQ Rcon TextComponent 启用状态
    mc_qq_rcon_text_component_status: Optional[int] = 1
    # MC_QQ 命令白名单
    mc_qq_cmd_whitelist: Optional[List[str]] = ["list", "tps", "banlist"]


plugin_config: Config = Config.parse_obj(get_driver().config)

__all__ = [
    "Group",
    "Guild",
    "Server",
    "Config",
    "plugin_config",
]
