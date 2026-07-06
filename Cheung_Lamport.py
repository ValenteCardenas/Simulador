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
        #Variables Cheung
        self.visitado = False
        self.padre = self.id
        self.sin_visitar = list(self.neighbors)
        self.hijos = []

        #Variables Chandy-Lamport
        self.chl_mi_estado = None
        self.chl_edo_canal = {vecino: [] for vecino in self.neighbors}
        self.chl_canales_marcados = {vecino: False for vecino in self.neighbors}
        self.chl_pendientes = 0
        self.chl_estado_guardado = False


    def chl_captura_estado_local(self):
        return {
            "id": self.id,
            "padre": self.padre,
            "visitado": self.visitado,
            "sin_visitar": list(self.sin_visitar),
            "chl_edo_canal": {
                vecino: list(msgs)
                for vecino, msgs in self.chl_edo_canal.items()
            },
            "chl_pendientes": self.chl_pendientes,
        }

    def chl_guarda_estado(self):
        self.chl_mi_estado = self.chl_captura_estado_local()
        self.chl_estado_guardado = True
        nombre_archivo = (
            f"estado_nodo_{self.id}_t{str(self.clock).replace('.', '_')}.json"
        )
        with open(nombre_archivo, "w", encoding="utf-8") as archivo:
            json.dump(self.chl_mi_estado, archivo, ensure_ascii=False, indent=2)
        print(f"Soy el nodo {self.id} y mi estado es {self.chl_mi_estado}")

    def chl_inicia_foto(self):
        self.chl_pendientes = len(self.neighbors)
        self.chl_guarda_estado()
        for vecino in self.neighbors:
            newevent = Event("chl_FOTO", self.clock + 1, vecino, self.id)
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
                print(
                    f"Soy el nodo {self.id} y soy mi propio padre, "
                    f"he terminado la exploracion"
                )
                AlgoritmCheungLamport.total_tiempo = self.clock
                for hijo in self.hijos:
                    newevent = Event("ARBOL_LISTO", self.clock + 1, hijo, self.id)
                    self.transmit(newevent)
                    AlgoritmCheungLamport.total_mesajes += 1


    def receive(self, event):
        nombre = event.getName()
        origen = event.getSource()

        if nombre == "INICIA":
            self.visitado = True
            self.padre = self.id
            self.chl_inicia_foto()
            self.continua_exploracion()

        elif nombre == "DESCUBRE":
            if self.chl_estado_guardado and not self.chl_canales_marcados[origen]:
                self.chl_edo_canal[origen].append(nombre)

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

        
        elif nombre == "RECHAZO":
            if self.chl_estado_guardado and not self.chl_canales_marcados[origen]:
                self.chl_edo_canal[origen].append(nombre)

            self.continua_exploracion()

        
        elif nombre == "REGRESA":
            if self.chl_estado_guardado and not self.chl_canales_marcados[origen]:
                self.chl_edo_canal[origen].append(nombre)

            if origen not in self.hijos:
                self.hijos.append(origen)
            self.continua_exploracion()

        
        elif nombre == "ARBOL_LISTO":
            if self.chl_estado_guardado and not self.chl_canales_marcados[origen]:
                self.chl_edo_canal[origen].append(nombre)

            for hijo in self.hijos:
                aviso = Event("ARBOL_LISTO", self.clock + 1, hijo, self.id)
                self.transmit(aviso)
                AlgoritmCheungLamport.total_mesajes += 1

        elif nombre == "chl_FOTO":
            # [Chandy-Lamport] Al llegar el marcador, ya se capturaron todos
            # los mensajes en transito de 'origen'; imprimir el estado del canal
            print(
                f"Soy el nodo {self.id}: guardo estado del canal "
                f"{origen}->{self.id}: {self.chl_edo_canal[origen]}"
            )

            if not self.chl_estado_guardado:
                # Primera vez que este nodo recibe un marcador:
                # marcar canal de llegada, guardar estado y reenviar marcadores
                self.chl_canales_marcados[origen] = True
                self.chl_pendientes = len(self.neighbors) - 1
                self.chl_guarda_estado()
                for vecino in self.neighbors:
                    newevent = Event("chl_FOTO", self.clock + 1, vecino, self.id)
                    self.transmit(newevent)
                    AlgoritmCheungLamport.total_mesajes += 1
            else:
                # Ya se guardo el estado local: solo cerrar canal si no marcado
                if not self.chl_canales_marcados[origen]:
                    self.chl_canales_marcados[origen] = True
                    self.chl_pendientes -= 1

            if self.chl_pendientes == 0:
                print(
                    f"Soy el nodo {self.id} y termine la toma de estado global. "
                    f"Estado: {self.chl_mi_estado}"
                )

        elif nombre == "chl_m":
            if self.chl_estado_guardado and not self.chl_canales_marcados[origen]:
                self.chl_edo_canal[origen].append(event.getPayload())


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
print(f"Tiempo total de exploracion: {AlgoritmCheungLamport.total_tiempo}")
