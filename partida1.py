from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import json
import random
import time
import uuid
from logica_juego import crear_mazo, repartir_cartas, que_jugador_gana_baza, sumar_puntos, que_cartas_puede_usar_jugador_arrastre


class Partida1:
    def __init__(self):
        self.socket = None
        self.jugador = None

    async def set_player(self, websocket: WebSocket):
        self.socket = websocket
        await self.iniciar_partida()

    async def iniciar_partida(self):
        puntosJugador0_2 = 0
        puntosJugador1_3 = 0
        
        orden_inicial = [0,1,2,3]
        orden = [0,1,2,3]
        
        vueltas = False
        
        await self.send_message_to_all_sockets("Comienza partida")
        
        for i in range(2):
            
            manos = []
            mazo, triunfo, manos = await self.comienzo_partida()
            
            for i in range(7):
                puntosJugador0_2, puntosJugador1_3, manos, orden, orden_inicial = await self.ronda(triunfo, puntosJugador0_2, puntosJugador1_3, manos, orden, orden_inicial)    
                if vueltas: 
                    ganador = self.comprobarGanador(puntosJugador0_2, puntosJugador1_3)
                    if ganador: break
                mazo, manos = await self.repartir(orden_inicial, mazo, triunfo, manos)
            
            await self.send_message_to_all_sockets("Arrastre")
            
            for i in range(6):
                await self.mandar_manos(orden_inicial, manos)
                orden, manos, puntosJugador0_2, puntosJugador1_3, indice_ganador = await self.arrastre(orden_inicial, orden, triunfo, puntosJugador0_2, puntosJugador1_3, manos)
                if vueltas: 
                    ganador = self.comprobarGanador(puntosJugador0_2, puntosJugador1_3)
                    if ganador: break
                
            if puntosJugador0_2 > 100 and puntosJugador1_3 < 100:
                mano_send = {"Ganador": [0,2], "0": puntosJugador0_2 ,"1": puntosJugador1_3, "2": puntosJugador0_2 ,"3": puntosJugador1_3}
                message = json.dumps(mano_send)                        
                await self.send_message_to_all_sockets(message)
                break
            elif puntosJugador1_3 > 100 and puntosJugador0_2 < 100:
                mano_send = {"Ganador": [1,3], "0": puntosJugador0_2 ,"1": puntosJugador1_3, "2": puntosJugador0_2 ,"3": puntosJugador1_3}
                message = json.dumps(mano_send)
                await self.send_message_to_all_sockets(message)
                break
            elif puntosJugador0_2 > 100 and puntosJugador1_3 > 100:
                if orden[indice_ganador] == orden_inicial[0]: 
                    mano_send = {"Ganador": [0,2], "0": puntosJugador0_2 ,"1": puntosJugador1_3, "2": puntosJugador0_2 ,"3": puntosJugador1_3}
                    message = json.dumps(mano_send)  
                    await self.send_message_to_all_sockets(message)
                    break
                else:
                    mano_send = {"Ganador": [1,3], "0": puntosJugador0_2 ,"1": puntosJugador1_3, "2": puntosJugador0_2 ,"3": puntosJugador1_3}
                    message = json.dumps(mano_send)
                    await self.send_message_to_all_sockets(message)
                    break
            else:
                vueltas = True
                mano_send = {"Ganador": None, "0": puntosJugador0_2 ,"1": puntosJugador1_3, "2": puntosJugador0_2 ,"3": puntosJugador1_3}
                message = json.dumps(mano_send)
                await self.send_message_to_all_sockets(message)
            
            
    async def remove_player(self):
        self.socket = None
        
        
    async def send_message_to_all_sockets(self, message: str):
        await self.socket.send_text(message)
        
    async def await_message(self, id: str):
        mensaje_jugador = await self.socket.receive_text()
        return mensaje_jugador
            
    async def send_message_to_socket(self, socketid: str, message: str):
        await self.socket.send_text(message)
        
    async def comienzo_partida(self):
        mazo = crear_mazo()
        random.shuffle(mazo)
        manos, mazo = repartir_cartas(mazo, 4)
        triunfo = mazo[0]
        mazo.remove(triunfo)
        mano_send = {"Cartas": manos[0], "Triunfo": triunfo ,"Jugador": 0}
        message = json.dumps(mano_send)
        await self.send_message_to_socket("0", message)
            
        return mazo, triunfo, manos

    async def ronda(self, triunfo, puntosJugador0_2, puntosJugador1_3, manos, orden, orden_inicial):
        cartas_jugadas = [None, None, None, None]
        puntuacion_cartas = []
        cartas_jugadas_mandar = [None, None, None, None]
        
        for i in range(4):
            mano_send = {"0": cartas_jugadas_mandar[0], "1": cartas_jugadas_mandar[1] , 
                        "2": cartas_jugadas_mandar[2] ,"3": cartas_jugadas_mandar[3] ,"Turno": orden[i], "Triunfo": triunfo}
            message = json.dumps(mano_send)
            await self.send_message_to_all_sockets(message)
            
            if orden[i] == orden_inicial[0]:
                carta = await self.await_message(str(orden[i]))
            else:
                carta = random.choice(manos[orden[i]])
                carta = carta[0] + "-" + str(carta[1])
                    
            palo, valor = carta.split("-") 
            carta_tupla = (palo, int(valor))

                    
            manos[orden[i]].remove(carta_tupla)
            cartas_jugadas[i] = carta_tupla
            cartas_jugadas_mandar[orden[i]] = carta_tupla
            puntuacion_cartas.append(carta_tupla)
        
        mano_send = {"0": cartas_jugadas_mandar[0], "1": cartas_jugadas_mandar[1] , 
                    "2": cartas_jugadas_mandar[2] ,"3": cartas_jugadas_mandar[3] ,"Turno": None, "Triunfo": triunfo}
        message = json.dumps(mano_send)
        await self.send_message_to_all_sockets(message)
        
        carta_gandora = que_jugador_gana_baza(puntuacion_cartas, triunfo)
        indice_ganador = puntuacion_cartas.index(carta_gandora)
        
        #Sumo puntos al jugador que ha ganado la baza
        if orden[indice_ganador] == orden_inicial[0]:
            puntosJugador0_2 += sumar_puntos(cartas_jugadas)
            await self.send_message_to_all_sockets("Ganador: 0")
            orden = [0,1,2,3]
        elif orden[indice_ganador] == orden_inicial[1]:
            puntosJugador1_3 += sumar_puntos(cartas_jugadas)
            await self.send_message_to_all_sockets("Ganador: 1")
            orden = [1,2,3,0]
        elif orden[indice_ganador] == orden_inicial[2]:    
            puntosJugador0_2 += sumar_puntos(cartas_jugadas)
            await self.send_message_to_all_sockets("Ganador: 2")
            orden = [2,3,0,1]
        else:
            puntosJugador0_2 += sumar_puntos(cartas_jugadas)
            await self.send_message_to_all_sockets("Ganador: 3")
            orden = [3,0,1,2]
                    
        return puntosJugador0_2, puntosJugador1_3, manos, orden, orden_inicial

    async def repartir(self, orden_inicial, mazo, triunfo, manos):
        for i in orden_inicial:
            if len(mazo) == 0:
                carta_robada = triunfo
            else:
                carta_robada = mazo[0]
                mazo.remove(carta_robada)
            manos[i].append(carta_robada)
            mano_send = manos[i]
            message = json.dumps(mano_send)
            if i == 0:
                await self.send_message_to_socket(str(i), message)
        
        return mazo, manos

    async def arrastre(self, orden_inicial, orden, triunfo, puntosJugador0_2, puntosJugador1_3, manos):
        cartas_jugadas = [None, None, None, None]
        cartas_jugadas_mandar = [None, None, None, None]
        puntuacion_cartas = []
        
        for i in range(4):
            #si eres el primero en tirar puedes usar lo que quieras
            if i == 0:
                mano_send = {"0": cartas_jugadas_mandar[0], "1": cartas_jugadas_mandar[1], 
                            "2": cartas_jugadas_mandar[2], "3": cartas_jugadas_mandar[3] ,"Turno": orden[i], "Triunfo": None}
                message = json.dumps(mano_send)
                await self.send_message_to_all_sockets(message)
                
                mano_send = manos[orden[i]]
                message = json.dumps(mano_send)
                await self.send_message_to_socket(str(orden[i]), message)
            else:
                mano_send = {"0": cartas_jugadas_mandar[0], "1": cartas_jugadas_mandar[1], 
                            "2": cartas_jugadas_mandar[2], "3": cartas_jugadas_mandar[3] ,"Turno": orden[i], "Triunfo": None}
                message = json.dumps(mano_send)
                await self.send_message_to_all_sockets(message)   
                        
                cartas_posibles = que_cartas_puede_usar_jugador_arrastre(manos[orden[i]], puntuacion_cartas, triunfo)
                message = json.dumps(cartas_posibles)
                await self.send_message_to_socket(str(orden[i]), message)
            
            if orden[i] == 0:
                carta = await self.await_message(str(orden[i]))
            else:
                if i != 0:
                    cartas_posibles = que_cartas_puede_usar_jugador_arrastre(manos[orden[i]], puntuacion_cartas, triunfo)
                else:
                    cartas_posibles = manos[orden[i]]
                print(cartas_posibles)
                carta = random.choice(cartas_posibles)
                carta = carta[0] + "-" + str(carta[1])
                    
            palo, valor = carta.split("-") 
            carta_tupla = (palo, int(valor))
                    
            manos[orden[i]].remove(carta_tupla)
            cartas_jugadas[i] = carta_tupla
            cartas_jugadas_mandar[orden[i]] = carta_tupla
            puntuacion_cartas.append(carta_tupla)
            
        mano_send = {"0": cartas_jugadas_mandar[0], "1": cartas_jugadas_mandar[1], 
                        "2": cartas_jugadas_mandar[2], "3": cartas_jugadas_mandar[3] ,"Turno": None, "Triunfo": None}
        message = json.dumps(mano_send)
        await self.send_message_to_all_sockets(message) 
            
        carta_gandora = que_jugador_gana_baza(puntuacion_cartas, triunfo)
        indice_ganador = puntuacion_cartas.index(carta_gandora)
        
        #Sumo puntos al jugador que ha ganado la baza
        if orden[indice_ganador] == orden_inicial[0]:
            puntosJugador0_2 += sumar_puntos(cartas_jugadas)
            await self.send_message_to_all_sockets("Ganador: 0")
            orden = [0,1,2,3]
        elif orden[indice_ganador] == orden_inicial[1]:
            puntosJugador1_3 += sumar_puntos(cartas_jugadas)
            await self.send_message_to_all_sockets("Ganador: 1")
            orden = [1,2,3,0]
        elif orden[indice_ganador] == orden_inicial[2]:    
            puntosJugador0_2 += sumar_puntos(cartas_jugadas)
            await self.send_message_to_all_sockets("Ganador: 2")
            orden = [2,3,0,1]
        else:
            puntosJugador0_2 += sumar_puntos(cartas_jugadas)
            await self.send_message_to_all_sockets("Ganador: 3")
            orden = [3,0,1,2]
        
        return orden, manos, puntosJugador0_2, puntosJugador1_3, indice_ganador 

    async def comprobarGanador(self, puntosJugador0_2, puntosJugador1_3):
        if puntosJugador0_2 >= 100:
            message = {"Ganador": [0,2], "0": puntosJugador0_2 ,"1": puntosJugador1_3, 
                    "2": puntosJugador0_2, "3": puntosJugador1_3}
            message = json.dumps(message)
            await self.send_message_to_all_sockets(message)
            return True
        elif puntosJugador1_3 >= 100:
            message = {"Ganador": [1,3], "0": puntosJugador0_2 ,"1": puntosJugador1_3, 
                    "2": puntosJugador0_2, "3": puntosJugador1_3}        
            message = json.dumps(message)
            await self.send_message_to_all_sockets(message)
            return True
        else:
            return False

    async def mandar_manos(self, orden_inicial, manos):
        for i in orden_inicial:
            mano_send = manos[i]
            message = json.dumps(mano_send)
            await self.send_message_to_socket(str(i), message)
            
            
    async def final_partida():
        print("meter en BD")