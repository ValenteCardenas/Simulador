import sys
import random
from event import Event
from model import Model
from simulation import Simulation

class AlgorithmClienteServidor(Model):
    def init(self):
        if self.id == 1:
            self.atendidas = 0
            self.estado = "LIBRE"
            self.cola = []
            print(f"[Nodo {self.id}] (Servidor) Inicializado.")
        else:
            print(f"[Nodo {self.id}] (Cliente) Inicializado.")

    def receive(self, event):
        if event.getName() == "INICIA":
            if self.id != 1:
                lanzar_moneda = random.choice([1,2,3,4])
                elegir = random.choice([1,2,3,4])
                if lanzar_moneda == elegir:
                    print(f"[t={self.clock}] Nodo {self.id} decidió ENVIAR petición al servidor.")
                    servidor = self.neighbors[0]
                    newevent = Event("SOLICITUD", self.clock + 1.0, servidor, self.id)
                    self.transmit(newevent)
                else:
                    print(f"[t={self.clock}] Nodo {self.id} decidió NO enviar petición.")
                
        elif event.getName() == "SOLICITUD":
            if self.id == 1:
                sender = event.source
                print(f"[t={self.clock}] Servidor recibe SOLICITUD de Nodo {sender}.")
                if self.estado == "LIBRE":
                    self.estado = "OCUPADO"
                    newevent = Event("OK", self.clock + 1.0, sender, self.id)
                    self.atendidas += 1
                    self.transmit(newevent)
                else:
                    print(f"[t={self.clock}] Servidor está OCUPADO. Nodo {sender} se agrega a la cola.")
                    self.cola.append(sender)

        elif event.getName() == "LIBERA":
            if self.cola:
                next_client = self.cola.pop(0)
                print(f"[t={self.clock}] Servidor libera y atiende al siguiente cliente en la cola: Nodo {next_client}.")
                newevent = Event("OK", self.clock + 1.0, next_client, self.id)
                self.atendidas += 1
                self.transmit(newevent)
            else:
                self.estado = "LIBRE"
                print(f"[t={self.clock}] Servidor se libera y no hay clientes en la cola.")
        
        elif event.getName() == "OK":
            print(f"[t={self.clock}] Nodo {self.id} recibió OK del Servidor (Petición Concedida).")
            newevent = Event("LIBERA", self.clock + 1.0, 1, self.id)
            self.transmit(newevent)
        

# ----------------------------------------------------------------------------------------
# "main()"
# ----------------------------------------------------------------------------------------
if len(sys.argv) != 2:
   print ("Por favor proporcione el nombre de la grafica de comunicaciones")
   raise SystemExit(1)

experiment = Simulation(sys.argv[1], 20)

for i in range(1, len(experiment.graph) + 1):
    m = AlgorithmClienteServidor()
    experiment.setModel(m, i)

for i in range(1, len(experiment.graph) + 1):
    seed = Event("INICIA", 0.0, i, i)
    experiment.init(seed)

experiment.run()

#Imprimimos cuantas peticiones fueron atendidas por el servidor
servidor = experiment.table[1].model  # El nodo 1 es el servidor
print(f"\nReporte Final: El Servidor atendió {servidor.atendidas} peticiones.")



