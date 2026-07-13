import sys
from event import Event
from model import Model
from simulation import Simulation

RETRASOS = {
    (3, 1): 1,   # P3 → P1 : rápido   (llega t=2)
    (3, 2): 6,   # P3 → P2 : lento    (llega t=7, DESPUÉS del mensaje de P1)
    (1, 2): 2,   # P1 → P2 : llega t=5, ANTES que el lento de P3
    (1, 3): 1,   # P1 → P3 : rápido   (llega t=4)
    (2, 1): 1,   # P2 → P1
    (2, 3): 1,   # P2 → P3
}

#Necesitamos un umbral de envio para que P2 no envie hasta recibir el mensaje de P1
#Si P3 no tuviera un umbral de envio, enviaria el mensaje inmediatamente
#de esta forma provocamos que el mensaje de P1 sea recibido antes que el de P3
#y provocamos el bloqueo de P2
UMBRAL_ENVIO = {
    1: 1,
    2: 2,
}

class AlgoritmoDCB(Model):
	def init(self):
		self.total_nodos = len(self.neighbors) + 1
		self.reloj_vectorial = [0 for _ in range(self.total_nodos)]
		self.cola_retraso = []
		self.id_mensaje_siguiente = 0
		self.mensajes_entregados = 0   # cuántos mensajes ha entregado este nodo
		self.ya_envio = False          # bandera: ya difundió su propio mensaje

	def receive(self, event):
		if event.getName() == "INICIA":
			print(f"[t={self.clock}] Nodo {self.id} inicia con VC={self.vector_a_texto()}")
			# Solo P3 arranca la cadena de mensajes del ejemplo
			if self.id == 3:
				nuevo_evento = Event("ENVIA", self.clock + 1, self.id, self.id)
				self.transmit(nuevo_evento)

		elif event.getName() == "ENVIA":
			# Garantizamos que cada nodo difunda exactamente un mensaje
			if self.ya_envio:
				return
			self.ya_envio = True

			self.reloj_vectorial[self.id - 1] += 1   # incrementa VC propio al enviar
			self.id_mensaje_siguiente += 1
			vector_mensaje = self.reloj_vectorial.copy()
			print(f"[t={self.clock}] Nodo {self.id} difunde m{self.id_mensaje_siguiente} con VC={self.vector_a_texto(vector_mensaje)}")

			for vecino in self.neighbors:
				retraso = RETRASOS.get((self.id, vecino), 1)
				nuevo_evento = Event("MENSAJE", self.clock + retraso, vecino, self.id)
				nuevo_evento.vector = vector_mensaje.copy()
				nuevo_evento.message_id = self.id_mensaje_siguiente
				self.transmit(nuevo_evento)

		elif event.getName() == "MENSAJE":
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
					entregado = True
					break

	def entregar_mensaje(self, event):
		vector_mensaje = event.vector.copy()
		id_mensaje = getattr(event, "message_id", 0)
		origen = event.getSource()

		for indice, valor in enumerate(vector_mensaje):
			if valor > self.reloj_vectorial[indice]:
				self.reloj_vectorial[indice] = valor

		print(f"[t={self.clock}] Nodo {self.id} libera m{id_mensaje} de {origen} y actualiza VC={self.vector_a_texto()}")

		self.mensajes_entregados += 1
		umbral = UMBRAL_ENVIO.get(self.id)
		if umbral is not None and self.mensajes_entregados == umbral and not self.ya_envio:
			nuevo_evento = Event("ENVIA", self.clock + 1, self.id, self.id)
			self.transmit(nuevo_evento)

	def es_entregable(self, event):
		indice_emisor = event.getSource() - 1
		vector_mensaje = event.vector

		if vector_mensaje[indice_emisor] != self.reloj_vectorial[indice_emisor] + 1:
			print(f"[t={self.clock}] Nodo {self.id} no puede liberar m{getattr(event, 'message_id', 0)} "
			      f"de {event.getSource()} porque VC[{indice_emisor}]={vector_mensaje[indice_emisor]} "
			      f"!= {self.reloj_vectorial[indice_emisor]} + 1")
			return False

		for indice in range(self.total_nodos):
			if indice == indice_emisor:
				continue
			if vector_mensaje[indice] > self.reloj_vectorial[indice]:
				print(f"[t={self.clock}] Nodo {self.id} no puede liberar m{getattr(event, 'message_id', 0)} "
				      f"de {event.getSource()} porque VC[{indice}]={vector_mensaje[indice]} "
				      f"> {self.reloj_vectorial[indice]}")
				return False

		return True

	def vector_a_texto(self, vector=None):
		if vector is None:
			vector = self.reloj_vectorial
		return "[" + ", ".join(str(valor) for valor in vector) + "]"


## main

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