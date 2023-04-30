from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import json
import random
import time
import uuid
from random import randrange

from partida2 import Partida2
from partida3 import Partida3
from partida4 import Partida4

app = FastAPI()

partidas2_privadas = {}
partidas2_publicas = {}
partidas3_privadas = {}
partidas3_publicas = {}
partidas4_privadas = {}
partidas4_publicas = {}

       
#Partida de 2 jugadores        
@app.websocket("/partida2/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()

    partida_disponible = None
    for partida in partidas2_publicas.values():
        if partida.jugadores < 2:
            partida_disponible = partida
            break

    if not partida_disponible:
        partida_id = str(uuid.uuid4())
        partida_disponible = Partida2()
        partidas2_publicas[partida_id] = partida_disponible

    jugador_id = f"socket{partida_disponible.jugadores}"
    await partida_disponible.add_player(websocket, client_id)

    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        await partida_disponible.remove_player(jugador_id)
        if partida_disponible.jugadores == 0:
            partidas2_publicas.pop(partida_id)
            
#Partida de 3 jugadores         
@app.websocket("/partida3/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()

    partida_disponible = None
    for partida in partidas3_publicas.values():
        if partida.jugadores < 3:
            partida_disponible = partida
            break

    if not partida_disponible:
        partida_id = str(uuid.uuid4())
        partida_disponible = Partida3()
        partidas3_publicas[partida_id] = partida_disponible

    jugador_id = f"socket{partida_disponible.jugadores}"
    await partida_disponible.add_player(websocket, client_id)

    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        await partida_disponible.remove_player(jugador_id)
        if partida_disponible.jugadores == 0:
            partidas3_publicas.pop(partida_id)
            
#Partida de 4 jugadores         
@app.websocket("/partida4/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()

    partida_disponible = None
    for partida in partidas4_publicas.values():
        if partida.jugadores < 4:
            partida_disponible = partida
            break

    if not partida_disponible:
        partida_id = str(uuid.uuid4())
        partida_disponible = Partida4()
        partidas4_publicas[partida_id] = partida_disponible

    jugador_id = f"socket{partida_disponible.jugadores}"
    await partida_disponible.add_player(websocket, client_id)

    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        await partida_disponible.remove_player(jugador_id)
        if partida_disponible.jugadores == 0:
            partidas4_publicas.pop(partida_id)
            
            
@app.post("/crear/partida2")
async def crear_partida():
    # Generar un número aleatorio entre 10000 y 99999 que no esté en uso
    while True:
        partida_id = str(randrange(10000, 100000))
        if partida_id not in partidas2_privadas:
            break

    partida_disponible = Partida2()
    partidas2_privadas[partida_id] = partida_disponible
    return {"codigo": partida_id}


# Unirse a una partida de 2 jugadores con un código
@app.websocket("/partida2/join/{client_id}/{codigo}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, codigo: str, ):
    await websocket.accept()

    if codigo not in partidas2_privadas:
        await websocket.send_text("Partida no encontrada.")
        await websocket.close()
        return

    partida_disponible = partidas2_privadas[codigo]

    if partida_disponible.jugadores >= 2:
        await websocket.send_text("Partida Llena.")
        await websocket.close()
        return

    jugador_id = f"socket{partida_disponible.jugadores}"
    await partida_disponible.add_player(websocket, client_id)

    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        await partida_disponible.remove_player(jugador_id)
        if partida_disponible.jugadores == 0:
            partidas2_privadas.pop(codigo)
            

@app.post("/crear/partida3")
async def crear_partida():
    # Generar un número aleatorio entre 10000 y 99999 que no esté en uso
    while True:
        partida_id = str(randrange(10000, 100000))
        if partida_id not in partidas3_privadas:
            break

    partida_disponible = Partida3()
    partidas3_privadas[partida_id] = partida_disponible
    return {"codigo": partida_id}


# Unirse a una partida de 2 jugadores con un código
@app.websocket("/partida3/join/{client_id}/{codigo}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, codigo: str, ):
    await websocket.accept()

    if codigo not in partidas3_privadas:
        await websocket.send_text("Partida no encontrada.")
        await websocket.close()
        return

    partida_disponible = partidas3_privadas[codigo]

    if partida_disponible.jugadores >= 3:
        await websocket.send_text("Partida Llena.")
        await websocket.close()
        return

    jugador_id = f"socket{partida_disponible.jugadores}"
    await partida_disponible.add_player(websocket, client_id)

    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        await partida_disponible.remove_player(jugador_id)
        if partida_disponible.jugadores == 0:
            partidas3_privadas.pop(codigo)
            
@app.post("/crear/partida4")
async def crear_partida():
    # Generar un número aleatorio entre 10000 y 99999 que no esté en uso
    while True:
        partida_id = str(randrange(10000, 100000))
        if partida_id not in partidas4_privadas:
            break

    partida_disponible = Partida4()
    partidas4_privadas[partida_id] = partida_disponible
    return {"codigo": partida_id}


# Unirse a una partida de 2 jugadores con un código
@app.websocket("/partida4/join/{client_id}/{codigo}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, codigo: str, ):
    await websocket.accept()

    if codigo not in partidas4_privadas:
        await websocket.send_text("Partida no encontrada.")
        await websocket.close()
        return

    partida_disponible = partidas4_privadas[codigo]

    if partida_disponible.jugadores >= 4:
        await websocket.send_text("Partida Llena.")
        await websocket.close()
        return

    jugador_id = f"socket{partida_disponible.jugadores}"
    await partida_disponible.add_player(websocket, client_id)

    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        await partida_disponible.remove_player(jugador_id)
        if partida_disponible.jugadores == 0:
            partidas4_privadas.pop(codigo)