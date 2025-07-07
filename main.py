import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """<!DOCTYPE html>
<html>
    <head>
        <title>Chat + Svetafor</title>
        <style>
            #traffic-light {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background-color: gray;
                margin: 10px;
                border: 2px solid #000;
            }
        </style>
    </head>
    <body>
        <h1>Artyom BW Chat + Svetafor</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>

        <div id="traffic-light"></div>
        <button onclick="changeLight()">Toggle Svetafor</button>

        <form onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>

        <ul id='messages'></ul>

        <script>
            var client_id = Date.now();
            document.querySelector("#ws-id").textContent = client_id;

            var ws = new WebSocket(`ws://10.10.4.8:8000/ws/${client_id}`);
            var trafficLight = document.getElementById("traffic-light");

            var colors = ["red", "yellow", "green"];
            var currentColorIndex = 0;

            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);

                if (data.type === "message") {
                    var messages = document.getElementById('messages');
                    var message = document.createElement('li');
                    var content = document.createTextNode(data.content);
                    message.appendChild(content);
                    messages.appendChild(message);
                } else if (data.type === "light") {
                    trafficLight.style.backgroundColor = data.color;
                }
            };

            function sendMessage(event) {
                var input = document.getElementById("messageText");
                ws.send(JSON.stringify({ type: "message", content: input.value }));
                input.value = '';
                event.preventDefault();
            }

            function changeLight() {
                currentColorIndex = (currentColorIndex + 1) % colors.length;
                const newColor = colors[currentColorIndex];
                ws.send(JSON.stringify({ type: "light", color: newColor }));
            }
        </script>
    </body>
</html>
"""

# Basic functions
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

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


manager = ConnectionManager()


@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket) # websocket ulanishini qabul qilish
    try:
        while True:
            # Matn korinishida xabarni qabul qilish
            data = await websocket.receive_text()               # reseve_txt() str qaytarish

            # Json ni Pyhon dict ga aylantrish
            try:
                message_data = json.loads(data)                 # json.loads(data) str ni json ga aylantrish
            # Json bolmasa oddiy matn qilib qaytarish
            except json.JSONDecodeError:                        # agar json.loads(data) json chala yoki json bolmasa ushlash un
                message_data = {"type": "message", "content": data}

            # Xabar turini tekshirish va vazifani bajarish
            if message_data.get("type") == "message":           # Type ni get() bilan aniqlash u bn xavsizroq
                # Oddiy chat xabari
                content = message_data.get("content", "")
                response = json.dumps({
                    "type": "message",
                    "content": f"Foydalanuvchi: {client_id}\nXabar : {content}",
                })
                await manager.broadcast(response)

            elif message_data.get("type") == "light":           # Type ni get() bilan aniqlash u bn xavsizroq
                # Svetafor rangi
                color = message_data.get("color", "gray")
                response = json.dumps({
                    "type": "light",
                    "color": color,
                })
                # Barcha foydalanuvchilarga yangi rangni yuborish
                await manager.broadcast(response)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        # Foydalanuvchi chiqib ketganligi xaqida xabar
        disconnect_message = json.dumps({
            "type": "message",
            "content": f"Client {client_id} chatdan chiqib ketdi",
        })
        await manager.broadcast(disconnect_message)

# terminal run kode [  fastapi run main.py ]