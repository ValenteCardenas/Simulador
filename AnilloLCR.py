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

for i in [random.randint(1, len(experiment.graph)), random.randint(1, len(experiment.graph))]:
    seed = Event("INICIA", 0.0, i, i, 0)
    experiment.init(seed) 

experiment.run()