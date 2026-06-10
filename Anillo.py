import sys
import random
from event import Event
from model import Model
from simulation import Simulation

class AlgorithmAnillo(Model):
    def init(self):
        self.succesor = self.neighbors[0]  # En un anillo, el sucesor es el primer vecino
        self.solicitud_sc = False

    def receive(self, event):
        if event.getName() == "SOLICITUD":
            lanzar_moneda = random.choice([1,2,3,4])
            elegir = random.choice([1,2,3,4])
            if lanzar_moneda == elegir:
                print(f"[t={self.clock}] Nodo {self.id} decidió ENVIAR petición a la seccion crítica.")
                self.solicitud_sc = True
            else:
                print(f"[t={self.clock}] Nodo {self.id} decidió NO enviar petición.")
                
        elif event.getName() == "TOKEN":
            if self.solicitud_sc == False:
                print(f"[t={self.clock}] Nodo {self.id} tiene TOKEN y no tiene solicitud pendiente. Enviando Token al sucesor.")
                self.succesor = self.neighbors[0]
                newevent = Event("TOKEN", self.clock + 1.0, self.succesor, self.id)
                self.transmit(newevent)
            else:
                print(f"[t={self.clock}] Nodo {self.id} envía OK a la aplicacion.")
                newevent = Event("OK", self.clock + 1.0, self.id, self.id)
                self.transmit(newevent)
        
        elif event.getName() == "LIBERA":
            print(f"Se recibió LIBERA del nodo {event.getSource()}. Enviando TOKEN al sucesor.")
            self.solicitud_sc = False
            self.succesor = self.neighbors[0]
            newevent = Event("TOKEN", self.clock + 1.0, self.succesor, self.id)
            self.transmit(newevent)

        elif event.getName() == "OK":
            print(f"Se recibió OK en la aplicación del nodo {self.id}. Enviando LIBERA.")
            newevent = Event("LIBERA", self.clock + 1.0, self.id, self.id)
            self.transmit(newevent)
        
##main
if len(sys.argv) != 2:
   print ("Por favor proporcione el nombre de la grafica de comunicaciones")
   raise SystemExit(1)

experiment = Simulation(sys.argv[1], 20)

for i in range(1, len(experiment.graph) + 1):
    m = AlgorithmAnillo()
    experiment.setModel(m, i)

for i in range(1, len(experiment.graph) + 1):
    seed2 = Event("SOLICITUD", 0.0, i, i)
    experiment.init(seed2)

genera_token = random.randint(1, len(experiment.graph))   
print(f"El token lo genera el nodo {genera_token}.")
seed = Event("TOKEN", 0.0, genera_token, genera_token)  
experiment.init(seed)

experiment.run()





