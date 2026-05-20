# 
# Implementa la simulacion de un PING/PONG
#
# Elaboro: Elizabeth Perez Cortes
#

import sys
from event import Event
from model import Model
from process import Process
from simulator import Simulator
from simulation import Simulation
import random as rd


class AlgorithmPingPong(Model):
  # Esta clase desciende de la clase Model e implementa los metodos 
  # "init()" y "receive()", que en la clase madre se definen como abstractos
  
  def init(self):
    # Aqui se definen e inicializan los atributos particulares del algoritmo
    print ("Inicio funciones", self.id)
    self.sucesor = self.neighbors[0]
    print ("Mi vecino es:", self.sucesor)

   #c. Para que el proceso tarde un númeor aleatorio entre 1 y 4 unidades de tiempo
   # utilizaremos la función randint del módulo random, que devuelve un número entero 
   # aleatorio entre los dos valores que se le pasan como parámetros. En este caso, se le pasan 1 y 4, por lo que devolverá un número entero aleatorio entre 1 y 4
  def receive(self, event):
    # Aqui se definen las acciones concretas que deben ejecutarse cuando se
    # recibe un evento
    if event.getName() == "INICIA":
       print ("[", self.id, "]: recibi INICIA en t=",self.clock," \n")
       newevent = Event("PING", self.clock + rd.randint(1, 4), self.sucesor, self.id)
       self.transmit(newevent)
    elif  event.getName() == "PING":
       print ("[", self.id, "]: recibi PING en t=",self.clock," \n")
       newevent = Event("PONG", self.clock + rd.randint(1, 4), self.sucesor, self.id)
       self.transmit(newevent)
    else:      
       print ("[", self.id, "]: recibi PONG en t=",self.clock," \n")
       newevent = Event("PING", self.clock + rd.randint(1, 4), self.sucesor, self.id)
       self.transmit(newevent)
  

# ----------------------------------------------------------------------------------------
# "main()"
# ----------------------------------------------------------------------------------------
# construye una instancia de la clase Simulation recibiendo como parametros el nombre del 
# archivo que codifica la lista de adyacencias de la grafica y el tiempo max. de simulacion

if len(sys.argv) != 2:
   print ("Por favor proporcione el nombre de la grafica de comunicaciones")
   raise SystemExit(1)

experiment = Simulation(sys.argv[1], 20)  

# asocia un pareja proceso/modelo con cada nodo de la grafica
for i in range(1,len(experiment.graph)+1):
    m = AlgorithmPingPong()
    experiment.setModel(m, i)

# inserta un evento semilla en la agenda y arranca
#b.Para que sea el nodo 2 el que inicie el proceso, se le asigna como fuente 
# y destino del evento semilla el nodo 2, y se le asigna el nombre "INICIA" 
# para que al recibirlo, el nodo 2 ejecute la parte del codigo que corresponde
# a ese evento, y asi inicie el proceso de ping pong.

#d.Para que el proceso inicie de manera aleatoria utilizaremos randint
#Dentro del metodo rand también podríamos usar len(experiment.graph) para que el 
#proceso se inicie en un nodo aleatorio de nuestro grafo, pero como solo tenemos 2 
#nodos, asignamos el valor 2 directamente.
seed = Event("INICIA", 0.0, rd.randint(1,2), rd.randint(1,2))
experiment.init(seed)
experiment.run()


