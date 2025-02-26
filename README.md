# Whisper In Void

A Simple chat site where everyone can send a message and watch them fade away.

Note: Made only for development purposes, for instance static files should be served with and use of reverse proxy servers like Nginx as aiohttp is relatively slower, usage of gunicorn etc.,
This is made to learn asynchronous programming in python.

## How to run

```console
$ pip install -r requirements.txt
$ python server.py 
```
Then visit http://localhost:5000 or whichever HTTP_PORT is

server.py is a single file which asynchronously runs both HTTP and WebSocket server

