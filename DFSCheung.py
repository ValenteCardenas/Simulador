import sys
import random
from event import Event
from model import Model
from simulation import Simulation

class AlgoritmDFSCheung(Model):
    total_mesajes = 0
    total_tiempo = 0

    def init(self):
        self.visitado = False
        self.padre = self.id
        self.sin_visitar = list(self.neighbors)

    def receive(self, event):
        if event.getName() == "INICIA":
            self.visitado = True
            self.padre = self.id
            self.continua_exploracion()

        elif event.getName() == "DESCUBRE":
            if event.getSource() in self.sin_visitar:
                self.sin_visitar.remove(event.getSource())
            
            if self.visitado:
                newevent = Event("RECHAZO", self.clock + 1, event.getSource(), self.id)
                self.transmit(newevent)
                AlgoritmDFSCheung.total_mesajes += 1
            else:
                self.visitado = True
                self.padre = event.getSource()
                print(f"Soy el nodo {self.id} y mi padre es el nodo {self.padre}")
                self.continua_exploracion()
        
        elif event.getName() == "RECHAZO" or event.getName() == "REGRESA":
            self.continua_exploracion()
    
    def continua_exploracion(self):
        if len(self.sin_visitar) > 0:
            vecino = self.sin_visitar.pop(0)
            newevent = Event("DESCUBRE", self.clock + 1, vecino, self.id)
            self.transmit(newevent)
            AlgoritmDFSCheung.total_mesajes += 1
        else:
            if self.padre != self.id:
                newevent = Event("REGRESA", self.clock + 1, self.padre, self.id)
                self.transmit(newevent)
                AlgoritmDFSCheung.total_mesajes += 1
            else:
                print(f"Soy el nodo {self.id} y soy mi propio padre, he terminado la exploración")
                AlgoritmDFSCheung.total_tiempo = self.clock
###main

if len(sys.argv) != 2:
    print ("Por favor proporcione el nombre de la grafica de comunicaciones")
    raise SystemExit(1)

experiment = Simulation(sys.argv[1], 20)

for i in range(1, len(experiment.graph) + 1):
    m = AlgoritmDFSCheung()
    experiment.setModel(m, i)

seed = Event("INICIA", 0.0, 1, 1)
experiment.init(seed)

experiment.run()

print(f"Total de mensajes enviados: {AlgoritmDFSCheung.total_mesajes}")
print(f"Tiempo total de exploración: {AlgoritmDFSCheung.total_tiempo}")
