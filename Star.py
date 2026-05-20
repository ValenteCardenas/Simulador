import sys
import random
from event import Event
from model import Model
from simulation import Simulation


class AlgorithmStar(Model):
    def init(self):
        # En la gráfica g1.txt, el nodo 1 es el centro.
        if self.id == 1:
            # Contador de peticiones atendidas favorablemente
            self.atendidas = 0
            print(f"[Nodo {self.id}] (Centro) Inicializado.")
        else:
            print(f"[Nodo {self.id}] (Periferico) Inicializado.")

    def receive(self, event):
        if event.getName() == "INICIA":
            if self.id != 1: 
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
                newevent = Event("TRAS", self.clock + 1.0, sender, self.id)
                self.atendidas += 1
                self.transmit(newevent)

        elif event.getName() == "TRAS":
            print(f"[t={self.clock}] Nodo {self.id} recibió TRAS del Centro (Petición Concedida).")



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
    print(f"Total de peticiones atendidas favorablemente: {centro.atendidas}")