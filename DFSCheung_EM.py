import sys
import random
from event import Event
from model import Model
from simulation import Simulation

# =============================================================================
# DFS de Cheung con Exclusión Mutua Distribuida
# =============================================================================
# Fase 1: Construcción del árbol de expansión (DFS Cheung)
#   Mensajes: INICIA, DESCUBRE, RECHAZO, REGRESA, ARBOL_LISTO
#
# Fase 2: Exclusión mutua por circulación de TOKEN sobre el árbol
#   Mensajes nuevos:
#     - TOKEN  : Testigo que circula por el árbol DFS (recorrido Euler)
#     - OK     : El nodo con TOKEN y solicitud pendiente entra a la SC
#     - LIBERA : El nodo sale de la SC y continúa circulando el TOKEN
#
# El TOKEN realiza un recorrido Euler sobre el árbol:
#   Visita nodo → hijos en orden → regresa al padre → siguiente hermano → ...
#   En la raíz, al completar un ciclo, reinicia el recorrido.
#
# Ejemplo con árbol:
#         1 (raíz)
#        / \
#       2   3
#      /
#     4
#   Recorrido: 1 → 2 → 4 → (regresa) 2 → (regresa) 1 → 3 → (regresa) 1 → ...
# =============================================================================

# Probabilidad de que un nodo solicite la SC al recibir el TOKEN (1/PROB_DENOM)
PROB_SOLICITUD = 4  # 1 de cada 4 → 25% de probabilidad

# Número máximo de rondas completas del TOKEN (para terminación limpia)
MAX_RONDAS_TOKEN = 3


