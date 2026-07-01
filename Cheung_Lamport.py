import sys
import random
import json
from event import Event
from model import Model
from simulation import Simulation


class AlgoritmCheungLamport(Model):
    total_mesajes = 0
    total_tiempo = 0

    def init(self):
        self.visitado = False
        self.padre = self.id
        self.sin_visitar = list(self.neighbors)
        self.hijos = []
        self.mi_estado = None
        self.edo_canal = {vecino: [] for vecino in self.neighbors}
        self.canales_marcados = {vecino: False for vecino in self.neighbors}
        self.pendientes = 0
        self.estado_guardado = False

    def captura_estado_local(self):
        return {
            "id": self.id,
            "padre": self.padre,
            "visitado": self.visitado,
            "sin_visitar": list(self.sin_visitar),
            "edo_canal": {vecino: list(mensajes) for vecino, mensajes in self.edo_canal.items()},
            "pendientes": self.pendientes,
        }

    def guarda_estado(self):
        self.mi_estado = self.captura_estado_local()
        self.estado_guardado = True
        nombre_archivo = f"estado_nodo_{self.id}_t{str(self.clock).replace('.', '_')}.json"
        with open(nombre_archivo, "w", encoding="utf-8") as archivo:
            json.dump(self.mi_estado, archivo, ensure_ascii=False, indent=2)
        print(f"Soy el nodo {self.id} y mi estado es {self.mi_estado}")

    def inicia_foto(self):
        self.pendientes = len(self.neighbors)
        self.guarda_estado()
        for vecino in self.neighbors:
            newevent = Event("FOTO", self.clock + 1, vecino, self.id)
            self.transmit(newevent)
            AlgoritmCheungLamport.total_mesajes += 1

    def continua_exploracion(self):
        if len(self.sin_visitar) > 0:
            vecino = self.sin_visitar.pop(0)
            newevent = Event("DESCUBRE", self.clock + 1, vecino, self.id)
            self.transmit(newevent)
            AlgoritmCheungLamport.total_mesajes += 1
        else:
            if self.padre != self.id:
                newevent = Event("REGRESA", self.clock + 1, self.padre, self.id)
                self.transmit(newevent)
                AlgoritmCheungLamport.total_mesajes += 1
            else:
                print(f"Soy el nodo {self.id} y soy mi propio padre, he terminado la exploración")
                AlgoritmCheungLamport.total_tiempo = self.clock
                for hijo in self.hijos:
                    newevent = Event("ARBOL_LISTO", self.clock + 1, hijo, self.id)
                    self.transmit(newevent)
                    AlgoritmCheungLamport.total_mesajes += 1

    def receive(self, event):
        if event.getName() == "INICIA":
            self.visitado = True
            self.padre = self.id
            self.inicia_foto()
            self.continua_exploracion()

        elif event.getName() == "DESCUBRE":
            origen = event.getSource()

            if origen in self.sin_visitar:
                self.sin_visitar.remove(origen)

            if self.visitado:
                newevent = Event("RECHAZO", self.clock + 1, origen, self.id)
                self.transmit(newevent)
                AlgoritmCheungLamport.total_mesajes += 1
            else:
                self.visitado = True
                self.padre = origen
                self.continua_exploracion()

        elif event.getName() == "ARBOL_LISTO":
            for hijo in self.hijos:
                aviso = Event("ARBOL_LISTO", self.clock + 1, hijo, self.id)
                self.transmit(aviso)
                AlgoritmCheungLamport.total_mesajes += 1

        elif event.getName() == "RECHAZO" or event.getName() == "REGRESA":
            if event.getName() == "REGRESA" and event.getSource() not in self.hijos:
                self.hijos.append(event.getSource())
            self.continua_exploracion()

        elif event.getName() == "FOTO":
            origen = event.getSource()

            if not self.estado_guardado:
                self.canales_marcados[origen] = True
                self.pendientes = len(self.neighbors) - 1
                self.guarda_estado()
                for vecino in self.neighbors:
                    newevent = Event("FOTO", self.clock + 1, vecino, self.id)
                    self.transmit(newevent)
                    AlgoritmCheungLamport.total_mesajes += 1
            else:
                if not self.canales_marcados[origen]:
                    self.canales_marcados[origen] = True
                    self.pendientes -= 1

            if self.pendientes == 0:
                print(f"Soy el nodo {self.id} y termine la toma de estado global")

        elif event.getName() == "m":
            origen = event.getSource()
            if self.visitado and not self.canales_marcados[origen]:
                self.edo_canal[origen].append(event.getPayload())


###main

if len(sys.argv) != 2:
    print("Por favor proporcione el nombre de la grafica de comunicaciones")
    raise SystemExit(1)

experiment = Simulation(sys.argv[1], 20)

for i in range(1, len(experiment.graph) + 1):
    m = AlgoritmCheungLamport()
    experiment.setModel(m, i)

seed = Event("INICIA", 0.0, 1, 1)
experiment.init(seed)

experiment.run()

print(f"Total de mensajes enviados: {AlgoritmCheungLamport.total_mesajes}")
print(f"Tiempo total de exploración: {AlgoritmCheungLamport.total_tiempo}")