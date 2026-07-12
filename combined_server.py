import asyncio
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

app = FastAPI()

# Храним активные подключения: {websocket: nickname}
CLIENTS = {}

# Этот роут будет автоматически отвечать на пинги Render (200 OK)
@app.get("/")
async def health_check():
    return {"status": "working"}

@app.head("/")
async def health_check_head():
    return None

async def broadcast(message, exclude_ws=None):
    if CLIENTS:
        for ws in list(CLIENTS.keys()):
            if ws != exclude_ws:
                try:
                    if isinstance(message, str):
                        await ws.send_text(message)
                    else:
                        await ws.send_bytes(message)
                except Exception:
                    # Если клиент отвалился во время отправки
                    if ws in CLIENTS:
                        del CLIENTS[ws]

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Первое сообщение от клиента — никнейм
    try:
        nickname = await websocket.receive_text()
        CLIENTS[websocket] = nickname
        print(f"[Сервер]: @{nickname} подключился.")
        await broadcast(f"[Сервер]: @{nickname} ворвался в чат!", exclude_ws=websocket)
    except Exception as e:
        print(f"Ошибка авторизации: {e}")
        await websocket.close()
        return

    # Цикл приёма сообщений
    try:
        while True:
            data = await websocket.receive()
            if "text" in data:
                await broadcast(data["text"], exclude_ws=websocket)
            elif "bytes" in data:
                await broadcast(data["bytes"], exclude_ws=websocket)
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in CLIENTS:
            nick = CLIENTS[websocket]
            del CLIENTS[websocket]
            print(f"[Сервер]: @{nick} отключился.")
            await broadcast(f"[Сервер]: @{nick} покинул чат!")

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 55555))
    uvicorn.run("combined_server:app", host="0.0.0.0", port=PORT, log_level="info")
