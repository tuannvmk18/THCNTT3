from typing import List, Optional

from fastapi import Cookie, Depends, FastAPI, Query, WebSocket, status, Request, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient
from bson.json_util import dumps

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

client = MongoClient(
    "mongodb+srv://Admin:01664983385TUan@chatrealtime.jvz5x.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client['mydb']
message_cl = db['messages']


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

    async def broadcast(self, payload):
        for connection in self.active_connections:
            await connection.send_json(payload)


manager = ConnectionManager()


@app.get("/get-messages")
def get_messages():
    payload = message_cl.find({})
    return dumps(payload)


@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


async def get_cookie_or_token(
    websocket: WebSocket,
    session: Optional[str] = Cookie(None),
    token: Optional[str] = Query(None),
):
    if session is None and token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    return session or token


@app.websocket("/client/{client_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    chatrom_id: str,
    cookie_or_token: str = Depends(get_cookie_or_token),
):
    await manager.connect(websocket)
    try: 
        while True:
            data = await websocket.receive_text()
            message_cl.save({
                u'token': cookie_or_token,
                u'message': data,
            })
            await manager.broadcast({
                u'token': cookie_or_token,
                u'message': data
            })
    except WebSocketDisconnect:
        pass
