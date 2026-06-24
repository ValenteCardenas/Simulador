import sys
import random
from event import Event
from model import Model
from simulation import Simulation

class AlgoritmoDCB(Model):
	def init(self):
		self.total_nodos = len(self.neighbors) + 1
		self.reloj_vectorial = [0 for _ in range(self.total_nodos)]
		self.cola_retraso = []
		self.id_mensaje_siguiente = 0

	def receive(self, event):
		if event.getName() == "INICIA":
			print(f"[t={self.clock}] Nodo {self.id} inicia con VC={self.vector_a_texto()}")
			#if random.random() < 1.0 / self.total_nodos:
			self.programar_envio_local()


		elif event.getName() == "ENVIA":
			self.difundir_mensaje()
			if random.random() < 1.0 / (2 *self.total_nodos):
				self.programar_envio_local()

		elif event.getName() == "MENSAJE":
			self.recibir_mensaje(event)

	def recibir_mensaje(self, event):
		vector_mensaje = event.vector.copy()
		id_mensaje = getattr(event, "message_id", 0)
		origen = event.getSource()
		print(f"[t={self.clock}] Nodo {self.id} recibe m{id_mensaje} de {origen} con VC={vector_mensaje}")
		self.cola_retraso.append(event)
		self.entregar_mensajes_listos()

	def entregar_mensajes_listos(self):
		entregado = True
		while entregado:
			entregado = False
			for pendiente in list(self.cola_retraso):
				if self.es_entregable(pendiente):
					self.cola_retraso.remove(pendiente)
					self.entregar_mensaje(pendiente)
					#Volver a programar un envío local con probabilidad 1/(2N) después de entregar un mensaje
					if random.random() < 1.0 / (2 * self.total_nodos):
						self.programar_envio_local()
					entregado = True
					break

	def entregar_mensaje(self, event):
		vector_mensaje = event.vector.copy()
		#Utilizamos getattr para obtener el id del mensaje, proporcionando un valor predeterminado de 0 si no existe. Y como el 0 no es un id válido, nos aseguramos de que siempre se imprima un id de mensaje válido.
		#getattr es un método incorporado en Python que se utiliza para obtener el valor de un atributo de un objeto. En este caso, se está utilizando para obtener el valor del atributo "message_id" del objeto event. Si el atributo no existe, se devuelve un valor predeterminado de 0. Esto es útil para evitar errores si el atributo no está presente en el objeto event.
		id_mensaje = getattr(event, "message_id", 0)
		origen = event.getSource()

		self.reloj_vectorial[self.id - 1] #Se incrementa el reloj vectorial del nodo que entrega el mensaje
		for indice, valor in enumerate(vector_mensaje):
			if valor > self.reloj_vectorial[indice]:
				self.reloj_vectorial[indice] = valor

		print(f"[t={self.clock}] Nodo {self.id} libera m{id_mensaje} de {origen} y actualiza VC={vector_mensaje}")

	def es_entregable(self, event):
		indice_emisor = event.getSource() - 1
		vector_mensaje = event.vector

		if vector_mensaje[indice_emisor] != self.reloj_vectorial[indice_emisor] + 1:
			print(f"[t={self.clock}] Nodo {self.id} no puede liberar m{getattr(event, 'message_id', 0)} de {event.getSource()} porque VC[{indice_emisor}]={vector_mensaje[indice_emisor]} != {self.reloj_vectorial[indice_emisor]} + 1")
			return False

		for indice in range(self.total_nodos):
			if indice == indice_emisor:
				continue
			if vector_mensaje[indice] > self.reloj_vectorial[indice]:
				print(f"[t={self.clock}] Nodo {self.id} no puede liberar m{getattr(event, 'message_id', 0)} de {event.getSource()} porque VC[{indice}]={vector_mensaje[indice]} > {self.reloj_vectorial[indice]}")
				return False

		return True

	def difundir_mensaje(self):
		self.reloj_vectorial[self.id - 1] += 1 #Se incrementa el reloj vectorial del nodo que envía el mensaje
		self.id_mensaje_siguiente += 1
		vector_mensaje = self.reloj_vectorial.copy()
		print(f"[t={self.clock}] Nodo {self.id} difunde m{self.id_mensaje_siguiente} con VC={self.vector_a_texto(vector_mensaje)}")

		for vecino in self.neighbors:
			retraso = random.randint(1, self.total_nodos)
			nuevo_evento = Event("MENSAJE", self.clock + retraso, vecino, self.id)
			nuevo_evento.vector = vector_mensaje.copy()
			nuevo_evento.message_id = self.id_mensaje_siguiente
			self.transmit(nuevo_evento)

	def programar_envio_local(self):
		retraso = random.randint(1, self.total_nodos)
		nuevo_evento = Event("ENVIA", self.clock + retraso, self.id, self.id)
		self.transmit(nuevo_evento)

	def debe_enviar_inicialmente(self):
		return random.random() < 1.0 / self.total_nodos

	def vector_a_texto(self, vector=None):
		if vector is None:
			vector = self.reloj_vectorial
		return "[" + ", ".join(str(valor) for valor in vector) + "]"


##main

if len(sys.argv) != 2:
	print("Por favor proporcione el nombre de la grafica de comunicaciones")
	raise SystemExit(1)


experiment = Simulation(sys.argv[1], 50)

for i in range(1, len(experiment.graph) + 1):
	modelo = AlgoritmoDCB()
	experiment.setModel(modelo, i)

for i in range(1, len(experiment.graph) + 1):
	evento_semilla = Event("INICIA", 0.0, i, i)
	experiment.init(evento_semilla)

experiment.run()
    