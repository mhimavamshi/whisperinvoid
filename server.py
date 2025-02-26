import asyncio
from aiohttp import web  
import aiofiles
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed
import os
import json
import random

class User:
    def __init__(self, websocket, adjectives):
        # self.id = self.generate_id()
        # self.generate_id()
        # self.name = self.generate_name(adjectives)
        # self.generate_name(adjectives)
        self.generate_all(adjectives)
        self.socket = websocket 

    def generate_all(self, adjectives):
        self.generate_id()
        self.generate_name(adjectives)

    def generate_id(self, length=6):
        self.id = ''.join(str(random.randint(0, 9)) for _ in range(length))

    def generate_name(self, adjectives, length=3):
        self.name = ''.join(random.sample(adjectives, length))

    def info(self):
        return {"id": self.id, "name": self.name}

    async def send(self, message):
        await self.socket.send(json.dumps(message)) 

class UserContainer:
    def __init__(self):
        # self.ids = set()
        self.users = {}
        self.sockets_to_id = {}
    
    def has_user_id(self, id):
        # return id in self.ids
        return id in self.users 

    def add(self, websocket, adjectives):
        user = User(websocket, adjectives)
        while self.has_user_id(user.id):
            user.generate_all(adjectives)
        # self.ids.add(user.id)
        self.users[user.id] = user
        self.sockets_to_id[websocket] = user.id
        return user.id

    async def send_join_message(self, user_id):
        user = self.users[user_id]
        await user.send(self.make_join_message(user))       

    def make_join_message(self, user):
        return user.info() | {"event": "joined"} # python 3.9 only?

    def get_user(self, id):
        return self.users[id] if self.has_user_id(id) else None
    
    def remove_id(self, id):
        if self.has_user_id(id):
            # self.ids.remove(id)
            del self.users[id]

    def remove_socket(self, socket):
        user_id = self.sockets_to_id.pop(socket, None)
        if user_id: self.remove_id(user_id)

    def clear(self):
        # del self.sockets_to_id
        # del self.users
        self.sockets_to_id.clear()
        self.users.clear()

    def __del__(self):
        self.clear()

    def make_broadcast_message(self, user, data):
        return user.info() | {"message": data, "event": "broadcast"}

    async def broadcast_from(self, id, data):
        if not self.has_user_id(id): return
        from_user = self.get_user(id)
        message = self.make_broadcast_message(from_user, data)
        for user_id, user in self.users.items():
            # if user_id == id: continue 
            await user.send(message) 


users = UserContainer()

adjectives = []

HOST, PORT = "localhost", 8765
ADJECTIVES_FILE = "adjectives.txt"

async def join_user(websocket, message):
    # user = User(websocket, adjectives)
    user_id = users.add(websocket, adjectives)
    await users.send_join_message(user_id)

async def broadcast_message(websocket, message):
    # await websocket.send(json.dumps({"here": "lololol"}))
    await users.broadcast_from(message['id'], message['message'])

event_handler = {
    'join': join_user,
    'broadcast': broadcast_message
}

fields_of = {
    'join': [],
    'broadcast': ['id', 'name', 'message']
}

def is_valid_message(message):
    fields = set(message.keys())
    # print(fields, fields_of[message['event']])
    # fields.remove('event')
    fields.discard('event')
    return fields  == set(fields_of[message['event']])

async def message_handler(websocket, message):
    message = json.loads(message)
    print("message recieved:", message)
    if is_valid_message(message):
        print("Valid:", message)
        await event_handler[message['event']](websocket, message)
    # await websocket.send(response)

async def user_handler(websocket):
    print(f"socket handler run")  
    # users.add(websocket)
    try:
        async for message in websocket:
            await message_handler(websocket, message)
    except ConnectionClosed:    
        print("ConnectionClosed")
    finally:
        users.remove_socket(websocket)
        print("removed a socket")

async def open_websocket_server():
    print(f"Starting websocket server at ws://{HOST}:{PORT}")
    async with serve(user_handler, HOST, PORT) as server:
        await server.wait_closed()

async def read_adjectives():
    async with aiofiles.open(ADJECTIVES_FILE, mode='r') as file:
        # async for line in file:
        #     adjectives.append(line.strip())
        data = await file.read()
        adjectives.extend(data.splitlines())

HTTP_HOST, HTTP_PORT = "localhost", "5000"

runner = None

async def open_http_server():
    global runner

    STATIC_DIR = "./static"

    async def index(request):
        raise web.HTTPFound('/index.html')

    async def static_file(request):
        path = STATIC_DIR + "/" + request.match_info['filename']
        if os.path.exists(path):
            return web.FileResponse(STATIC_DIR + '/' + request.match_info['filename'])
        return web.Response(status=404)

    app = web.Application()
    app.add_routes([web.get('/{filename}', static_file), web.get('/', index)])

    # web.run_app(app)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HTTP_HOST, HTTP_PORT)
    print(f"Starting HTTP server at http://{HTTP_HOST}:{HTTP_PORT}")
    await site.start()

async def main():
    try:
        await asyncio.gather(
            read_adjectives(),
            open_http_server(),
            open_websocket_server()
        )
    except asyncio.CancelledError:
        print("Shutting down servers...")
        if runner is not None: 
            print("Shutting down HTTP server")
            await runner.cleanup()
        

asyncio.run(main())
