import asyncio
import os
import websockets

# Render автоматически выдает порт в переменную среды PORT
PORT = int(os.environ.get("PORT", 55555))

# Храним подключенных клиентов: {websocket: nickname}
CLIENTS = {}

async def broadcast(message, exclude_ws=None):
    if CLIENTS:
        # Создаем список задач на отправку всем, кроме автора сообщения
        targets = [ws for ws in CLIENTS if ws != exclude_ws]
        if targets:
            await asyncio.gather(*[ws.send(message) for ws in targets], return_exceptions=True)

async def handle_client(websocket):
    # Ожидаем первое сообщение — никнейм
    try:
        nickname = await websocket.recv()
        CLIENTS[websocket] = nickname
        print(f"[Сервер]: @{nickname} подключился.")
        await broadcast(f"[Сервер]: @{nickname} ворвался в чат!", exclude_ws=websocket)
    except Exception as e:
        print(f"Ошибка при авторизации: {e}")
        return

    # Цикл обработки сообщений (и текст, и голос летят через один канал)
    try:
        async for message in websocket:
            # Если это строка (текст), пересылаем как текст, если байты (голос) — как байты
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
    async with websockets.serve(handle_client, "0.0.0.0", PORT):
        await asyncio.Future() # Держим сервер запущенным

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Сервер остановлен.")
