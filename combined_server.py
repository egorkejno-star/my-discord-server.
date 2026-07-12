import asyncio
import os
import websockets

# Render автоматически выдает порт в переменную среды PORT
PORT = int(os.environ.get("PORT", 55555))

# Храним подключенных клиентов: {websocket: nickname}
CLIENTS = {}

# Обработчик обычных HTTP/HEAD запросов для проверок Render
async def health_check(path, request_headers):
    if path == "/":
        return websockets.http.HTTPStatus.OK, [], b"OK"
    return None

async def broadcast(message, exclude_ws=None):
    if CLIENTS:
        targets = [ws for ws in CLIENTS if ws != exclude_ws]
        if targets:
            await asyncio.gather(*[ws.send(message) for ws in targets], return_exceptions=True)

async def handle_client(websocket):
    try:
        nickname = await websocket.recv()
        CLIENTS[websocket] = nickname
        print(f"[Сервер]: @{nickname} подключился.")
        await broadcast(f"[Сервер]: @{nickname} ворвался в чат!", exclude_ws=websocket)
    except Exception as e:
        print(f"Ошибка при авторизации: {e}")
        return

    try:
        async for message in websocket:
            await broadcast(message, exclude_ws=websocket)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if websocket in CLIENTS:
            nick = CLIENTS[websocket]
            del CLIENTS[websocket]
            print(f"[Сервер]: @{nick} отключился.")
            await broadcast(f"[Сервер]: @{nick} покинул чат!")

async def main():
    print(f"Сервер WebSocket запускается на порту {PORT}...")
    # Привязываем health_check к серверу
    async with websockets.serve(handle_client, "0.0.0.0", PORT, process_request=health_check):
        await asyncio.Future() # Держим сервер запущенным

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Сервер остановлен.")
