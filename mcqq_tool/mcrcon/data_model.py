import aiomcrcon
import websockets
from typing import List


class RconClient:
    """MC_QQ Rcon 客户端"""
    server_name: str
    websocket: websockets.WebSocketServerProtocol
    rcon: aiomcrcon.Client

    def __init__(self, server_name: str, websocket: websockets.WebSocketServerProtocol, rcon: aiomcrcon.Client):
        self.server_name: str = server_name
        self.websocket: websockets.WebSocketServerProtocol = websocket
        self.rcon: aiomcrcon.Client = rcon


RconCLIENTS: List[RconClient] = []
"""Rcon 客户端列表"""
