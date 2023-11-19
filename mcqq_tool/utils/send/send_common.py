"""
发送共用
"""
import contextlib
from typing import Union

from aiomcrcon import ClientNotConnectedError
from nonebot import logger

from ...config import plugin_config, Client, CLIENTS


async def remove_client(server_name: str):
    """
    移除客户端
    :param server_name: 服务器名
    """
    if client := CLIENTS.get(server_name):
        if client.websocket:
            with contextlib.suppress(Exception):
                await client.websocket.close()
        if client.rcon:
            await client.rcon.close()
        del CLIENTS[server_name]
        logger.info(f"[MC_QQ]丨[Server:{server_name}] 的 WebSocket 客户端已移除")


async def send_common_cmd_to_mc(client: Client, cmd: str) -> Union[str, None]:
    """
    准备发送通用命令到 MC
    :param client: 客户端
    :param cmd: 命令
    """
    server = plugin_config.mc_qq_server_dict.get(client.server_name)
    # 先判断是否有Rcon进行发送
    if client.rcon and server.rcon_cmd:
        return await send_common_cmd_to_mc_by_rcon(client=client, cmd=cmd)
    elif client.websocket:
        # await send_common_to_mc_by_ws(client=client, message=cmd)
        return "WebSocket 暂不支持发送命令"
    else:
        await remove_client(client.server_name)
    return None


async def send_common_cmd_to_mc_by_rcon(client: Client, cmd: str) -> Union[str, None]:
    """
    准备发送通用 Rcon 命令到 MC
    :param client:
    :param cmd:
    :return: 返回信息
    """
    try:
        back_msg = await client.rcon.send_cmd(cmd)
        logger.success(f"[MC_QQ_Rcon]丨发送至 [server:{client.server_name}] 的消息 \"{cmd}\"")
        return back_msg[0]
    except ClientNotConnectedError as e:
        logger.error(f"[MC_QQ_Rcon]丨发送至 [Server:{client.server_name}] 的过程中出现了错误：{e}")
        await remove_client(client.server_name)
    return None


async def send_common_to_mc_by_ws(client: Client, message: str) -> None:
    """
    准备发送通用 WebSocket 命令到 MC
    :param client:
    :param message:
    :return: 返回信息
    """
    await client.websocket.send_text(message)
    return None
