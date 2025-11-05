from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import asyncio
from typing import Set, Dict
import os

app = FastAPI()

# Store active connections
active_connections: Set[WebSocket] = set()
# Store user info (websocket -> user data)
user_data: Dict[WebSocket, Dict] = {}

# Serve static files
static_dir = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def get_index():
    return FileResponse("index.html")

@app.get("/style.css")
async def get_style():
    return FileResponse("style.css")

@app.get("/script.js")
async def get_script():
    return FileResponse("script.js")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    
    try:
        # Wait for user to send their name and color
        data = await websocket.receive_text()
        user_info = json.loads(data)
        username = user_info.get("username", "Anonymous")
        color = user_info.get("color", "#000000")
        
        user_data[websocket] = {
            "username": username,
            "color": color
        }
        
        # Broadcast that user joined
        join_message = {
            "type": "join",
            "username": username,
            "color": color,
            "message": f"{username} joined the chat"
        }
        await broadcast_message(join_message, exclude=websocket)
        
        # Send confirmation to the user
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "You joined the chat!"
        }))
        
        # Listen for messages
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "message":
                broadcast_data = {
                    "type": "message",
                    "username": username,
                    "color": color,
                    "message": message_data.get("message", "")
                }
                await broadcast_message(broadcast_data)
                
    except WebSocketDisconnect:
        # User disconnected
        if websocket in user_data:
            username = user_data[websocket]["username"]
            leave_message = {
                "type": "leave",
                "username": username,
                "message": f"{username} left the chat"
            }
            await broadcast_message(leave_message, exclude=websocket)
            del user_data[websocket]
        active_connections.discard(websocket)

async def broadcast_message(message: dict, exclude: WebSocket = None):
    """Broadcast a message to all connected clients except the excluded one"""
    message_json = json.dumps(message)
    disconnected = set()
    
    for connection in active_connections:
        if connection != exclude:
            try:
                await connection.send_text(message_json)
            except:
                disconnected.add(connection)
    
    # Clean up disconnected clients
    for connection in disconnected:
        active_connections.discard(connection)
        if connection in user_data:
            del user_data[connection]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

