import asyncio
import websockets

async def test():
    try:
        async with websockets.connect('ws://127.0.0.1:8000/ws/telemetry') as ws:
            print('Connected!')
            for i in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                print('Received:', msg[:100])
    except Exception as e:
        print("Error:", e)

asyncio.run(test())
