import asyncio
import websockets
import json
import os
import globalvar as GlobalVar 

async def ws_send_msg(websocket, msg):
    await websocket.send(msg)

async def recv_msg(websocket,comm_queue):
    while True:
        recv_text = await websocket.recv()
        print(f"{recv_text}")
        print("recv_text type ", type(recv_text))
        recv_text = json.loads(recv_text)
        print("recv_text type", type(recv_text))
        msg = {"comm":"ws","msg":recv_text}
        comm_queue.put(msg)
        
# 客户端主逻辑
async def main_logic(comm_queue = None):
    ECCI_CONTROLLER_WS_IP = os.getenv("ECCI_CONTROLLER_WS_IP","api-server")
    # ECCI_CONTROLLER_WS_IP = "api-server"
    ECCI_CONTROLLER_WS_PORT = int(os.getenv("ECCI_CONTROLLER_WS_PORT",8000))
    try:
        async with websockets.connect(f"ws://{ECCI_CONTROLLER_WS_IP}:{ECCI_CONTROLLER_WS_PORT}/ws/controller/") as websocket:
        # async with websockets.connect("ws://api-server:8000/ws/controller/") as websocket:
            print("main_logic websocket id ", id(websocket))
            GlobalVar.set_ws_client(websocket)
            await recv_msg(websocket,comm_queue)
    except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed) as e:
        print("websocket disconnect, error is "+str(e))
        os._exit(1)

def ws_main(comm_queue=None):
    print("execute ws_main")
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    asyncio.get_event_loop().run_until_complete(main_logic(comm_queue))

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main_logic())