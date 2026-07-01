# Este archivo contiene la implementacion de la clase Event (11.11.10)
""" Un objeto de la clase Event encapsula la informacion que se intercambia 
entre las entidades activas de un sistema distribuido """

# ----------------------------------------------------------------------------------------		
class Event:                   # Descendiente de la clase "object" (default)
    """ Atributos: "name", "time", "target" y "source", 
    contiene tambien un constructor y los metodos que devuelven cada
    uno de los atributos individuales """
    
    def __init__(self, name, time, target, source, payload=None):
        """ Construye una instancia con los atributos inicializados """
        self.name   = name
        self.time   = time        
        self.target = target        
        self.source = source
        self.payload = payload
        
		
    def getName(self):
        return self.name
		
    def getTime(self):
        """ Devuelve el tiempo en el que debe ocurrir el evento """
        return (self.time)
		
    def getTarget(self):
        """ Devuelve la identidad del proceso al que va dirigido """
        return (self.target)
		
    def getSource(self):
        """ Devuelve la identidad del proceso que origina el evento """
        return (self.source)

    def getPayload(self):
        """ Devuelve el contenido transportado por el evento, si existe """
        return (self.payload)
	