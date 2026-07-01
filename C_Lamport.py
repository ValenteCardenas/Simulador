import sys
import random
from event import Event
from model import Model
from simulation import Simulation

class AlgoritmLamport(Model):
    def init(self):
        self.mi_estado = None
        self.visitado = False
        self.edo_canal = {vecino: [] for vecino in self.neighbors}
        self.canales_marcados = {vecino: False for vecino in self.neighbors}
        self.pendientes = 0

    def captura_estado_local(self):
        return {
            "visitado": self.visitado,
            "edo_canal": {vecino: list(mensajes) for vecino, mensajes in self.edo_canal.items()},
            "pendientes": self.pendientes,
        }
    
    def receive(self, event):
        if event.getName() == "INICIA":
            self.visitado = True
            self.pendientes = len(self.neighbors)
            self.mi_estado = self.captura_estado_local()
            for vecino in self.neighbors:
                newevent = Event("FOTO", self.clock + 1, vecino, self.id)
                self.transmit(newevent)
                AlgoritmLamport.total_mesajes += 1

        elif event.getName() == "FOTO":
            origen = event.getSource()

            if not self.visitado:
                self.visitado = True
                self.pendientes = len(self.neighbors) - 1
                self.canales_marcados[origen] = True
                self.mi_estado = self.captura_estado_local()
                print(f"Soy el nodo {self.id} y mi estado es {self.mi_estado}")
                for vecino in self.neighbors:
                    newevent = Event("FOTO", self.clock + 1, vecino, self.id)
                    self.transmit(newevent)
                    AlgoritmLamport.total_mesajes += 1
            else:
                if not self.canales_marcados[origen]:
                    self.canales_marcados[origen] = True
                    self.pendientes -= 1
                self.mi_estado = self.captura_estado_local()

            if self.pendientes == 0:
                print(f"Soy el nodo {self.id} y termine la toma de estado global")
        
        elif event.getName() == "m":
            origen = event.getSource()
            if self.visitado and not self.canales_marcados[origen]:
                self.edo_canal[origen].append(event.getPayload())