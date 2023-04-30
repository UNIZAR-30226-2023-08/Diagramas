from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import json
from logica_juego import crear_mazo, repartir_cartas, que_jugador_gana_baza, sumar_puntos, que_cartas_puede_usar_jugador_arrastre, cantar_cambiar
import random
import time
import uuid

class Partida3:
    def __init__(self):
        self.sockets = {}
        self.jugadores = 0
        self.client_list = [None, None, None]

    async def add_player(self, websocket: WebSocket, client_id: str):
        jugador_id = f"socket{self.jugadores}"
        self.sockets[jugador_id] = websocket
        self.jugadores += 1
        self.client_list[self.jugadores - 1] = client_id

        if self.jugadores == 3:
            # Enviar mensaje a todos los jugadores con la lista de client_id
            message = json.dumps({"0": self.client_list[0], "1": self.client_list[1], "2": self.client_list[2]})
            for i in range(self.jugadores):
                await self.send_message_to_socket(str(i), message)
            await self.iniciar_partida()
        else:
            # Enviar mensaje a todos los jugadores con la lista de client_id
            message = json.dumps({"0": self.client_list[0], "1": self.client_list[1], "2": self.client_list[2]})
            for i in range(self.jugadores):
                await self.send_message_to_socket(str(i), message)

    async def iniciar_partida(self):
        puntosJugador0 = 0
        puntosJugador1 = 0
        puntosJugador2 = 0
        
        orden_inicial = [0,1,2]
        orden = [0,1,2]
        
        ganador = 0
        
        cantado0 = [False, False, False, False]
        cantado1 = [False, False, False, False]
        cantado2 = [False, False, False, False]
        
        await self.send_message_to_all_sockets("Comienza partida")
                            
        manos = []
        triunfo, manos = await self.comienzo_partida()
        
        perdedor = 0
        

        await self.send_message_to_all_sockets("Arrastre")
        
        #TODO CAMBIAR EL NUMERO DE VECES QUE SE JEUGA
        for i in range(12):
            await self.mandar_manos(orden_inicial, manos)
            orden, manos, puntosJugador0, puntosJugador1, puntosJugador2, puede_cantar_cambiar = await self.arrastre(
                orden_inicial, orden, triunfo, puntosJugador0, puntosJugador1, puntosJugador2, manos)
            cantado0, cantado1, cantado2, puntosJugador0, puntosJugador1, puntosJugador2, triunfo = await self.cantar_cambiar_jugador(manos, triunfo, cantado0, cantado1, cantado2, puntosJugador0, puntosJugador1, puntosJugador2, puede_cantar_cambiar)

            
        if puntosJugador0 == puntosJugador1 or puntosJugador0 == puntosJugador2 or puntosJugador1 == puntosJugador2:
            mano_send = {"Perdedor": None, "0": puntosJugador0 ,"1": puntosJugador1, "2": puntosJugador2}
            message = json.dumps(mano_send)                        
            await self.send_message_to_all_sockets(message)
            perdedor = None
        elif puntosJugador1 < puntosJugador0 < puntosJugador2  or puntosJugador2 < puntosJugador0 < puntosJugador1:
            mano_send = {"Perdedor": 0, "0": puntosJugador0 ,"1": puntosJugador1, "2": puntosJugador2}
            message = json.dumps(mano_send)                        
            await self.send_message_to_all_sockets(message)
            perdedor = 0
        elif puntosJugador0 < puntosJugador1 < puntosJugador2  or puntosJugador2 < puntosJugador1 < puntosJugador0:
            mano_send = {"Perdedor": 1, "0": puntosJugador0 ,"1": puntosJugador1, "2": puntosJugador2}
            message = json.dumps(mano_send)                        
            await self.send_message_to_all_sockets(message)
            perdedor = 1
        else:
            mano_send = {"Perdedor": 2, "0": puntosJugador0 ,"1": puntosJugador1, "2": puntosJugador2}
            message = json.dumps(mano_send)                        
            await self.send_message_to_all_sockets(message)
            perdedor = 2
            
        await self.fin_partidafin_partida(self.client_list, perdedor, puntosJugador0, puntosJugador1, puntosJugador2)
        
    async def remove_player(self, jugador_id: str):
        self.sockets.pop(jugador_id, None)
        self.jugadores -= 1
        
    async def await_message(self, id):
        try:
            if id == "0":
                mensaje_jugador_0 = await asyncio.wait_for(self.sockets["socket0"].receive_text(), timeout=20)
                return mensaje_jugador_0
            elif id == "1":
                mensaje_jugador_1 = await asyncio.wait_for(self.sockets["socket1"].receive_text(), timeout=20)
                return mensaje_jugador_1
            else:
                mensaje_jugador_1 = await asyncio.wait_for(self.sockets["socket2"].receive_text(), timeout=20)
                return mensaje_jugador_1
            
        except asyncio.TimeoutError:
            message_fin = {"Desconexion": id}
            message_fin = json.dumps(message_fin)
            await self.send_message_to_all_sockets(message_fin)
            self.terminate_game()
            raise
        
    async def await_message_siete(self, id):
        try:
            if id == "0":
                mensaje_jugador_0 = await asyncio.wait_for(self.sockets["socket0"].receive_text(), timeout=4)
                return mensaje_jugador_0
            elif id == "1":
                mensaje_jugador_1 = await asyncio.wait_for(self.sockets["socket1"].receive_text(), timeout=4)
                return mensaje_jugador_1
            else:
                mensaje_jugador_1 = await asyncio.wait_for(self.sockets["socket2"].receive_text(), timeout=4)
                return mensaje_jugador_1
        except asyncio.TimeoutError:
            return None

    def terminate_game(self):
        self.sockets = {}
        
    async def send_message_to_socket(self, socketid: str, message: str):
        if socketid == "0":
            await self.sockets["socket0"].send_text(message)
        elif socketid == "1":
            await self.sockets["socket1"].send_text(message)
        else:
            await self.sockets["socket2"].send_text(message)
            
    async def send_message_to_all_sockets(self, message: str):
        await self.sockets["socket0"].send_text(message)
        await self.sockets["socket1"].send_text(message)
        await self.sockets["socket2"].send_text(message)
        
    async def comienzo_partida(self):
        mazo = crear_mazo()
        random.shuffle(mazo)
        
        mano1 = mazo[:len(mazo)//3]
        mano2 = mazo[len(mazo)//3:2*(len(mazo)//3)]
        mano3 = mazo[2*(len(mazo)//3):]
        triunfo = random.choice(mano3)
        mano3.remove(triunfo)
        
        manos = []
        manos.append(mano1)
        manos.append(mano2)
        manos.append(mano3)
        
        # Repartir manos a los jugadores
        for i in range(3):
            mano_send = {"Cartas": manos[i], "Triunfo": triunfo ,"Jugador": i}
            message = json.dumps(mano_send)
            await self.send_message_to_socket(str(i), message)
            
        return triunfo, manos

    async def repartir(self, orden_inicial, mazo, triunfo, manos):
        for i in orden_inicial:
            if len(mazo) == 0:
                carta_robada = triunfo
            else:
                carta_robada = mazo[0]
                mazo.remove(carta_robada)
            manos[i].append(carta_robada)
            mano_send = manos[i]
            mano_send = {"Cartas": manos[i]}
            message = json.dumps(mano_send)
            await self.send_message_to_socket(str(i), message)
        
        return mazo, manos

    async def arrastre(self, orden_inicial, orden, triunfo, puntosJugador0, puntosJugador1, puntosJugador2, manos):
        cartas_jugadas = [None, None, None]
        cartas_jugadas_mandar = [None, None, None]
        puntuacion_cartas = []
        global message_socket
        
        for i in range(3):
            #si eres el primero en tirar puedes usar lo que quieras
            if i == 0:
                mano_send = {"0": cartas_jugadas_mandar[0], "1": cartas_jugadas_mandar[1], "2": cartas_jugadas_mandar[2] , "Turno": orden[i], "Triunfo": None}
                message = json.dumps(mano_send)
                await self.send_message_to_all_sockets(message)
                
                mano_send ={"Cartas Posibles": manos[orden[i]]}
                message = json.dumps(mano_send)
                await self.send_message_to_socket(str(orden[i]), message)
            else:
                mano_send = {"0": cartas_jugadas_mandar[0], "1": cartas_jugadas_mandar[1], "2": cartas_jugadas_mandar[2], "Turno": orden[i], "Triunfo": None}
                message = json.dumps(mano_send)
                await self.send_message_to_all_sockets(message)   
                        
                cartas_posibles = que_cartas_puede_usar_jugador_arrastre(manos[orden[i]], puntuacion_cartas, triunfo)
                mano_send = {"Cartas Posibles": cartas_posibles}
                message = json.dumps(mano_send)
                await self.send_message_to_socket(str(orden[i]), message)
            
            carta = await self.await_message(str(orden[i]))
                    
            palo, valor = carta.split("-") 
            carta_tupla = (palo, int(valor))
                    
            manos[orden[i]].remove(carta_tupla)
            cartas_jugadas[i] = carta_tupla
            cartas_jugadas_mandar[orden[i]] = carta_tupla
            puntuacion_cartas.append(carta_tupla)
            
        mano_send = {"0": cartas_jugadas_mandar[0], "1": cartas_jugadas_mandar[1], "2": cartas_jugadas_mandar[2], "Turno": None, "Triunfo": None}
        message = json.dumps(mano_send)
        await self.send_message_to_all_sockets(message)
            
        carta_gandora = que_jugador_gana_baza(puntuacion_cartas, triunfo)
        indice_ganador = puntuacion_cartas.index(carta_gandora)
        
        puede_cantar_cambiar = 0
        
        #Sumo puntos al jugador que ha ganado la baza
        if orden[indice_ganador] == orden_inicial[0]:
            puntosJugador0 += sumar_puntos(cartas_jugadas)
            message_ganador = {"Ganador": "0"}
            message_ganador = json.dumps(message_ganador)
            await self.send_message_to_all_sockets(message_ganador)
            puede_cantar_cambiar = 0
        elif orden[indice_ganador] == orden_inicial[1]:
            puntosJugador1 += sumar_puntos(cartas_jugadas)
            message_ganador = {"Ganador": "1"}
            message_ganador = json.dumps(message_ganador)
            await self.send_message_to_all_sockets(message_ganador)
            puede_cantar_cambiar = 1
        else:
            puntosJugador2 += sumar_puntos(cartas_jugadas)
            message_ganador = {"Ganador": "2"}
            message_ganador = json.dumps(message_ganador)
            await self.send_message_to_all_sockets(message_ganador)
            puede_cantar_cambiar = 2
        
        #Cambiar el orden si ha ganado el 1 o 2 la baza
        if indice_ganador == 1:
            orden = [orden[1],orden[2],orden[0]]
        elif indice_ganador == 2:
            orden = [orden[2],orden[0],orden[1]]
        
        return orden, manos, puntosJugador0, puntosJugador1, puntosJugador2, puede_cantar_cambiar

    async def comprobarGanador(self, puntosJugador0, puntosJugador1):
        if puntosJugador1 >= 100:
            message = {"Ganador": 0, "0": puntosJugador0 ,"1": puntosJugador1}
            message = json.dumps(message)
            await self.send_message_to_all_sockets(message)
            return True
        elif puntosJugador1 >= 100:
            message = {"Ganador": 1, "0": puntosJugador0 ,"1": puntosJugador1}
            message = json.dumps(message)
            await self.send_message_to_all_sockets(message)
            return True
        else:
            return False

    async def mandar_manos(self, orden_inicial, manos):
        for i in orden_inicial:
            mano_send = {"Cartas": manos[i]}
            message = json.dumps(mano_send)
            await self.send_message_to_socket(str(i), message)
            
            
    async def cantar_cambiar_jugador(self, manos, triunfo, cantado0, cantado1, cantado2, puntosJugador0, puntosJugador1, puntosJugador2,  puede_cantar_cambiar):
        posibilidad = [False, False, False]
        for i in range(3):
            palo, valor = triunfo
            tiene_siete_triunfo, cantar_oro, cartar_basto, cantar_copa, cantar_espada =  cantar_cambiar(manos[i], triunfo)
            cantado = cantado0
            if i == 1: cantado = cantado1
            elif i == 2: cantado = cantado2
            
            if puede_cantar_cambiar == i:
                           
                if cantar_oro and cantado[0] == False:
                    elque = "20"
                    if "oro" == str(palo): elque = "40"
                    mano_send = {"Canta": elque, "Palo": "oro" ,"Jugador": i}
                    message = json.dumps(mano_send)
                    await self.send_message_to_all_sockets(message)
                    if i == 0:
                        cantado0[0] = True 
                        if elque == "20": puntosJugador0 += 20
                        if elque == "40": puntosJugador0 += 40
                    elif i == 1:
                        cantado1[0] = True
                        if elque == "20": puntosJugador1 += 20
                        if elque == "40": puntosJugador1 += 40
                    else:
                        cantado2[0] = True
                        if elque == "20": puntosJugador2 += 20
                        if elque == "40": puntosJugador2 += 40
                        
                if cartar_basto and cantado[1] == False:
                    elque = "20"
                    if "basto" == str(palo): elque = "40"
                    mano_send = {"Canta": elque, "Palo": "basto" ,"Jugador": i}
                    message = json.dumps(mano_send)
                    await self.send_message_to_all_sockets(message)
                    if i == 0: 
                        cantado0[1] = True
                        if elque == "20": puntosJugador0 += 20
                        if elque == "40": puntosJugador0 += 40
                    elif i == 1:
                        cantado1[1] = True
                        if elque == "20": puntosJugador1 += 20
                        if elque == "40": puntosJugador1 += 40
                    else:
                        cantado2[1] = True
                        if elque == "20": puntosJugador2 += 20
                        if elque == "40": puntosJugador2 += 40    
                        
                if cantar_copa and cantado[2] == False:
                    elque = "20"
                    if "copa" == str(palo): elque = "40"
                    mano_send = {"Canta": elque, "Palo": "copa" ,"Jugador": i}
                    message = json.dumps(mano_send)
                    await self.send_message_to_all_sockets(message)
                    if i == 0: 
                        cantado0[2] = True
                        if elque == "20": puntosJugador0 += 20
                        if elque == "40": puntosJugador0 += 40
                    elif i == 1:
                        cantado1[2] = True
                        if elque == "20": puntosJugador1 += 20
                        if elque == "40": puntosJugador1 += 40
                    else:
                        cantado2[2] = True
                        if elque == "20": puntosJugador2 += 20
                        if elque == "40": puntosJugador2 += 40
                        
                if cantar_espada and cantado[3] == False:
                    elque = "20"
                    if "espada" == str(palo): elque = "40"
                    mano_send = {"Canta": elque, "Palo": "espada" ,"Jugador": i}
                    message = json.dumps(mano_send)
                    await self.send_message_to_all_sockets(message)
                    if i == 0: 
                        cantado0[3] = True
                        if elque == "20": puntosJugador0 += 20
                        if elque == "40": puntosJugador0 += 40
                    elif i == 1:
                        cantado1[3] = True
                        if elque == "20": puntosJugador1 += 20
                        if elque == "40": puntosJugador1 += 40
                    else:
                        cantado2[3] = True
                        if elque == "20": puntosJugador2 += 20
                        if elque == "40": puntosJugador2 += 40 
                        
            if tiene_siete_triunfo and puede_cantar_cambiar:
                posibilidad[i] = True
                
                    
        for i in range(2):
                mano_send = {"Cambiar7": posibilidad[i]}
                message = json.dumps(mano_send)
                await self.send_message_to_socket(str(i), message)
        
        if posibilidad[0] or posibilidad[1] or posibilidad[2]:
            x = 0
            if posibilidad[1]:
                x = 1
            elif posibilidad[2]:
                x = 2
                
            inicio = time.time()        
            cambiar = await self.await_message_siete(str(x))
            final = time.time()
            if cambiar == "True":
                manos[i].remove((palo, 7))
                manos[i].append(triunfo)
                triunfo = (palo, 7)
                cambiado_por_jugador = i
            segundos = final - inicio
            if segundos < 4:
                await asyncio.sleep(4 - segundos)
        else:
            await asyncio.sleep(4)

                        
        message = {"Cambiado": None}
        message = json.dumps(message)                
                        
        if cambiado_por_jugador != 10:
            message = {"Cambiado": cambiado_por_jugador}
            message = json.dumps(message)
        
        for a in range(3):
            await self.send_message_to_socket(str(a), message)
            
        return cantado0, cantado1, puntosJugador0, puntosJugador1, puntosJugador2, triunfo
    
    async def fin_partida(self, client_list, perdedor, puntosJugador0, puntosJugador1, puntosJugador2):
        print("METE AQUI LO DE BD")