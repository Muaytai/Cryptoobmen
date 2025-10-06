import asyncio
import websockets
import json

async def test_websocket():
    # Use the same URL pattern as in the frontend
    uri = "ws://localhost:8000/ws/deposit_status/address/9FadeNnX2pVag1g9Yc7Tjsj8vhYyig6jp56faf8GsC3M/"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}")
            print("Waiting for messages...")
            
            # Wait for a message
            message = await websocket.recv()
            print(f"Received message: {message}")
            
            # Parse the message
            data = json.loads(message)
            print(f"Parsed data: {data}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())