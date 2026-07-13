import sys
import random
from event import Event
from model import Model
from simulation import Simulation

class AlgoritmoABIL(Model):
    total_mensajes = 0 #Metrica de simulacion (no es estado del algoritmo)
    def init(self):
        self.visitado = False
        num_productos = random.randint(2, 10)
        self.productos = [random.randint(1, 100) for _ in range(num_productos)]
        self.resultados = set()

    def receive(self, event):
        if event.getName() == "INICIA":
            payload = event.getPayload()
            ttl = payload[0]
            producto_buscado = payload[1]
            self.visitado = True

            print(f"[t={self.clock}] Nodo {self.id} INICIA busqueda del producto "
                  f"{producto_buscado} con TTL={ttl}")

            nodos_encontrados = []
            if producto_buscado in self.productos:
                nodos_encontrados.append(self.id)
                self.resultados.add(self.id)
                print(f"  -> Nodo {self.id} TIENE el producto {producto_buscado}")

            if ttl > 0:
                for v in self.neighbors:
                    newevent = Event("M", self.clock + 1, v, self.id,
                                     [ttl - 1, producto_buscado, self.id,
                                      list(nodos_encontrados)])
                    self.transmit(newevent)
                    AlgoritmoABIL.total_mensajes += 1
            else:
                print(f"[t={self.clock}] TTL=0, solo se verifico el emisor")


        elif event.getName() == "M": # (ttl, producto, emisor, lista)
            payload = event.getPayload()
            ttl = payload[0]
            producto_buscado = payload[1]
            emisor_id = payload[2]
            nodos_encontrados = list(payload[3])  # Copia para no mutar el original

            if not self.visitado:
                self.visitado = True

                print(f"[t={self.clock}] Nodo {self.id} recibe M de "
                      f"{event.getSource()}, TTL={ttl}")

                if producto_buscado in self.productos:
                    nodos_encontrados.append(self.id)
                    print(f"  -> Nodo {self.id} TIENE producto {producto_buscado}")

                if ttl > 0:
                    for v in self.neighbors:
                        if v != event.getSource():
                            newevent = Event("M", self.clock + 1, v, self.id,
                                             [ttl - 1, producto_buscado, emisor_id,
                                              list(nodos_encontrados)])
                            self.transmit(newevent)
                            AlgoritmoABIL.total_mensajes += 1
                else:
                    print(f"  Nodo {self.id} (hoja TTL=0), envia RETORNO "
                          f"a emisor {emisor_id} con nodos={nodos_encontrados}")
                    newevent = Event("RETORNO", self.clock + 1, emisor_id,
                                     self.id, nodos_encontrados)
                    self.transmit(newevent)
                    AlgoritmoABIL.total_mensajes += 1

        elif event.getName() == "RETORNO":
            nodos = event.getPayload()
            for n in nodos:
                self.resultados.add(n)
            print(f"[t={self.clock}] Nodo {self.id} recibe RETORNO de "
                  f"{event.getSource()}: nodos={nodos}")


## main

if len(sys.argv) != 2:
    print("Uso: python PI_Limited.py <archivo_topologia>")
    raise SystemExit(1)

#random.seed(123)  # Semilla para reproducibilidad

experiment = Simulation(sys.argv[1], 100)
TTL = 5
producto_buscado = random.randint(1, 100)

for i in range(1, len(experiment.graph) + 1):
    m = AlgoritmoABIL()
    experiment.setModel(m, i)

print(f"=== ABIL: Buscando producto {producto_buscado} con TTL={TTL} ===")
print(f"Red de {len(experiment.graph)} nodos\n")

seed = Event("INICIA", 0.0, 1, 1, [TTL, producto_buscado])
experiment.init(seed)

experiment.run()


# Obtener resultados del emisor (estado local del nodo 1)
emisor_modelo = experiment.table[1].model

# Ground truth: todos los nodos que realmente tienen el producto
todos_con_producto = []
for i in range(1, len(experiment.graph) + 1):
    modelo = experiment.table[i].model
    if producto_buscado in modelo.productos:
        todos_con_producto.append(i)

print(f"RESULTADOS FINALES")

print(f"Producto buscado: {producto_buscado}")
print(f"Nodos con producto (ground truth): {todos_con_producto} "
      f"({len(todos_con_producto)} nodos)")
print(f"Nodos encontrados por ABIL (TTL={TTL}): "
      f"{sorted(emisor_modelo.resultados)} "
      f"({len(emisor_modelo.resultados)} nodos)")
print(f"Total de mensajes enviados: {AlgoritmoABIL.total_mensajes}")

if len(todos_con_producto) > 0:
    falsos_negativos = [n for n in todos_con_producto
                        if n not in emisor_modelo.resultados]
    pct_fn = len(falsos_negativos) / len(todos_con_producto) * 100
    print(f"Falsos negativos: {falsos_negativos} ({len(falsos_negativos)} nodos)")
    print(f"% Falsos negativos: {pct_fn:.1f}%")
else:
    print(f"Ningun nodo tiene el producto {producto_buscado}")
