from typing import List

import websockets


class Client:
    """MC_QQ Rcon 客户端"""
    server_name: str
    websocket: websockets.WebSocketServerProtocol

    def __init__(self, server_name: str, websocket: websockets.WebSocketServerProtocol):
        self.server_name: str = server_name
        self.websocket: websockets.WebSocketServerProtocol = websocket


CLIENTS: List[Client] = []
