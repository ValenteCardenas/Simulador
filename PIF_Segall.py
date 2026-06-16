import sys
import random
from event import Event
from model import Model
from simulation import Simulation

class AlgoritnmPIFShegall(Model):
    total_mensajes = 0
    tiempo_final = 0

    def init(self):
        self.visitado = False
        self.padre = None
        self.ok = {v: False for v in self.neighbors}
    
    def receive(self, event):
        if event.getName() == "INICIA":
            self.padre = self.id
            self.visitado = True
            print(f"[t={self.clock}] Nodo {self.id} INICIA la exploracion")
            for v in self.neighbors:
                if v != self.padre:
                    print(f"[t={self.clock}] Nodo {self.id} envia M a {v}")
                    newevent = Event("M", self.clock + 1, v, self.id)
                    self.transmit(newevent)
                    AlgoritnmPIFShegall.total_mensajes += 1

        elif event.getName() == "M":
            self.ok[event.getSource()] = True
            if not self.visitado:
                self.padre = event.getSource()
                print(f"[t={self.clock}] Soy nodo {self.id} mi padre es {event.getSource()}")
                self.visitado = True
                for v in self.neighbors:
                    if v != self.padre:
                        print(f"[t={self.clock}] Nodo {self.id} envia M a {v}")
                        newevent = Event("M", self.clock + 1, v, self.id)
                        self.transmit(newevent)
                        AlgoritnmPIFShegall.total_mensajes += 1

            
            if all(self.ok[n] for n in self.neighbors):
                AlgoritnmPIFShegall.tiempo_final = self.clock
                if self.padre != self.id:
                    print(f"[t={self.clock}] Nodo {self.id} envia M a {self.padre}")
                    newevent = Event("M", self.clock + 1, self.padre, self.id)
                    self.transmit(newevent)
                    AlgoritnmPIFShegall.total_mensajes += 1

                    

##main

if len(sys.argv) != 2:
    print ("Por favor proporcione el nombre de la grafica de comunicaciones")
    raise SystemExit(1)

experiment = Simulation(sys.argv[1], 50)

for i in range(1, len(experiment.graph) + 1):
    m = AlgoritnmPIFShegall()
    experiment.setModel(m, i)

seed = Event("INICIA", 0.0, 1, 1)
experiment.init(seed)

experiment.run()

print(f"\nTotal de mensajes enviados: {AlgoritnmPIFShegall.total_mensajes}")
print(f"Costo en tiempo (unidades): {AlgoritnmPIFShegall.tiempo_final}")

