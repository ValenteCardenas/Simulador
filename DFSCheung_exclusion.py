import sys
import random
from event import Event
from model import Model
from simulation import Simulation

class DFSCheungExclusion(Model):
    total_mensajes = 0

    def init(self):
        self.visitado = False
        self.padre = self.id          
        self.sin_visitar = list(self.neighbors)
        self.hijos = []               
        self.arbol_construido = False  

        
        self.solicitud_sc = False    
        self.hijo_actual_idx = 0      # indice del siguiente hijo a visitar con TOKEN

    def receive(self, event):
        nombre = event.getName()

        if nombre == "INICIA":
            self.visitado = True
            self.padre = self.id
            print(f"[t={self.clock}] Nodo {self.id} INICIA la exploracion DFS (es la raiz).")
            self.continua_exploracion()

        elif nombre == "DESCUBRE":
            if event.getSource() in self.sin_visitar:
                self.sin_visitar.remove(event.getSource())

            if self.visitado:
                newevent = Event("RECHAZO", self.clock + 1, event.getSource(), self.id)
                self.transmit(newevent)
                DFSCheungExclusion.total_mensajes += 1
            else:
                self.visitado = True
                self.padre = event.getSource()
                print(f"[t={self.clock}] Nodo {self.id} descubierto, padre = {self.padre}")
                self.continua_exploracion()

        elif nombre == "RECHAZO":
            self.continua_exploracion()

        elif nombre == "REGRESA":
            self.hijos.append(event.getSource())
            self.continua_exploracion()

        elif nombre == "SOLICITUD":
            lanzar_moneda = random.choice([1, 2, 3, 4])
            elegir = random.choice([1, 2, 3, 4])
            if lanzar_moneda == elegir:
                print(f"[t={self.clock}] Nodo {self.id} decidio SOLICITAR la seccion critica.")
                self.solicitud_sc = True
            else:
                print(f"[t={self.clock}] Nodo {self.id} decidio NO solicitar.")

        elif nombre == "TOKEN":
            self.procesar_token()

        elif nombre == "OK":
            print(f"[t={self.clock}] Nodo {self.id} ENTRA a la seccion critica. *")
            newevent = Event("LIBERA", self.clock + 1.0, self.id, self.id)
            self.transmit(newevent)
            DFSCheungExclusion.total_mensajes += 1

        elif nombre == "LIBERA":
            print(f"[t={self.clock}] Nodo {self.id} SALE de la seccion critica.")
            self.solicitud_sc = False
            self.continuar_recorrido_token()

        elif nombre == "ARBOL_LISTO":
            self.arbol_construido = True
            for hijo in self.hijos:
                newevent = Event("ARBOL_LISTO", self.clock + 1, hijo, self.id)
                self.transmit(newevent)
                DFSCheungExclusion.total_mensajes += 1

    def continua_exploracion(self):
        if len(self.sin_visitar) > 0:
            vecino = self.sin_visitar.pop(0)
            newevent = Event("DESCUBRE", self.clock + 1, vecino, self.id)
            self.transmit(newevent)
            DFSCheungExclusion.total_mensajes += 1
        else:
            if self.padre != self.id:
                newevent = Event("REGRESA", self.clock + 1, self.padre, self.id)
                self.transmit(newevent)
                DFSCheungExclusion.total_mensajes += 1
            else:
                self.arbol_construido = True
                print(f"\nArbol construido.")
                print(f"Hijos de la raiz: {self.hijos}")
                print(f"Total de mensajes: {DFSCheungExclusion.total_mensajes}")
                print("\n")
                print(f"Iniciando exclusion mutua con TOKEN")

                newevent = Event("ARBOL_LISTO", self.clock + 1, self.id, self.id)
                self.transmit(newevent)
                DFSCheungExclusion.total_mensajes += 1

                token_event = Event("TOKEN", self.clock + 2, self.id, self.id)
                self.transmit(token_event)
                DFSCheungExclusion.total_mensajes += 1

    def procesar_token(self):
        if self.solicitud_sc:
            print(f"[t={self.clock}] Nodo {self.id} tiene TOKEN y solicitud pendiente -> enviando OK.")
            newevent = Event("OK", self.clock + 1.0, self.id, self.id)
            self.transmit(newevent)
            DFSCheungExclusion.total_mensajes += 1
        else:
            print(f"[t={self.clock}] Nodo {self.id} tiene TOKEN sin solicitud -> pasando TOKEN.")
            self.continuar_recorrido_token()

    def continuar_recorrido_token(self):
        if self.hijo_actual_idx < len(self.hijos):
            siguiente_hijo = self.hijos[self.hijo_actual_idx]
            self.hijo_actual_idx += 1
            newevent = Event("TOKEN", self.clock + 1.0, siguiente_hijo, self.id)
            self.transmit(newevent)
            DFSCheungExclusion.total_mensajes += 1
        else:
            self.hijo_actual_idx = 0
            if self.padre != self.id:
                newevent = Event("TOKEN", self.clock + 1.0, self.padre, self.id)
                self.transmit(newevent)
                DFSCheungExclusion.total_mensajes += 1
            else:
                print(f"[t={self.clock}] Nodo {self.id} (raiz) reinicia el ciclo del TOKEN.")
                newevent = Event("TOKEN", self.clock + 1.0, self.id, self.id)
                self.transmit(newevent)
                DFSCheungExclusion.total_mensajes += 1

##main

if len(sys.argv) != 2:
    print("Por favor proporcione el nombre de la grafica de comunicaciones")
    raise SystemExit(1)

experiment = Simulation(sys.argv[1], 50)

for i in range(1, len(experiment.graph) + 1):
    m = DFSCheungExclusion()
    experiment.setModel(m, i)

seed_dfs = Event("INICIA", 0.0, 1, 1)
experiment.init(seed_dfs)

# Generar solicitudes aleatorias para todos los nodos
for i in range(1, len(experiment.graph) + 1):
    seed_solicitud = Event("SOLICITUD", 0.0, i, i)
    experiment.init(seed_solicitud)

experiment.run()

print(f"\nTotal de mensajes enviados: {DFSCheungExclusion.total_mensajes}")
