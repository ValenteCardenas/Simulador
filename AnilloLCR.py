import sys
import random
from event import Event
from model import Model
from simulation import Simulation

class AlgoritmAnilloLCR(Model):
    def init(self):
        self.id_lider = 0
        self.estado = "DORMIDO"
        self.id
        self.succesor = self.neighbors[0]
        
    def receive(self, event):
        if event.getName()[0] == "INICIA":
            print(f"Envio la candidatura inicial nodo: {self.id}")
            newevent = Event("CANDIDATURA", self.clock,self.succesor, self.id, self.id)
            self.estado = "DESPIERTO"
            self.transmit(newevent)
            
        elif event.getName()[0] == "CANDIDATURA":
            if(event.getName()[1] < self.id):
                if(self.estado == "DORMIDO"):
                    print(f"Estaba dormido, haré la revision, soy el nodo: {self.id}")
                    self.estado = "DESPIERTO"
                    print(f"Mi id es más alto que el evento, envio la candidatura inicial nodo: {self.id}")
                    newevent = Event("CANDIDATURA", self.clock,self.succesor, self.id, self.id)
                    self.transmit(newevent)

            elif(event.getName()[1] > self.id):
                if(self.estado == "DORMIDO"):
                    self.estado = "DESPIERTO"
                print(f"Estoy despierto, haré la revision, soy el nodo: {self.id}")
                print(f"El evento tiene un id más alto, lo voy a reenviar, soy el nodo: {self.id}")
                newevent = Event("CANDIDATURA", self.clock, self.succesor, self.id, event.getName()[1])
                
                self.transmit(newevent)
            else:
                print(f"Soy el nodo: {self.id}, y soy el líder electo")
                newevent = Event("ELECTO", self.clock, self.succesor, self.id, self.id)
                self.id_lider = event.getName()[1]
                self.transmit(newevent)
        
        elif event.getName()[0] == "ELECTO":
            self.id_lider = event.getName()[1]
            if(event.getName()[1] != self.id):
                print(f"No soy el líder pero ya actualicé la información, pasaré la elección, soy el nodo: {self.id}")
                newevent = Event("ELECTO", self.clock, self.succesor, self.id, self.id_lider)
                self.transmit(newevent)
            else:
                print(f"Fuí el vencedor para el nodo {self.id}, el líder electo es: {self.id_lider}")
###main

if len(sys.argv) != 2:
   print ("Por favor proporcione el nombre de la grafica de comunicaciones")
   raise SystemExit(1)

experiment = Simulation(sys.argv[1], 20)

for i in range(1, len(experiment.graph) + 1):
    m = AlgoritmAnilloLCR()
    experiment.setModel(m, i)

# a. El mejor caso en mensajes
# Se da cuando SOLO UN NODO arranca la elección (y no despierta a nadie más con su mensaje
# si los demás no inician por su cuenta, o si simplemente ignoran los menores). 
# Otra forma del mejor caso es que todos inicien pero el anillo esté ordenado ascendentemente.
# Con un solo nodo iniciando, generará N mensajes de elección y N de electo (2N en total).
# for i in [1]: 
#seed = Event("INICIA", 0.0, i, i, 0)
#experiment.init(seed)

# b. El mejor caso en tiempo
# Se da cuando todos los nodos inician al mismo tiempo (t=0.0). Las candidaturas menores
# se descartan rápido en red y el nodo de mayor id comienza a circular inmediatamente, 
# tomando exactamente 2N unidades de tiempo (N para dar la vuelta, N para anunciar).
# for i in range(1, len(experiment.graph) + 1):
#     seed = Event("INICIA", 0.0, i, i, 0)
#     experiment.init(seed)

# c. El peor caso en mensajes
# Se da cuando TODOS los nodos inician la elección al mismo tiempo (t=0.0) y además
# están ubicados en ORDEN DESCENDENTE en la dirección del anillo (ej. 6->5->4->3->2->1).
# El nodo 6 da N pasos, el 5 da N-1 pasos, el 4 da N-2 pasos... generando O(N^2) mensajes.
# Para correrlo necesitas un .txt ordenado al revés y activarlos todos:
# for i in range(1, len(experiment.graph) + 1):
#     seed = Event("INICIA", 0.0, i, i, 0)
#     experiment.init(seed)

# d. El peor caso en tiempo
# ¡Exacto! Ocurre cuando el nodo con el SEGUNDO ID más grande (ej. 5) despierta primero,
# y topológicamente está a N-1 de distancia del nodo de MAYOR ID (ej. 6), de forma
# que el mensaje da casi toda la vuelta. Justo antes de recibirlo (t = N-1), el
# nodo mayor (6) se despierta e inicia su proceso.
# Para un anillo 5->4->3->2->1->6(->5), donde N=6:
# seed1 = Event("INICIA", 0.0, 5, 5, 0)
# seed2 = Event("INICIA", 5.0, 6, 6, 0) # El 6 se despierta en t=N-1
# experiment.init(seed1)
# experiment.init(seed2)

# Elegimos los nodos 1 y 2 para despertarse al mismo tiempo
for i in [random.randint(1, len(experiment.graph)), random.randint(1, len(experiment.graph))]:
    seed = Event("INICIA", 0.0, i, i, 0)
    experiment.init(seed) 

# Se corre la simulación una sola vez, DESPUÉS de haber encolado los eventos iniciales
experiment.run()