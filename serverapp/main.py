from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates 
from typing import List
import asyncio
import json
import numpy as np
from pickle import dumps, loads
from util.image_code import image_to_base64

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
class RPiConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.img: dict = {}

    async def connect(self, websocket: WebSocket, rpi_id: int):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.img[rpi_id] = np.zeros((480, 640, ), dtype=np.uint8)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)
rpi_client_manager = RPiConnectionManager()
web_client_manager = ConnectionManager()

@app.websocket("/rpi/{client_id}")
async def rpi_endpoint(websocket: WebSocket, client_id: int):
    await rpi_client_manager.connect(websocket, client_id)
    data = await websocket.receive_text()
    if data == "Raspberry Pi Hello":
        await rpi_client_manager.send_personal_message("Web Server Hello", websocket)
    try:
        while True:
            buffer_matrix = await websocket.receive_bytes()
            coord = loads(buffer_matrix)
            try:
                if coord.shape == (1,):
                    # print("coord success")
                    await rpi_client_manager.send_personal_message("OK", websocket)
                else:
                    print(coord.shape)
                
            except:
                print("Error")
            buffer_matrix = await websocket.receive_bytes()
            image = loads(buffer_matrix)
            try:
                if image.shape == (480, 640, ):
                    rpi_client_manager.img[client_id] = image
                    await rpi_client_manager.send_personal_message("OK", websocket)
                else:
                    print(image.shape)
            except:
                print("Error")
    except WebSocketDisconnect:
        rpi_client_manager.disconnect(websocket)
        await web_client_manager.broadcast("RPI Disconnected")

@app.websocket("/web_client/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await web_client_manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(0.1)
            await websocket.send_bytes(image_to_base64(rpi_client_manager.img[client_id]))
    except WebSocketDisconnect:
        web_client_manager.disconnect(websocket)

@app.get("/")
async def index():
	return templates.TemplateResponse("index.html", {})

@app.get("/check_server")
async def check_server():
	return {"message": "Hello World"}

