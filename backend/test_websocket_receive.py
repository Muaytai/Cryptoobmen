import asyncio
import websockets
import json
import time

async def test_websocket_receive():
    # Use the same URL pattern as in the frontend
    uri = "ws://localhost:8000/ws/deposit_status/address/9FadeNnX2pVag1g9Yc7Tjsj8vhYyig6jp56faf8GsC3M/"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}")
            print("Waiting for messages...")
            
            # Wait for a few messages
            for i in range(5):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    print(f"Received message {i+1}: {message}")
                    
                    # Parse the message
                    data = json.loads(message)
                    print(f"Parsed data: {data}")
                except asyncio.TimeoutError:
                    print("No message received within 10 seconds")
                    break
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket_receive())