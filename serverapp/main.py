from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates 
from typing import List
import asyncio

app = FastAPI()

templates = Jinja2Templates(directory="templates") 


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


web_client_manager = ConnectionManager()

@app.websocket("/web_clinet/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
	await web_client_manager.connect(websocket)
	try:
		while True:
			await asyncio.sleep(0.1)
	except WebSocketDisconnect:
		web_client_manager.disconnect(websocket)

@app.get("/")
async def index():
	return templates.TemplateResponse("index.html", {})

@app.get("/check_server")
async def check_server():
	return {"message": "Hello World"}

