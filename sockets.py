#!/usr/bin/env python
# coding: utf-8
# Copyright (c) 2013-2014 Abram Hindle
# Copyright (c) 2022 Daniel Chu
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


#cmput404w22
#heavily based on https://github.com/abramhindle/WebSocketsExamples from class prof

import flask
from flask import Flask, request, redirect, Response
from flask_sockets import Sockets
import gevent
from gevent import queue
import time
import json
import os
import http_codes

app = Flask(__name__)
sockets = Sockets(app)
app.debug = True

clients = list()

class World:
    def __init__(self):
        self.clear()
        # we've got listeners now!
        self.listeners = list()
        
    def add_set_listener(self, listener):
        self.listeners.append( listener )

    def update(self, entity, key, value):
        entry = self.space.get(entity,dict())
        entry[key] = value
        self.space[entity] = entry
        self.update_listeners( entity )

    def set(self, entity, data):
        self.space[entity] = data
        self.update_listeners( entity )

    def update_listeners(self, entity):
        '''update the set listeners'''
        for listener in self.listeners:
            listener(entity, self.get(entity))

    def clear(self):
        self.space = dict()

    def get(self, entity):
        return self.space.get(entity,dict())
    
    def world(self):
        return self.space

class Client:
    '''
    Client
    Taken from https://github.com/abramhindle/WebSocketsExamples/blob/master/chat.py
    '''
    def __init__(self):
        self.queue = queue.Queue()

    def put(self, v):
        self.queue.put_nowait(v)

    def get(self):
        return self.queue.get()


myWorld = World()        

def set_listener( entity, data ):
    ''' do something with the update ! '''
    #not going to bother with the world listener since I can already send to all clients elsewhere

myWorld.add_set_listener( set_listener )
        
@app.route('/')
def hello():
    '''Return something coherent here.. perhaps redirect to /static/index.html '''
    return redirect("/static/index.html", code = http_codes.FOUND)

def send_all(msg):# from https://github.com/abramhindle/WebSocketsExamples/blob/master/chat.py
    for client in clients:
        client.put( msg )

def send_all_json(obj):# fromhttps://github.com/abramhindle/WebSocketsExamples/blob/master/chat.py
    send_all( json.dumps(obj) )

def read_ws(ws,client):# based on https://github.com/abramhindle/WebSocketsExamples/blob/master/chat.py
    '''A greenlet function that reads from the websocket and updates the world'''
    # XXX: TODO IMPLEMENT ME
    try:
        while True:
            msg = ws.receive()
            #print(f"WS RECV: {msg}")
            if (msg is not None):
                packet = json.loads(msg)
                send_all_json( packet )
                for entity, data in packet.items():
                    for k, v in data.items():
                        myWorld.update(entity, k, v)
            else:
                break
    except:
        '''Done'''

@sockets.route('/subscribe')
def subscribe_socket(ws):
    '''Fufill the websocket URL of /subscribe, every update notify the
       websocket and read updates from the websocket '''
    #taken from https://github.com/abramhindle/WebSocketsExamples/blob/master/chat.py
    # XXX: TODO IMPLEMENT ME
    #return None
    print(f"Socket opened from {request.remote_addr}")
    client = Client()
    clients.append(client)
    g = gevent.spawn( read_ws, ws, client )    
    try:
        while True:
            # block here
            msg = client.get()
            ws.send(msg)
    except Exception as e:# WebSocketError as e:
        print(f"WS Error {e}")
    finally:
        clients.remove(client)
        gevent.kill(g)

    

# I give this to you, this is how you get the raw body/data portion of a post in flask
# this should come with flask but whatever, it's not my project.
def flask_post_json():
    '''Ah the joys of frameworks! They do so much work for you
       that they get in the way of sane operation!'''
    if (request.json != None):
        return request.json
    elif (request.data != None and request.data.decode("utf8") != u''):
        return json.loads(request.data.decode("utf8"))
    else:
        return json.loads(request.form.keys()[0])

@app.route("/entity/<entity>", methods=['POST','PUT'])
def update(entity):
    '''update the entities via this interface'''
    #return None
    if request.json == None:
        raise Exception(f"No json body given for /entity/{entity}")
    for k, v in flask_post_json().items():
        myWorld.update(entity, k, v)
    return myWorld.get(entity)

@app.route("/world", methods=['POST','GET'])    
def world():
    '''you should probably return the world here'''
    return myWorld.world()

@app.route("/entity/<entity>", methods=["GET"])    
def get_entity(entity):
    '''This is the GET version of the entity interface, return a representation of the entity'''
    return myWorld.get(entity)


@app.route("/clear", methods=['POST','GET'])
def clear():
    '''Clear the world out!'''
    return myWorld.clear()



if __name__ == "__main__":
    ''' This doesn't work well anymore:
        pip install gunicorn
        and run
        gunicorn -k flask_sockets.worker sockets:app
    '''
    app.run()
