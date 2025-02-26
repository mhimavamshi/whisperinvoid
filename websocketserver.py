import asyncio
import aiofiles
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed
import json
import random

'''
generate an unique id for a new connection and use it to check if same socket is connecting again
generate an unique name for a new connection associated with the id to broadcast to everyone

'''

class User:
    def __init__(self, websocket, adjectives):
        self.id = self.generate_id()
        self.name = self.generate_name(adjectives)
        self.socket = websocket 

    def generate_id(self, length=6):
        return ''.join(str(random.randint(0, 9)) for _ in range(length))

    def generate_name(self, adjectives, length=3):
        return ''.join(random.sample(adjectives, length))

    def info(self):
        return {"id": self.id, "name": self.name}

    async def send(self, message):
        await self.socket.send(json.dumps(message)) 

class UserContainer:
    def __init__(self):
        self.ids = set()
        self.users = {}
    
    def has_user_id(self, id):
        return id in self.ids

    def add(self, user: User):
        if not self.has_user_id(user.id):
            self.ids.add(user.id)
            self.users[user.id] = user

    async def send_join_message(self, user):
        await user.send(self.make_join_message(user))       

    def make_join_message(self, user):
        return user.info() | {"event": "joined"} # python 3.9 only?

    def get_user(self, id):
        return self.users[id] if self.has_user_id(id) else None
    
    # def make_join_message(self, user):
    #     return user.info() 

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
    user = User(websocket, adjectives)
    users.add(user)
    await users.send_join_message(user)

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
    fields.remove('event')
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
        pass
    # finally:
    #     users.remove(websocket)

async def open_server():
    async with serve(user_handler, HOST, PORT) as server:
        await server.wait_closed()

async def read_adjectives():
    async with aiofiles.open(ADJECTIVES_FILE, mode='r') as file:
        async for line in file:
            adjectives.append(line.strip())

async def main():
    await asyncio.gather(
        open_server(),
        read_adjectives()
    )

print(f"Starting websocket server at ws://{HOST}:{PORT}")
asyncio.run(main())
