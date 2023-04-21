from typing import Optional, List, Dict

from pydantic import BaseModel, Extra, Field


class Guild(BaseModel):
    """频道配置"""
    # 频道ID
    guild_id: int
    # 子频道ID
    channel_id: int


class Server(BaseModel):
    """服务器配置"""
    # 服务器名称
    server_name: str
    # 服务器群列表
    group_list: Optional[List[int]] = []
    # 服务器频道列表
    guild_list: Optional[List[Guild]] = []


class Config(BaseModel, extra=Extra.ignore):
    # 服务器地址
    mc_qq_ws_ip: Optional[str] = "127.0.0.1"
    # 服务器端口
    mc_qq_rcon_ws_port: Optional[int] = 8766
    # 是否发送群聊名称
    mc_qq_send_group_name: Optional[bool] = False
    # 是否显示服务器名称
    mc_qq_display_server_name: Optional[bool] = False
    # 服务器列表
    mc_qq_rcon_servers_list: Optional[List[Server]] = Field(default_factory=list)
    # MCRcon 密码
    mc_qq_rcon_password: Optional[str] = "password"
    # Rcon 字典
    mc_qq_rcon_rcon_dict: Optional[Dict[str, int]] = Field(default_factory=dict)
