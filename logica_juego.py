import random

#Crear la baza
def crear_mazo():
    palos = ("oro", "copa", "espada", "basto")
    valores = (1, 2, 3, 4, 5, 6, 7, 10, 11, 12)
    mazo = [(palo, valor) for palo in palos for valor in valores]
    return mazo

#Repartir las cartas
def repartir_cartas(mazo, numJugadores):
    manos = []
    for i in range(numJugadores):
        mano = random.sample(mazo, 6)
        manos.append(mano)
        for carta in mano:
            mazo.remove(carta)
    return manos, mazo

#Suma de puntos de la baza
def sumar_puntos(baza):
    #Recorrer la baza y sumar los puntos
    valores_cartas = {1: 11, 3: 10, 12: 4, 10: 3, 11: 2}
    puntos = 0
    for _, numCarta in baza:
        puntos += valores_cartas.get(numCarta, 0)
    return puntos

#Comprobar si la jugada es valida
def que_jugador_gana_baza(baza, triunfo):
    valorCarta = [2,4,5,6,7,11,10,12,3,1]
    cartaAlta = baza[0]
    for i in range(len(baza)):
        #Si son del mismo palo
        if cartaAlta[0] == baza[i][0]:
            valorCartaAlta = valorCarta.index(cartaAlta[1])
            valorCartaNueva = valorCarta.index(baza[i][1])
            if valorCartaAlta < valorCartaNueva:
                cartaAlta = baza[i]
        #Si no son del mismo palo
        else:
            #Si la nueva carta es del triunfo
            if baza[i][0] == triunfo[0]:
                cartaAlta = baza[i]     
    return cartaAlta


def que_cartas_puede_usar_jugador_arrastre(mano, baza, triunfo):
    triunfo = triunfo[0]
    if len(baza) == 1:
        return si_puedo_tengo_que_superar(mano, baza, triunfo)
    elif len(baza) == 2:
        cartaAlta = que_jugador_gana_baza(baza, triunfo)
        if cartaAlta != baza[0]:
            return si_puedo_tengo_que_superar(mano, baza, triunfo)
        else:
            return no_tengo_que_superar(mano, baza)
    elif len(baza) == 3:
        cartaAlta = que_jugador_gana_baza(baza, triunfo)
        if cartaAlta != baza[1]:
            return si_puedo_tengo_que_superar(mano, baza, triunfo)
        else:
            return no_tengo_que_superar(mano, baza)
        
                
def si_puedo_tengo_que_superar(mano, baza, triunfo):
    valorCarta = [2,4,5,6,7,11,10,12,3,1]
    cartasPosibles = []
    cartasPosiblesMayores = []
    cartasTriunfos = []
    palo = baza[0][0]
    if palo == triunfo:
        for x in range(len(mano)):
            if mano[x][0] == triunfo:
                cartasPosibles.append(mano[x])
            if len(cartasPosibles) == 0: return mano;
        for c in range(len(cartasPosibles)):
            cartasPosiblesValor = valorCarta.index(int(cartasPosibles[c][1]))
            cartaBazaValor = valorCarta.index(int(baza[0][1]))
            if cartasPosiblesValor > cartaBazaValor:
                cartasPosiblesMayores.append(cartasPosibles[c])
        if len(cartasPosiblesMayores) > 0: return cartasPosiblesMayores;
        else:return cartasPosibles;
    else:
        #Si no es triunfo 
        for x in range(len(mano)):
            if mano[x][0] == palo:
                cartasPosibles.append(mano[x])
        #Si tengo cartas del palo
        if len(cartasPosibles) > 0:
            for i in range(len(cartasPosibles)):
                cartasPosiblesValor = valorCarta.index(int(cartasPosibles[i][1]))
                cartaBazaValor = valorCarta.index(int(baza[0][1]))
                if cartasPosiblesValor > cartaBazaValor:
                    cartasPosiblesMayores.append(cartasPosibles[i])
            #Si tengo cartas de ese palo mayores
            if len(cartasPosiblesMayores) > 0: return cartasPosiblesMayores;
            #Si tengo cartas de ese palo pero no mayores
            else:return cartasPosibles;
        #Si no tengo cartas del palo ni trunfos juego lo que sea
        else:
            for x in range(len(mano)):
                if mano[x][0] == triunfo:
                    cartasTriunfos.append(mano[x])
            if len(cartasTriunfos) > 0: 
                return cartasTriunfos;
            else: 
                return mano;

def no_tengo_que_superar(mano, baza):
    cartasPosibles = []
    palo = baza[0][0]
    for i in range(len(mano)):
        if mano[i][0] == palo:
            cartasPosibles.append(mano[i])
    if len(cartasPosibles) > 0: return cartasPosibles;
    else: return mano;
    
 
def cantar_cambiar(mano, triunfo):
    tiene_siete_triunfo = False
    cantar_oro = False
    cantar_basto = False
    cantar_copa = False
    cantar_espada = False
        
    for carta in mano:
        palo, valor = carta
        if valor == 7 and palo == triunfo[0]:
            tiene_siete_triunfo = True
    
        if valor == 10 and palo == "oro":
            for carta in mano:
                palo, valor = carta
                if palo == "oro" and valor == 12:
                    cantar_oro = True
                    
        if valor == 10 and palo == "basto":
            for carta in mano:
                palo, valor = carta
                if palo == "basto" and valor == 12:
                    cantar_basto = True
                    
        if valor == 10 and palo == "copa":
            for carta in mano:
                palo, valor = carta
                if palo == "copa" and valor == 12:
                    cantar_copa = True
                    
        if valor == 10 and palo == "espada":
            for carta in mano:
                palo, valor = carta
                if palo == "espada" and valor == 12:
                    cantar_espada = True
    
    return tiene_siete_triunfo, cantar_oro, cantar_basto, cantar_copa, cantar_espada
    
                

validez = que_cartas_puede_usar_jugador_arrastre([("basto", 2), ("basto", 11), ("oro", 3)], [("copa", 5), ("basto", 4)], "espada")

suma = sumar_puntos([("espada", 3), ("espada", 1), ("basto", 5), ("oro", 5)])
#print(suma)

suma = cantar_cambiar([("espada", 10), ("espada", 12), ("espada", 7), ("oro", 10), ("oro", 12)], ("espada", 2))
#print(suma)

cartaGanadora = que_jugador_gana_baza([("espada", 3), ("espada", 1)], "oro")
#print(cartaGanadora)


         
                    
        