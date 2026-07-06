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

        # ── INICIA ────────────────────────────────────────────────────────
        # Solo inicia el DFS de Cheung. La toma de estado global se dispara
        # con el evento chl_INICIA_FOTO sembrado en el instante Teg.
        if nombre == "INICIA":
            self.visitado = True
            self.padre = self.id
            self.continua_exploracion()

        # ── chl_INICIA_FOTO ──────────────────────────────────────────────
        # Evento sembrado en el instante Teg para disparar la toma de
        # estado global de Chandy-Lamport en el nodo que lo recibe.
        elif nombre == "chl_INICIA_FOTO":
            if not self.chl_estado_guardado:
                self.chl_inicia_foto()

        # ── DESCUBRE ──────────────────────────────────────────────────────
        elif nombre == "DESCUBRE":
            # [Chandy-Lamport] Registrar mensaje aplicativo en transito
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

        # ── RECHAZO ───────────────────────────────────────────────────────
        elif nombre == "RECHAZO":
            # [Chandy-Lamport] Registrar mensaje aplicativo en transito
            if self.chl_estado_guardado and not self.chl_canales_marcados[origen]:
                self.chl_edo_canal[origen].append(nombre)

            self.continua_exploracion()

        # ── REGRESA ───────────────────────────────────────────────────────
        elif nombre == "REGRESA":
            # [Chandy-Lamport] Registrar mensaje aplicativo en transito
            if self.chl_estado_guardado and not self.chl_canales_marcados[origen]:
                self.chl_edo_canal[origen].append(nombre)

            if origen not in self.hijos:
                self.hijos.append(origen)
            self.continua_exploracion()

        # ── ARBOL_LISTO ───────────────────────────────────────────────────
        elif nombre == "ARBOL_LISTO":
            # [Chandy-Lamport] Registrar mensaje aplicativo en transito
            if self.chl_estado_guardado and not self.chl_canales_marcados[origen]:
                self.chl_edo_canal[origen].append(nombre)

            for hijo in self.hijos:
                aviso = Event("ARBOL_LISTO", self.clock + 1, hijo, self.id)
                self.transmit(aviso)
                AlgoritmCheungLamport.total_mesajes += 1

        # ── chl_FOTO ──────────────────────────────────────────────────────
        elif nombre == "chl_FOTO":
            print(
                f"Soy el nodo {self.id}: guardo estado del canal "
                f"{origen}->{self.id}: {self.chl_edo_canal[origen]}"
            )

            if not self.chl_estado_guardado:
                self.chl_canales_marcados[origen] = True
                self.chl_pendientes = len(self.neighbors) - 1
                self.chl_guarda_estado()
                for vecino in self.neighbors:
                    newevent = Event("chl_FOTO", self.clock + 1, vecino, self.id)
                    self.transmit(newevent)
                    AlgoritmCheungLamport.total_mesajes += 1
            else:
                if not self.chl_canales_marcados[origen]:
                    self.chl_canales_marcados[origen] = True
                    self.chl_pendientes -= 1

            if self.chl_pendientes == 0:
                print(
                    f"Soy el nodo {self.id} y termine la toma de estado global. "
                    f"Estado: {self.chl_mi_estado}"
                )

        # ── chl_m ─────────────────────────────────────────────────────────
        elif nombre == "chl_m":
            if self.chl_estado_guardado and not self.chl_canales_marcados[origen]:
                self.chl_edo_canal[origen].append(event.getPayload())


###main

if len(sys.argv) != 2:
    print("Por favor proporcione el nombre de la grafica de comunicaciones")
    raise SystemExit(1)

grafo = sys.argv[1]
maxtime = 50  # tiempo maximo de simulacion

# ══════════════════════════════════════════════════════════════════════
# Punto 2: Determinar el tiempo t que tarda la ejecucion del DFS
# ══════════════════════════════════════════════════════════════════════
print("=" * 60)
print("PUNTO 2: Ejecucion DFS puro para determinar el tiempo t")
print("=" * 60)

experiment = Simulation(grafo, maxtime)
for i in range(1, len(experiment.graph) + 1):
    m = AlgoritmCheungLamport()
    experiment.setModel(m, i)
seed = Event("INICIA", 0.0, 1, 1)
experiment.init(seed)
experiment.run()

t = AlgoritmCheungLamport.total_tiempo
print(f"\nTotal de mensajes enviados: {AlgoritmCheungLamport.total_mesajes}")
print(f"Tiempo total de exploracion (t): {t}")

# ══════════════════════════════════════════════════════════════════════
# Punto 3: Generar un numero aleatorio Teg entre 3 y t-3
# ══════════════════════════════════════════════════════════════════════
if t < 7:
    print(f"\nError: t={t} es demasiado pequeno para generar Teg en [3, t-3].")
    print("Elija un grafo mas grande.")
    raise SystemExit(1)

Teg = random.randint(3, int(t) - 3)
print(f"\nPunto 3: Teg generado: {Teg}")

# ══════════════════════════════════════════════════════════════════════
# Punto 4: Sembrar el evento chl_INICIA_FOTO en el instante Teg
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print(f"PUNTO 4: Ejecucion DFS + toma de estado global en Teg = {Teg}")
print("=" * 60)

num_nodos = len(experiment.graph)

# Reiniciar contadores de clase
AlgoritmCheungLamport.total_mesajes = 0
AlgoritmCheungLamport.total_tiempo = 0

# Crear nueva simulacion
exp = Simulation(grafo, maxtime)
for i in range(1, num_nodos + 1):
    m = AlgoritmCheungLamport()
    exp.setModel(m, i)

# Sembrar evento INICIA del DFS en t=0 dirigido al nodo 1
seed_dfs = Event("INICIA", 0.0, 1, 1)
exp.init(seed_dfs)

# Sembrar evento chl_INICIA_FOTO en el instante Teg dirigido al nodo 1
seed_foto = Event("chl_INICIA_FOTO", float(Teg), 1, 1)
exp.init(seed_foto)

exp.run()

print(f"\nTotal de mensajes enviados: {AlgoritmCheungLamport.total_mesajes}")
print(f"Tiempo total de exploracion: {AlgoritmCheungLamport.total_tiempo}")
