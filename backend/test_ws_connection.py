import asyncio
import websockets
import json
import sys

async def test_websocket():
    # Use the correct WebSocket URL that we know works
    uri = "ws://127.0.0.1:8000/ws/deposit_status/address/5s9HUwUzaDWtJvGCuSns31QGgr8PLqdocuuGk4bkaBZK/"
    
    print(f"Attempting to connect to {uri}")
    
    try:
        # Set a timeout for the connection
        websocket = await asyncio.wait_for(websockets.connect(uri), timeout=5)
        print(f"Connected to {uri}")
        
        # Send a test message through the channel layer
        # This would normally be done from the Django application
        print("WebSocket connection established. Waiting for messages...")
        
        # Wait for messages for a short time
        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=10)
            print(f"Received: {message}")
        except asyncio.TimeoutError:
            print("No messages received within 10 seconds")
        
        # Close the connection
        await websocket.close()
        print("WebSocket connection closed")
            
    except asyncio.TimeoutError:
        print(f"Failed to connect: TimeoutError - Connection attempt timed out")
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"Failed to connect: Invalid status code {e.status_code}")
    except websockets.exceptions.NegotiationError as e:
        print(f"Failed to connect: Negotiation error {e}")
    except Exception as e:
        print(f"Failed to connect: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_websocket())