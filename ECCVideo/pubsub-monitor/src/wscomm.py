# import asyncio
# import websockets
# import json
import asyncio
import websockets
import json
import os
import globalvar as GlobalVar 

async def ws_send(msg):
    ws = GlobalVar.get_forward_client()
    send_txt = json.dumps(msg)
    print(send_txt)
    await ws.send(send_txt)
        # await websocket.recv()




# async def ws_send_msg(websocket, msg):
#     await websocket.send(msg)

# async def recv_msg(websocket,comm_queue):
#     while True:
#         recv_text = await websocket.recv()
#         print(f"{recv_text}")
#         print("recv_text type ", type(recv_text))
#         recv_text = json.loads(recv_text)
#         print("recv_text type", type(recv_text))
#         msg = {"comm":"ws","msg":recv_text}
#         comm_queue.put(msg)

ECCI_MONITOR_FORWARD_PORT = os.getenv("ECCI_MONITOR_FORWARD_PORT",default="8000")
ECCI_MONITOR_FORWARD_IP = os.getenv("ECCI_MONITOR_FORWARD_IP",default="api-server")

# 客户端主逻辑
async def main_logic():
    try:
        async with websockets.connect(f"ws://{ECCI_MONITOR_FORWARD_IP}:{ECCI_MONITOR_FORWARD_PORT}/ws/monitor/") as websocket:
            print("main_logic websocket id ", id(websocket))
            GlobalVar.set_forward_client(websocket)
            async for message in websocket:
                print(message)
    except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed) as e:
        print("websocket disconnect, error is "+str(e))
        os._exit(1)

def ws_forward_main():
    print("execute ws_main")
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    asyncio.get_event_loop().run_until_complete(main_logic())

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main_logic())