class DFSCheungEM(Model):
    """
    Modelo de nodo que implementa:
      - Fase 1: DFS de Cheung para construir un árbol de expansión
      - Fase 2: Exclusión mutua mediante circulación de TOKEN
    """
    # ---- Contadores globales (de clase) ----
    mensajes_dfs = 0        # Mensajes de la Fase 1 (DFS)
    mensajes_em = 0         # Mensajes de la Fase 2 (exclusión mutua)
    entradas_sc = 0         # Veces que algún nodo entró a la SC
    total_tiempo = 0        # Tiempo final de la simulación

    def init(self):
        # ---- Estado para Fase 1 (DFS) ----
        self.visitado = False
        self.padre = self.id            # Inicialmente cada nodo es su propio padre
        self.sin_visitar = list(self.neighbors)
        self.hijos = []                 # Lista de hijos en el árbol DFS
        self.arbol_construido = False

        # ---- Estado para Fase 2 (exclusión mutua) ----
        self.solicitud_sc = False       # ¿El nodo quiere entrar a la SC?
        self.hijo_actual_idx = 0        # Índice del siguiente hijo a visitar con TOKEN
        self.rondas_completadas = 0     # Solo la raíz lleva la cuenta de rondas

    # =====================================================================
    #  receive: Despacha cada mensaje al manejador correspondiente
    # =====================================================================
    def receive(self, event):
        nombre = event.getName()

        # ----------- Fase 1: Construcción del árbol DFS ----------
        if nombre == "INICIA":
            self._manejar_inicia(event)

        elif nombre == "DESCUBRE":
            self._manejar_descubre(event)

        elif nombre == "RECHAZO":
            self._manejar_rechazo(event)

        elif nombre == "REGRESA":
            self._manejar_regresa(event)

        elif nombre == "ARBOL_LISTO":
            self._manejar_arbol_listo(event)

        # ----------- Fase 2: Exclusión mutua con TOKEN ----------
        elif nombre == "TOKEN":
            self._manejar_token(event)

        elif nombre == "OK":
            self._manejar_ok(event)

        elif nombre == "LIBERA":
            self._manejar_libera(event)

    # =================================================================
    #  FASE 1: Manejadores de la construcción del árbol DFS
    # =================================================================

    def _manejar_inicia(self, event):
        """El nodo raíz arranca la exploración DFS."""
        self.visitado = True
        self.padre = self.id
        print(f"[t={self.clock:.1f}] [FASE 1] Nodo {self.id} INICIA la exploracion DFS (es la raiz)")
        self._continua_exploracion()

    def _manejar_descubre(self, event):
        """Un vecino nos envía DESCUBRE para explorarnos."""
        origen = event.getSource()

        # Eliminar al emisor de la lista de vecinos sin visitar
        if origen in self.sin_visitar:
            self.sin_visitar.remove(origen)

        if self.visitado:
            # Ya fuimos visitados → enviar RECHAZO
            rechazo = Event("RECHAZO", self.clock + 1, origen, self.id)
            self.transmit(rechazo)
            DFSCheungEM.mensajes_dfs += 1
        else:
            # Primera vez que nos visitan → adoptar como padre
            self.visitado = True
            self.padre = origen
            print(f"[t={self.clock:.1f}] [FASE 1] Nodo {self.id} descubierto, padre = {self.padre}")
            self._continua_exploracion()

    def _manejar_rechazo(self, event):
        """Nuestro vecino ya estaba visitado -> intentar siguiente vecino."""
        self._continua_exploracion()

    def _manejar_regresa(self, event):
        """Un hijo termino su sub-arbol y regresa -> registrarlo como hijo."""
        self.hijos.append(event.getSource())
        self._continua_exploracion()

    def _manejar_arbol_listo(self, event):
        """La raiz nos notifica que el arbol esta completo."""
        self.arbol_construido = True
        # Propagar ARBOL_LISTO a todos los hijos (recursivamente por el árbol)
        for hijo in self.hijos:
            aviso = Event("ARBOL_LISTO", self.clock + 1, hijo, self.id)
            self.transmit(aviso)
            DFSCheungEM.mensajes_em += 1

    def _continua_exploracion(self):
        """Continúa el DFS: enviar DESCUBRE al siguiente vecino o REGRESA al padre."""
        if len(self.sin_visitar) > 0:
            vecino = self.sin_visitar.pop(0)
            descubre = Event("DESCUBRE", self.clock + 1, vecino, self.id)
            self.transmit(descubre)
            DFSCheungEM.mensajes_dfs += 1
        else:
            # Sin vecinos por visitar
            if self.padre != self.id:
                # No somos raíz → regresar al padre
                regresa = Event("REGRESA", self.clock + 1, self.padre, self.id)
                self.transmit(regresa)
                DFSCheungEM.mensajes_dfs += 1
            else:
                # Somos la raíz → el árbol está completo
                self.arbol_construido = True
                print(f"\n{'='*60}")
                print(f"  [FASE 1 COMPLETA] Nodo {self.id} (raiz): Arbol DFS construido")
                print(f"  Hijos de la raiz: {self.hijos}")
                print(f"  Mensajes DFS: {DFSCheungEM.mensajes_dfs}")
                print(f"{'='*60}\n")

                # Notificar a todos que el árbol está listo
                arbol_listo = Event("ARBOL_LISTO", self.clock + 1, self.id, self.id)
                self.transmit(arbol_listo)
                DFSCheungEM.mensajes_em += 1

                # Iniciar Fase 2: enviar TOKEN a sí mismo
                print(f"  [FASE 2] Iniciando exclusion mutua - TOKEN circula por el arbol\n")
                token = Event("TOKEN", self.clock + 2, self.id, self.id)
                self.transmit(token)
                DFSCheungEM.mensajes_em += 1

    # =================================================================
    #  FASE 2: Manejadores de exclusión mutua (TOKEN, OK, LIBERA)
    # =================================================================

    def _manejar_token(self, event):
        """
        El nodo recibe el TOKEN.

        Decisión aleatoria: ¿solicitar la sección crítica?
          - Sí → Se envía OK a sí mismo (entra a la SC)
          - No → Pasa el TOKEN al siguiente nodo en el recorrido Euler
        """
        # Decisión dinámica: cada vez que el TOKEN llega, el nodo decide
        # si quiere entrar a la SC (simula un proceso real que puede o no
        # necesitar el recurso compartido en este momento).
        dado = random.randint(1, PROB_SOLICITUD)
        if dado == 1:
            self.solicitud_sc = True
            print(f"[t={self.clock:.1f}] [FASE 2] Nodo {self.id} recibe TOKEN y SOLICITA la SC")
        else:
            self.solicitud_sc = False

        if self.solicitud_sc:
            # Tiene solicitud pendiente → enviar OK (entrar a la SC)
            print(f"[t={self.clock:.1f}] [FASE 2] Nodo {self.id} tiene TOKEN + solicitud -> enviando OK")
            ok = Event("OK", self.clock + 1, self.id, self.id)
            self.transmit(ok)
            DFSCheungEM.mensajes_em += 1
        else:
            # Sin solicitud → pasar TOKEN al siguiente nodo
            print(f"[t={self.clock:.1f}] [FASE 2] Nodo {self.id} tiene TOKEN sin solicitud -> pasando TOKEN")
            self._pasar_token()

    def _manejar_ok(self, event):
        """
        El nodo entra a la sección crítica.
        Simula el uso del recurso compartido y luego se envía LIBERA a sí mismo.
        """
        DFSCheungEM.entradas_sc += 1
        print(f"[t={self.clock:.1f}] [FASE 2] *** Nodo {self.id} ENTRA a la seccion critica "
              f"(entrada #{DFSCheungEM.entradas_sc}) ***")

        # Simular el uso de la SC (duración = 1 unidad de tiempo)
        libera = Event("LIBERA", self.clock + 1, self.id, self.id)
        self.transmit(libera)
        DFSCheungEM.mensajes_em += 1

    def _manejar_libera(self, event):
        """
        El nodo sale de la seccion critica.
        Limpia su solicitud y continua pasando el TOKEN.
        """
        print(f"[t={self.clock:.1f}] [FASE 2] Nodo {self.id} SALE de la seccion critica -> pasando TOKEN")
        self.solicitud_sc = False
        self._pasar_token()

    def _pasar_token(self):
        """
        Pasa el TOKEN al siguiente nodo siguiendo el recorrido Euler del arbol:
          1. Si quedan hijos por visitar -> TOKEN al siguiente hijo
          2. Si ya visito todos los hijos -> TOKEN al padre
          3. Si es la raiz y ya visito todos -> reiniciar ciclo (nueva ronda)
        """
        if self.hijo_actual_idx < len(self.hijos):
            # Todavía hay hijos por visitar en este ciclo
            siguiente = self.hijos[self.hijo_actual_idx]
            self.hijo_actual_idx += 1
            token = Event("TOKEN", self.clock + 1, siguiente, self.id)
            self.transmit(token)
            DFSCheungEM.mensajes_em += 1
        else:
            # Ya visitamos todos los hijos → reiniciar índice para el próximo ciclo
            self.hijo_actual_idx = 0

            if self.padre != self.id:
                # No somos la raiz -> devolver TOKEN al padre
                token = Event("TOKEN", self.clock + 1, self.padre, self.id)
                self.transmit(token)
                DFSCheungEM.mensajes_em += 1
            else:
                # Somos la raiz -> completamos una ronda
                self.rondas_completadas += 1
                print(f"\n[t={self.clock:.1f}] [FASE 2] Raiz completo ronda "
                      f"{self.rondas_completadas}/{MAX_RONDAS_TOKEN} del TOKEN")

                if self.rondas_completadas < MAX_RONDAS_TOKEN:
                    # Reiniciar el ciclo del TOKEN
                    token = Event("TOKEN", self.clock + 1, self.id, self.id)
                    self.transmit(token)
                    DFSCheungEM.mensajes_em += 1
                else:
                    # Se alcanzo el limite de rondas -> terminar
                    DFSCheungEM.total_tiempo = self.clock
                    print(f"\n{'='*60}")
                    print(f"  [FIN] Exclusion mutua completada tras {MAX_RONDAS_TOKEN} rondas")
                    print(f"{'='*60}")


