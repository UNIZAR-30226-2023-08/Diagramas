from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import json
from logica_juego import crear_mazo, repartir_cartas, que_jugador_gana_baza, sumar_puntos, que_cartas_puede_usar_jugador_arrastre, cantar_cambiar
import random
import time
import uuid


class Partida2:
    def __init__(self):
        self.sockets = {}
        self.jugadores = 0
        self.client_list = [None, None]
            
    async def add_player(self, websocket: WebSocket, client_id: str):
        jugador_id = f"socket{self.jugadores}"
        self.sockets[jugador_id] = websocket
        self.jugadores += 1
        self.client_list[self.jugadores - 1] = client_id

        if self.jugadores == 2:
            # Enviar mensaje a todos los jugadores con la lista de client_id
            message = json.dumps({"0": self.client_list[0], "1": self.client_list[1]})
            for i in range(self.jugadores):
                await self.send_message_to_socket(str(i), message)
            await self.iniciar_partida()
        else:
            # Enviar mensaje a todos los jugadores con la lista de client_id
            message = json.dumps({"0": self.client_list[0], "1": self.client_list[1]})
            for i in range(self.jugadores):
                await self.send_message_to_socket(str(i), message)


    async def iniciar_partida(self):
        puntosJugador0 = 0
        puntosJugador1 = 0
        
        orden_inicial = [0,1]
        orden = [0,1]
        
        ganador = 0
        
        cantado0 = [False, False, False, False]
        cantado1 = [False, False, False, False]
        
        vueltas = False
        arrastre = False
        
        await self.send_message_to_all_sockets("Comienza partida")
        
        for i in range(2):
            
            manos = []
            mazo, triunfo, manos = await self.comienzo_partida()
            arrastre = False
            
            for i in range(14):
                puntosJugador0, puntosJugador1, manos, orden, orden_inicial, puede_cantar_cambiar= await self.ronda(triunfo, puntosJugador0, puntosJugador1, manos, orden, orden_inicial)    
                if vueltas: 
                    ganador = self.comprobarGanador(puntosJugador0, puntosJugador1)
                    if ganador: break
                cantado0, cantado1, puntosJugador0, puntosJugador1, triunfo = await self.cantar_cambiar_jugador(manos, triunfo, cantado0, cantado1, puntosJugador0, puntosJugador1, puede_cantar_cambiar, arrastre)
                mazo, manos = await self.repartir(orden_inicial, mazo, triunfo, manos)
            
            await self.send_message_to_all_sockets("Arrastre")
            arrastre = True
            for i in range(6):
                await self.mandar_manos(orden_inicial, manos)
                orden, manos, puntosJugador0, puntosJugador1, indice_ganador = await self.arrastre(orden_inicial, orden, triunfo, puntosJugador0, puntosJugador1, manos)
                if vueltas: 
                    ganador = self.comprobarGanador(puntosJugador0, puntosJugador1)
                    if ganador: break
                cantado0, cantado1, puntosJugador0, puntosJugador1, triunfo = await self.cantar_cambiar_jugador(manos, triunfo, cantado0, cantado1, puntosJugador0, puntosJugador1, puede_cantar_cambiar, arrastre)

                
            if puntosJugador0 > 100 and puntosJugador1 < 100:
                mano_send = {"Ganador Partida": 0, "0": puntosJugador0 ,"1": puntosJugador1}
                message = json.dumps(mano_send)                        
                await self.send_message_to_all_sockets(message)
                ganador = 0
                break
            elif puntosJugador1 > 100 and puntosJugador0 < 100:
                mano_send = {"Ganador Partida": 1, "0": puntosJugador0 ,"1": puntosJugador1}
                message = json.dumps(mano_send)
                await self.send_message_to_all_sockets(message)
                ganador = 1
                break
            elif puntosJugador0 > 100 and puntosJugador1 > 100:
                if orden[indice_ganador] == orden_inicial[0]: 
                    mano_send = {"Ganador Partida": 0, "0": puntosJugador0 ,"1": puntosJugador1}
                    message = json.dumps(mano_send)  
                    await self.send_message_to_all_sockets(message)
                    ganador = 0
                    break
                else:
                    mano_send = {"Ganador Partida": 1, "0": puntosJugador0 ,"1": puntosJugador1}
                    message = json.dumps(mano_send)
                    await self.send_message_to_all_sockets(message)
                    ganador = 1
                    break
            else:
                vueltas = True
                mano_send = {"Ganador Partida": None, "0": puntosJugador0 ,"1": puntosJugador1}
                message = json.dumps(mano_send)
                await self.send_message_to_all_sockets(message)
                ganador = 10
                
        if ganador == 0 or ganador == 1:
            await self.fin_partida(self.client_list, ganador, puntosJugador0, puntosJugador1)

    async def remove_player(self, jugador_id: str):
        self.sockets.pop(jugador_id, None)
        self.jugadores -= 1
        
    async def await_message(self, id):
        try:
            if id == "0":
                mensaje_jugador_0 = await asyncio.wait_for(self.sockets["socket0"].receive_text(), timeout=20)
                return mensaje_jugador_0
            else:
                mensaje_jugador_1 = await asyncio.wait_for(self.sockets["socket1"].receive_text(), timeout=20)
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
            else:
                mensaje_jugador_1 = await asyncio.wait_for(self.sockets["socket1"].receive_text(), timeout=4)
                return mensaje_jugador_1
        except asyncio.TimeoutError:
            return None

    def terminate_game(self):
        self.sockets = {}
        
    async def send_message_to_socket(self, socketid: str, message: str):
        if socketid == "0":
            await self.sockets["socket0"].send_text(message)
        else:
            await self.sockets["socket1"].send_text(message)
            
    async def send_message_to_all_sockets(self, message: str):
        await self.sockets["socket0"].send_text(message)
        await self.sockets["socket1"].send_text(message)
        
    async def comienzo_partida(self, ):
        mazo = crear_mazo()
        random.shuffle(mazo)
        manos, mazo = repartir_cartas(mazo, 2)
        triunfo = mazo[0]
        mazo.remove(triunfo)
        
        # Repartir manos a los jugadores
        for i in range(2):
            mano_send = {"Cartas": manos[i], "Triunfo": triunfo ,"Jugador": i}
            message = json.dumps(mano_send)
            await self.send_message_to_socket(str(i), message)
            
        return mazo, triunfo, manos

    async def ronda(self, triunfo, puntosJugador0, puntosJugador1, manos, orden, orden_inicial):
        cartas_jugadas = [None, None]
        puntuacion_cartas = []
        cartas_jugadas_mandar = [None, None]
        
        for i in range(2):
            mano_send = {"0": cartas_jugadas_mandar[0], "1": cartas_jugadas_mandar[1] ,"Turno": orden[i], "Triunfo": triunfo}
            message = json.dumps(mano_send)
            await self.send_message_to_all_sockets(message)
            
            carta = await self.await_message(str(orden[i]))
                    
            palo, valor = carta.split("-") 
            carta_tupla = (palo, int(valor))

                    
            manos[orden[i]].remove(carta_tupla)
            cartas_jugadas[i] = carta_tupla
            cartas_jugadas_mandar[orden[i]] = carta_tupla
            puntuacion_cartas.append(carta_tupla)
        
        mano_send = {"0": cartas_jugadas_mandar[0], "1": cartas_jugadas_mandar[1] ,"Turno": None, "Triunfo": triunfo}
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
        else:
            puntosJugador1 += sumar_puntos(cartas_jugadas)
            message_ganador = {"Ganador": "1"}
            message_ganador = json.dumps(message_ganador)
            await self.send_message_to_all_sockets(message_ganador)
            puede_cantar_cambiar = 1
            
        #Si el jugador que ha ganado es el 1, cambia el orden de los jugadores
        if indice_ganador == 1:
            orden = list(reversed(orden))
                    
        return puntosJugador0, puntosJugador1, manos, orden, orden_inicial, puede_cantar_cambiar

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

    async def arrastre(self, orden_inicial, orden, triunfo, puntosJugador0, puntosJugador1, manos):
        cartas_jugadas = [None, None]
        cartas_jugadas_mandar = [None, None]
        puntuacion_cartas = []
        
        for i in range(2):
            #si eres el primero en tirar puedes usar lo que quieras
            if i == 0:
                mano_send = {"0": cartas_jugadas_mandar[0], "1": cartas_jugadas_mandar[1] ,"Turno": orden[i], "Triunfo": None}
                message = json.dumps(mano_send)
                await self.send_message_to_all_sockets(message)
                
                mano_send = {"Cartas Posibles": manos[orden[i]]}
                message = json.dumps(mano_send)
                await self.send_message_to_socket(str(orden[i]), message)
            else:
                mano_send = {"0": cartas_jugadas_mandar[0], "1": cartas_jugadas_mandar[1] ,"Turno": orden[i], "Triunfo": None}
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
            
        mano_send = {"0": cartas_jugadas_mandar[0], "1": cartas_jugadas_mandar[1] ,"Turno": None, "Triunfo": None}
        message = json.dumps(mano_send)
        await self.send_message_to_all_sockets(message)  
            
        carta_gandora = que_jugador_gana_baza(puntuacion_cartas, triunfo)
        indice_ganador = puntuacion_cartas.index(carta_gandora)
        
        #Sumo puntos al jugador que ha ganado la baza
        if orden[indice_ganador] == orden_inicial[0]:
            puntosJugador0 += sumar_puntos(cartas_jugadas)
            message_ganador = {"Ganador": "0"}
            message_ganador = json.dumps(message_ganador)
            await self.send_message_to_all_sockets(message_ganador)
        else:
            puntosJugador1 += sumar_puntos(cartas_jugadas)
            message_ganador = {"Ganador": "1"}
            message_ganador = json.dumps(message_ganador)
            await self.send_message_to_all_sockets(message_ganador)
            
        #Si el jugador que ha ganado es el 1, cambia el orden de los jugadores
        if indice_ganador == 1:
            orden = orden[1:] + orden[:1]
        
        return orden, manos, puntosJugador0, puntosJugador1, indice_ganador 

    async def comprobarGanador(self, puntosJugador0, puntosJugador1):
        if puntosJugador0 >= 100:
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
            mano_send = manos[i]
            mano_send = {"Cartas": manos[i]}
            message = json.dumps(mano_send)
            await self.send_message_to_socket(str(i), message)
            
    async def cantar_cambiar_jugador(self, manos, triunfo, cantado0, cantado1, puntosJugador0, puntosJugador1, puede_cantar_cambiar, arrastre):
        cambiado_por_jugador = 10
        posibilidad = [False, False]
        for i in range(2):
            palo, valor = triunfo
            tiene_siete_triunfo, cantar_oro, cartar_basto, cantar_copa, cantar_espada =  cantar_cambiar(manos[i], triunfo)
            cantado = cantado0
            if i != 0: cantado = cantado1
            cambiar = "False"
                    
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
                    else:
                        cantado1[0] = True
                        if elque == "20": puntosJugador1 += 20
                        if elque == "40": puntosJugador1 += 40
                        
                if cartar_basto and cantado[1] == False:
                    elque = "20"
                    if "basto" == str(palo): elque = "40"
                    mano_send = {"Canta": elque, "Palo": "basto" ,"Jugador": i}
                    message = json.dumps(mano_send)
                    await self.send_message_to_all_sockets(message)
                    if i == 0: 
                        cantado1[0] = True
                        if elque == "20": puntosJugador0 += 20
                        if elque == "40": puntosJugador0 += 40
                    else:
                        cantado1[1] = True
                        if elque == "20": puntosJugador1 += 20
                        if elque == "40": puntosJugador1 += 40
                        
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
                    else:
                        cantado1[2] = True
                        if elque == "20": puntosJugador1 += 20
                        if elque == "40": puntosJugador1 += 40
                        
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
                    else:
                        cantado1[3] = True
                        if elque == "20": puntosJugador1 += 20
                        if elque == "40": puntosJugador1 += 40
                
                if tiene_siete_triunfo and not arrastre and puede_cantar_cambiar == i:
                    posibilidad[i] = True
        
        for i in range(2):
                mano_send = {"Cambiar7": posibilidad[i]}
                message = json.dumps(mano_send)
                await self.send_message_to_socket(str(i), message)
        
        if posibilidad[0] or posibilidad[1]:
            x = 0
            if posibilidad[1]:
                x = 1
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
        
        for a in range(2):
            await self.send_message_to_socket(str(a), message)
                             
        return cantado0, cantado1, puntosJugador0, puntosJugador1, triunfo
    
    async def fin_partida(self, client_list, ganador, puntosJugador0, puntosJugador1):
        print("METE AQUI LO DE BD")