# Este archivo contiene la implementacion de la clase Process (11.11.10)
""" Cada objeto de la clase Process representa la entidad activa que reside en
un nodo de la grafica de comunicaciones """

# ----------------------------------------------------------------------------------------
class Process:                   # Descendiente de la clase "object" (default)
    """ Atributos: "neighbors", "engine", "id", "model",
    contiene tambien un constructor y los metodos "setModel()", 
    "transmit()" y "receive()" 	"""
	
    def __init__(self, neighbors, engine, id):
        """ asocia al proceso con su lista de vecinos, su motor de 
        simulacion y su identificador """
        self.neighbors = neighbors
        self.engine = engine
        self.id = id
		
    def setModel(self, model):
        """ asocia al proceso con el modelo que debe ejecutar y viceversa """
        self.model = model
        self.model.setProcess(self, self.neighbors, self.id)
        self.model.init()
		
    def setTime(self, time):
        """ actualiza el valor del reloj local """	
        self.model.setTime(time)
		
    def transmit(self, event):	
        """ invoca al motor para insertar un evento en su agenda """
        self.engine.insertEvent(event)
#        print "transmite mensaje"
		
    def receive(self, event):
        """ consulta a su modelo para decidir la atencion de un evento """
#        self.model.setTime(event.getTime())
        self.model.receive(event)

        
