import sys
import random
from event import Event
from model import Model
from simulation import Simulation

#Código correspondinete a la exclusion mutua distribuida (EMD) de Ricart y Agrawala
#PDF: Practica6AD_26p.pdf
#PDF: AlgoritmosOrdenyEstadoGlobal_v2.pdf

class AlgoritmEMD(Model):
    def init(self):
        self.Tpeticion = 0
        self.Valor_mas_alto_recibido = 0
        self.Respuestas_pendientes = 0
        self.Solicitud_EM = False
        self.Solicitud_Pendiente = {}
    def receive(self, event):
        if event.getName() == "INICIA":
            if not self.Solicitud_EM:  # Solo intenta si no esta ya en proceso de solicitar
                if self.lanzar_moneda():
                    self.DLOCK()
                else:
                    # Si no quiso pedir la SC, vuelve a intentarlo mas adelante
                    self.transmit(Event("INICIA", self.clock + 1.0, self.id, self.id))

        elif event.getName() == "REQUEST":
            tpeticion_remota = getattr(event, "tpeticion", 0)
            self.Valor_mas_alto_recibido = max(self.Valor_mas_alto_recibido, tpeticion_remota)
            if not self.Solicitud_EM:
                newevent = Event("REPLY", self.clock + 1.0, event.getSource(), self.id)
                self.transmit(newevent)
            else:
                if (self.Tpeticion, self.id) > (tpeticion_remota, event.getSource()):
                    newevent = Event("REPLY", self.clock + 1.0, event.getSource(), self.id)
                    self.transmit(newevent)
                else:
                    self.Solicitud_Pendiente[event.getSource()] = True
        
        elif event.getName() == "REPLY":
            self.Respuestas_pendientes -= 1
            if self.Respuestas_pendientes == 0:
                print(f"[t={self.clock}] Nodo {self.id} entra a la seccion critica.")
                self.transmit(Event("LIBERA", self.clock + 1.0, self.id, self.id))

        elif event.getName() == "LIBERA":
            self.DUNLOCK()
            # Una vez que sale de la seccion critica, vuelve a iniciar el ciclo de intentos
            self.transmit(Event("INICIA", self.clock + 2.0, self.id, self.id))
        
    def lanzar_moneda(self):
        return random.random() < 0.20
    
    def DLOCK(self):
        self.Solicitud_EM = True
        self.Tpeticion = self.Valor_mas_alto_recibido + 1
        self.Valor_mas_alto_recibido = self.Tpeticion
        self.Respuestas_pendientes = len(self.neighbors)
        print(f"[t={self.clock}] Nodo {self.id} solicita acceso al recurso con Tpeticion={self.Tpeticion}.")
        for neighbor in self.neighbors:
            newevent = Event("REQUEST", self.clock + 1.0, neighbor, self.id)
            newevent.tpeticion = self.Tpeticion
            self.transmit(newevent)
        if self.Respuestas_pendientes == 0:
            print(f"[t={self.clock}] Nodo {self.id} entra a la seccion critica.")
            self.transmit(Event("LIBERA", self.clock + 1.0, self.id, self.id))
    
    def DUNLOCK(self):
        self.Solicitud_EM = False
        for neighbor in self.neighbors:
            if self.Solicitud_Pendiente.get(neighbor, False):
                newevent = Event("REPLY", self.clock + 1.0, neighbor, self.id)
                self.transmit(newevent)
                self.Solicitud_Pendiente[neighbor] = False

##main

if len(sys.argv) != 2:
   print ("Por favor proporcione el nombre de la grafica de comunicaciones")
   raise SystemExit(1)

experiment = Simulation(sys.argv[1], 20)

for i in range(1, len(experiment.graph) + 1):
    m = AlgoritmEMD()
    experiment.setModel(m, i)

for i in range(1, len(experiment.graph) + 1):
    seed = Event("INICIA", 0.0, i, i)
    experiment.init(seed)

experiment.run()