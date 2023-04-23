import aiomcrcon
import websockets
from typing import Optional, List, Dict
from pydantic import BaseModel, Extra, Field


class Client:
    """MC_QQ 客户端"""
    server_name: str
    websocket: websockets.WebSocketServerProtocol
    rcon: Optional[aiomcrcon.Client] = None

    def __init__(
            self, server_name: str,
            websocket: websockets.WebSocketServerProtocol,
            rcon: Optional[aiomcrcon.Client] = None
    ):
        self.server_name: str = server_name
        self.websocket: websockets.WebSocketServerProtocol = websocket
        self.rcon: Optional[aiomcrcon.Client] = rcon


CLIENTS: Dict[str, Client] = {}


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
    # 是否开启 Rcon
    rcon_enable: Optional[bool] = False


class Config(BaseModel, extra=Extra.ignore):
    """配置"""
    # 服务器地址
    mc_qq_ws_ip: Optional[str] = "127.0.0.1"
    # 服务器端口
    mc_qq_ws_port: Optional[int] = 8765
    # 是否发送群聊名称
    mc_qq_send_group_name: Optional[bool] = False
    # 是否显示服务器名称
    mc_qq_display_server_name: Optional[bool] = False
    # 服务器列表
    mc_qq_server_list: Optional[List[Server]] = Field(default_factory=list)
    # MCRcon 密码
    mc_qq_rcon_password: Optional[str] = "password"
    # Rcon 字典
    mc_qq_rcon_dict: Optional[Dict[str, int]] = Field(default_factory=dict)
    # MC_QQ 频道管理员身份组
    mc_qq_guild_admin_roles: Optional[List[str]] = ["频道主", "超级管理员"]
