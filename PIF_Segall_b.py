import sys
import random
from event import Event
from model import Model
from simulation import Simulation

class AlgoritnmPIFShegall(Model):
    total_mensajes = 0
    tiempo_final = 0
    padres = {}              
    info_descendientes = {}  
    rutas = {}               # rutas[(target, time, source)] = (origen, destino)

    def init(self):
        self.visitado = False
        self.padre = None
        self.ok = {v: False for v in self.neighbors}
        self.hijos = []             
        self.descendientes = {}     
    
    def receive(self, event):
        if event.getName() == "INICIA":
            self.padre = self.id
            AlgoritnmPIFShegall.padres[self.id] = self.id
            self.visitado = True
            print(f"[t={self.clock}] Nodo {self.id} INICIA la exploracion")
            for v in self.neighbors:
                if v != self.padre:
                    print(f"[t={self.clock}] Nodo {self.id} envia M a {v}")
                    newevent = Event("M", self.clock + 1, v, self.id)
                    self.transmit(newevent)
                    AlgoritnmPIFShegall.total_mensajes += 1

        elif event.getName() == "M":
            j = event.getSource()
            self.ok[j] = True
            if not self.visitado:
                self.padre = j
                AlgoritnmPIFShegall.padres[self.id] = j
                print(f"[t={self.clock}] Soy nodo {self.id} mi padre es {j}")
                self.visitado = True
                for v in self.neighbors:
                    if v != self.padre:
                        print(f"[t={self.clock}] Nodo {self.id} envia M a {v}")
                        newevent = Event("M", self.clock + 1, v, self.id)
                        self.transmit(newevent)
                        AlgoritnmPIFShegall.total_mensajes += 1

            # Verificar si j es hijo de este nodo
            if AlgoritnmPIFShegall.padres.get(j) == self.id:
                self.hijos.append(j)
                self.descendientes[j] = AlgoritnmPIFShegall.info_descendientes.get(j, set())

            if all(self.ok[n] for n in self.neighbors):
                # Calcular el conjunto total de descendientes de este nodo
                todos_desc = set()
                for h in self.hijos:
                    todos_desc.add(h)
                    todos_desc.update(self.descendientes[h])
                AlgoritnmPIFShegall.info_descendientes[self.id] = todos_desc

                if self.padre != self.id:
                    print(f"[t={self.clock}] Nodo {self.id} envia M a {self.padre}")
                    print(f"  -> Hijos: {self.hijos}")
                    print(f"  -> Descendientes por hijo: { {h: sorted(self.descendientes[h]) for h in self.hijos} }")
                    newevent = Event("M", self.clock + 1, self.padre, self.id)
                    self.transmit(newevent)
                    AlgoritnmPIFShegall.total_mensajes += 1
                    AlgoritnmPIFShegall.tiempo_final = self.clock
                else:
                    AlgoritnmPIFShegall.tiempo_final = self.clock
                    print(f"[t={self.clock}] Arbol construido.")
                    print(f"  -> Nodo {self.id} (RAIZ) Hijos: {self.hijos}")
                    print(f"  -> Descendientes por hijo: { {h: sorted(self.descendientes[h]) for h in self.hijos} }")


        elif event.getName() == "MSG":
            clave = (self.id, self.clock, event.getSource())
            origen, destino = AlgoritnmPIFShegall.rutas.pop(clave)

            if destino == self.id:
                print(f"[t={self.clock}] Nodo {self.id}: *** Mensaje de nodo {origen} ENTREGADO ***")
            else:
                # Buscar si destino esta entre hijos o descendientes de algun hijo
                hijo_destino = None
                for h in self.hijos:
                    if h == destino or destino in self.descendientes.get(h, set()):
                        hijo_destino = h
                        break

                if hijo_destino is not None:
                    print(f"[t={self.clock}] Nodo {self.id}: Encamina MSG({origen}->{destino}) hacia hijo {hijo_destino}")
                    AlgoritnmPIFShegall.rutas[(hijo_destino, self.clock + 1, self.id)] = (origen, destino)
                    newevent = Event("MSG", self.clock + 1, hijo_destino, self.id)
                    self.transmit(newevent)
                    AlgoritnmPIFShegall.total_mensajes += 1
                
                elif self.padre != self.id:
                    print(f"[t={self.clock}] Nodo {self.id}: Encamina MSG({origen}->{destino}) hacia padre {self.padre}")
                    AlgoritnmPIFShegall.rutas[(self.padre, self.clock + 1, self.id)] = (origen, destino)
                    newevent = Event("MSG", self.clock + 1, self.padre, self.id)
                    self.transmit(newevent)
                    AlgoritnmPIFShegall.total_mensajes += 1
                
                else:
                    # Soy la raiz y destino no encontrado -> ERROR
                    print(f"[t={self.clock}] Nodo {self.id} (RAIZ): Destino {destino} NO encontrado -> ERROR a {origen}")
                    hijo_origen = None
                    for h in self.hijos:
                        if h == origen or origen in self.descendientes.get(h, set()):
                            hijo_origen = h
                            break
                    if hijo_origen is not None:
                        AlgoritnmPIFShegall.rutas[(hijo_origen, self.clock + 1, self.id)] = (origen, destino)
                        newevent = Event("ERROR", self.clock + 1, hijo_origen, self.id)
                        self.transmit(newevent)
                        AlgoritnmPIFShegall.total_mensajes += 1
                    else:
                        print(f"[t={self.clock}] Nodo {self.id}: *** ERROR - destino {destino} NO existe en el arbol ***")

        elif event.getName() == "ERROR":
            clave = (self.id, self.clock, event.getSource())
            origen, destino = AlgoritnmPIFShegall.rutas.pop(clave)

            if origen == self.id:
                print(f"[t={self.clock}] Nodo {self.id}: *** ERROR - destino {destino} NO existe en el arbol ***")
            else:
                hijo_origen = None
                for h in self.hijos:
                    if h == origen or origen in self.descendientes.get(h, set()):
                        hijo_origen = h
                        break

                if hijo_origen is not None:
                    print(f"[t={self.clock}] Nodo {self.id}: Encamina ERROR(destino {destino} no existe) hacia hijo {hijo_origen}")
                    AlgoritnmPIFShegall.rutas[(hijo_origen, self.clock + 1, self.id)] = (origen, destino)
                    newevent = Event("ERROR", self.clock + 1, hijo_origen, self.id)
                    self.transmit(newevent)
                    AlgoritnmPIFShegall.total_mensajes += 1
                elif self.padre != self.id:
                    print(f"[t={self.clock}] Nodo {self.id}: Encamina ERROR(destino {destino} no existe) hacia padre {self.padre}")
                    AlgoritnmPIFShegall.rutas[(self.padre, self.clock + 1, self.id)] = (origen, destino)
                    newevent = Event("ERROR", self.clock + 1, self.padre, self.id)
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

# Prueba 1: Nodo 7 envia mensaje al nodo 2
AlgoritnmPIFShegall.rutas[(7, 15.0, 7)] = (7, 2)
test1 = Event("MSG", 15.0, 7, 7)
experiment.init(test1)

# Prueba 2: Nodo 3 envia mensaje a nodo 99 (no existe -> ERROR)
AlgoritnmPIFShegall.rutas[(3, 25.0, 3)] = (3, 99)
test2 = Event("MSG", 25.0, 3, 3)
experiment.init(test2)

# Prueba 3: Nodo 2 envia mensaje al nodo 7
AlgoritnmPIFShegall.rutas[(2, 35.0, 2)] = (2, 7)
test3 = Event("MSG", 35.0, 2, 2)
experiment.init(test3)

experiment.run()

print(f"\nTotal de mensajes enviados: {AlgoritnmPIFShegall.total_mensajes}")
print(f"Costo en tiempo (unidades): {AlgoritnmPIFShegall.tiempo_final}")