#  main


if len(sys.argv) != 2:
    print("Uso: python DFSCheung_EM.py <archivo_grafica>")
    print("  Ejemplo: python DFSCheung_EM.py g1.txt")
    raise SystemExit(1)

# Crear la simulación con tiempo suficiente para ambas fases
experiment = Simulation(sys.argv[1], 100)

# Instanciar un modelo para cada nodo de la gráfica
for i in range(1, len(experiment.graph) + 1):
    m = DFSCheungEM()
    experiment.setModel(m, i)

# Evento semilla: el nodo 1 inicia el DFS
seed = Event("INICIA", 0.0, 1, 1)
experiment.init(seed)

# Ejecutar la simulación
experiment.run()

# =============================================================================
#  Reporte final
# =============================================================================
total_mensajes = DFSCheungEM.mensajes_dfs + DFSCheungEM.mensajes_em

print(f"\n{'='*60}")
print(f"  REPORTE FINAL")
print(f"{'='*60}")
print(f"  Mensajes Fase 1 (DFS):             {DFSCheungEM.mensajes_dfs}")
print(f"  Mensajes Fase 2 (Exclusion Mutua): {DFSCheungEM.mensajes_em}")
print(f"  Total de mensajes:                 {total_mensajes}")
print(f"  Entradas a la seccion critica:     {DFSCheungEM.entradas_sc}")
print(f"  Tiempo total de simulacion:        {DFSCheungEM.total_tiempo:.1f}")
print(f"{'='*60}")
