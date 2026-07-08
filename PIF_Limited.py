import sys
import random
from event import Event
from model import Model
from simulation import Simulation

class AlgoritnmPIFShegallLimited(Model):
    total_mensajes = 0
    tiempo_final = 0

    def init(self):
        self.visitado = False
        self.padre = None
        self.ok = {v: False for v in self.neighbors}
        self.maxTTL = -1
    
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
                    AlgoritnmPIFShegallLimited.total_mensajes += 1

        elif event.getName() == "M":
            if (event.getPayload() > self.maxTTL):
                self.maxTTL = event.getPayload()
                self.padre = event.getSource()
                for v in self.neighbors:
                    self.ok[v] = False
                self.ok[self.padre] = True

                if (event.getPayload() > 0):
                    print(f"[t={self.clock}] Nodo {self.id} envia M a sus vecinos")
                    for v in self.neighbors:
                        if v != self.padre:
                            newevent = Event("M", self.clock + 1, v, self.id, event.getPayload() - 1)
                            self.transmit(newevent)
                else:
                    print(f"[t={self.clock}] Nodo {self.id} envia M a {self.padre}")
                    newevent = Event("M", self.clock + 1, self.padre, self.id)
                    self.transmit(newevent)
            else:
                self.ok[event.getSource()] = True
                newevent = Event("M", self.clock + 1, event.getSource(), self.id, event.getPayload())
                self.transmit(newevent)
            if (self.maxTTL > 0 and all(self.ok.values())):
                if self.padre != self.id:
                    print(f"[t={self.clock}] Nodo {self.id} envia M a {self.padre}")
                    newevent = Event("M", self.clock + 1, self.padre, self.id, self.maxTTL)
                    self.transmit(newevent)
            
            
                    

##main

if len(sys.argv) != 2:
    print ("Por favor proporcione el nombre de la grafica de comunicaciones")
    raise SystemExit(1)

experiment = Simulation(sys.argv[1], 50)

for i in range(1, len(experiment.graph) + 1):
    m = AlgoritnmPIFShegallLimited()
    experiment.setModel(m, i)

seed = Event("INICIA", 0.0, 1, 1)
experiment.init(seed)

experiment.run()

print(f"\nTotal de mensajes enviados: {AlgoritnmPIFShegallLimited.total_mensajes}")
print(f"Costo en tiempo (unidades): {AlgoritnmPIFShegallLimited.tiempo_final}")

