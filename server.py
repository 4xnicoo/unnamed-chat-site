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

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Serve static files
app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")

@app.get("/")
async def get_index():
    return FileResponse(
        os.path.join(BASE_DIR, "index.html"),
        media_type="text/html"
    )

@app.get("/style.css")
async def get_style():
    return FileResponse(
        os.path.join(BASE_DIR, "style.css"),
        media_type="text/css"
    )

@app.get("/script.js")
async def get_script():
    return FileResponse(
        os.path.join(BASE_DIR, "script.js"),
        media_type="application/javascript"
    )

@app.get("/health")
async def health_check():
    return {"status": "ok"}

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
        
        # Send confirmation to the user with current user list
        current_users = [
            {"username": user_data[conn]["username"], "color": user_data[conn]["color"]}
            for conn in active_connections if conn in user_data
        ]
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "You joined the chat!",
            "users": current_users
        }))
        
        # Broadcast updated user list to all clients
        await broadcast_user_list()
        
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
        # Broadcast updated user list after user leaves
        await broadcast_user_list()

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

async def broadcast_user_list():
    """Broadcast the current user list to all connected clients"""
    current_users = [
        {"username": user_data[conn]["username"], "color": user_data[conn]["color"]}
        for conn in active_connections if conn in user_data
    ]
    user_list_message = {
        "type": "user_list",
        "users": current_users
    }
    await broadcast_message(user_list_message)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

