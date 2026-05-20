import sys
import random
from event import Event
from model import Model
from simulation import Simulation


class AlgorithmStar(Model):
    def init(self):
        # En la gráfica g1.txt, el nodo 1 es el centro.
        if self.id == 1:
            # Inicializamos recursos con un número aleatorio entre 1 y 5
            self.recursos = random.randint(1, 5)
            # Contador de peticiones atendidas favorablemente
            self.atendidas = 0
            print(f"[Nodo {self.id}] (Centro) Inicializado con {self.recursos} recursos.")
        else:
            print(f"[Nodo {self.id}] (Periferia) Inicializado.")

    def receive(self, event):
        if event.getName() == "INICIA":
            if self.id != 1: 
                # Decisión aleatoria (True o False) en la periferia
                decide_enviar = random.choice([True, False])
                if decide_enviar:
                    print(f"[t={self.clock}] Nodo {self.id} decidió ENVIAR petición TRIS al centro.")
                    centro = self.neighbors[0] 
                    newevent = Event("TRIS", self.clock + 1.0, centro, self.id)
                    self.transmit(newevent)
                else:
                    print(f"[t={self.clock}] Nodo {self.id} decidió NO enviar petición.")

        elif event.getName() == "TRIS":
            if self.id == 1:
                sender = event.source
                print(f"[t={self.clock}] Centro recibe TRIS de Nodo {sender}.")
                
                # Revisar si aún hay recursos
                if self.recursos > 0:
                    self.recursos -= 1
                    self.atendidas += 1
                    # Responde con TRAS (Favorable)
                    newevent = Event("TRAS", self.clock + 1.0, sender, self.id)
                else:
                    # Responde con TRUS (Sin recursos)
                    newevent = Event("TRUS", self.clock + 1.0, sender, self.id)
                
                self.transmit(newevent)

        elif event.getName() == "TRAS":
            print(f"[t={self.clock}] Nodo {self.id} recibió TRAS del Centro (Petición Concedida).")

        elif event.getName() == "TRUS":
            print(f"[t={self.clock}] Nodo {self.id} recibió TRUS del Centro (Sin Recursos).")


# ----------------------------------------------------------------------------------------
# "main()"
# ----------------------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Por favor proporcione el nombre de la grafica de comunicaciones (ej. g1.txt)")
        raise SystemExit(1)

    experiment = Simulation(sys.argv[1], 50)  

    models = []
    for i in range(1, len(experiment.graph) + 1):
        m = AlgorithmStar()
        experiment.setModel(m, i)
        models.append(m)

    for i in range(1, len(experiment.graph) + 1):
        seed = Event("INICIA", 0.0, i, i)
        experiment.init(seed)

    experiment.run()

    # Imprimir el reporte final
    centro = models[0] # El nodo 1 es el centro y está en el índice 0
    print("\n--- SIMULACIÓN TERMINADA ---")
    print(f"Total de peticiones atendidas favorablemente: {centro.atendidas}")
    print(f"Número de recursos restantes: {centro.recursos}")