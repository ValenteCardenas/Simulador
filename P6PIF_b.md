# Explicación del Algoritmo PIF de Segall — Versión B

## Archivo: `PIF_Segall_b.py`

---

## 1. ¿Qué es este programa? (Explicación verbal)

Este programa implementa una **versión extendida del algoritmo PIF (Propagation of Information with Feedback) de Segall** sobre un simulador de sistemas distribuidos. A diferencia de la versión básica (`PIF_Segall.py`), que solamente construye un **árbol de expansión (spanning tree)** mediante inundación y retroalimentación, esta versión **b** agrega dos capacidades adicionales:

1. **Recopilación de información topológica**: Durante la construcción del árbol, cada nodo aprende quiénes son sus hijos directos y todos sus descendientes (nietos, bisnietos, etc.). Esta información se propaga de las hojas hacia la raíz durante la fase de retroalimentación.

2. **Enrutamiento de mensajes punto a punto**: Una vez construido el árbol, cualquier nodo puede enviar un mensaje a cualquier otro nodo. El mensaje se encamina subiendo al padre o bajando a un hijo según la tabla de descendientes. Si el destino no existe, se genera un mensaje de `ERROR` que se encamina de vuelta al emisor original.

En resumen: el programa **primero construye un árbol de expansión** y **luego usa ese árbol como infraestructura de enrutamiento** para comunicación unicast entre nodos arbitrarios.

---

## 2. Arquitectura del Simulador (Contexto)

El algoritmo se ejecuta sobre un simulador de eventos discretos compuesto por cuatro clases base:

| Clase | Archivo | Responsabilidad |
|-------|---------|----------------|
| `Event` | `event.py` | Encapsula un mensaje: nombre, tiempo, destino y origen |
| `Model` | `model.py` | Clase abstracta que define `init()` y `receive()` |
| `Process` | `process.py` | Entidad activa en un nodo; delega lógica al `Model` |
| `Simulation` | `simulation.py` | Lee la gráfica, crea procesos y ejecuta el motor |
| `Simulator` | `simulator.py` | Motor de simulación con agenda ordenada por tiempo |

El flujo general es:

```
Simulation lee grafo → crea Processes → asocia Models → inserta evento semilla → ejecuta run()
                                                                                      ↓
                                                                              Simulator extrae evento
                                                                                      ↓
                                                                              Process.receive(evento)
                                                                                      ↓
                                                                              Model.receive(evento)
```

---

## 3. Estructura de la Gráfica de Comunicaciones

La gráfica se lee de un archivo de texto (por ejemplo `g4.txt`). Cada línea `i` lista los vecinos del nodo `i+1`:

```
Línea 1: 2 3       → Nodo 1 tiene vecinos {2, 3}
Línea 2: 3 1 5     → Nodo 2 tiene vecinos {3, 1, 5}
Línea 3: 1 2 5     → Nodo 3 tiene vecinos {1, 2, 5}
Línea 4: 6         → Nodo 4 tiene vecinos {6}
Línea 5: 6 3 2     → Nodo 5 tiene vecinos {6, 3, 2}
Línea 6: 5 4       → Nodo 6 tiene vecinos {5, 4}
```

Esto representa una gráfica no dirigida de 6 nodos.

---

## 4. Explicación Técnica Línea por Línea

### 4.1 Importaciones y Definición de Clase (líneas 1–12)

```python
import sys
import random
from event import Event
from model import Model
from simulation import Simulation

class AlgoritnmPIFShegall(Model):
    total_mensajes = 0
    tiempo_final = 0
    padres = {}              
    info_descendientes = {}  
    rutas = {}               # rutas[(target, time, source)] = (origen, destino)
```

**Variables de clase** (compartidas por todos los nodos):

| Variable | Tipo | Propósito |
|----------|------|-----------|
| `total_mensajes` | `int` | Contador global de mensajes enviados en toda la simulación |
| `tiempo_final` | `int` | Marca de tiempo del último evento relevante |
| `padres` | `dict` | Mapea `nodo → padre` para todo el árbol. Permite que un nodo consulte la relación padre-hijo de otros nodos |
| `info_descendientes` | `dict` | Mapea `nodo → set(descendientes)`. Almacena el subárbol completo debajo de cada nodo |
| `rutas` | `dict` | Tabla de enrutamiento temporal. La clave `(target, time, source)` identifica unívocamente un mensaje en tránsito, y el valor `(origen, destino)` indica de dónde viene y a dónde va |

> **Nota técnica**: `padres`, `info_descendientes` y `rutas` son variables de clase (estáticas), accesibles desde cualquier instancia. Esto simula una "memoria compartida" que en un sistema real se construiría mediante el intercambio de mensajes.

---

### 4.2 Inicialización del Nodo — `init()` (líneas 14–19)

```python
def init(self):
    self.visitado = False
    self.padre = None
    self.ok = {v: False for v in self.neighbors}
    self.hijos = []             
    self.descendientes = {}     
```

Cada nodo inicializa:

| Atributo | Tipo | Significado |
|----------|------|-------------|
| `visitado` | `bool` | ¿Ya fue alcanzado por la onda de exploración? |
| `padre` | `int/None` | ID del nodo padre en el árbol (la raíz se asigna a sí misma) |
| `ok` | `dict{vecino: bool}` | Registro de qué vecinos ya respondieron. **El nodo no puede reportar hacia arriba hasta que todos sus vecinos hayan confirmado.** |
| `hijos` | `list` | Lista de hijos directos en el árbol |
| `descendientes` | `dict{hijo: set}` | Para cada hijo, el conjunto de todos los nodos debajo de él |

---

### 4.3 Manejo de Eventos — `receive()` (líneas 21–146)

El método `receive()` es el corazón del algoritmo. Maneja **cuatro tipos de eventos**:

#### 4.3.1 Evento `"INICIA"` (líneas 22–32) — Inicio de la exploración

```python
if event.getName() == "INICIA":
    self.padre = self.id                              # La raíz es su propio padre
    AlgoritnmPIFShegall.padres[self.id] = self.id     # Registra en la tabla global
    self.visitado = True
    print(f"[t={self.clock}] Nodo {self.id} INICIA la exploración")
    for v in self.neighbors:
        if v != self.padre:                           # A todos los vecinos excepto sí mismo
            newevent = Event("M", self.clock + 1, v, self.id)
            self.transmit(newevent)
            AlgoritnmPIFShegall.total_mensajes += 1
```

**Verbalmente**: El nodo raíz (nodo 1 en este caso) se marca como visitado, se declara su propio padre, y **envía un mensaje `M` a todos sus vecinos**. Cada mensaje se programa para el instante `self.clock + 1` (siguiente unidad de tiempo). Esto inicia la **onda de propagación** (flooding).

---

#### 4.3.2 Evento `"M"` (líneas 34–75) — Propagación y retroalimentación

Este es el evento más complejo. Un mensaje `"M"` cumple **doble función**:

- **Propagar** la exploración hacia adelante (cuando el nodo no ha sido visitado)
- **Confirmar** (feedback) hacia el padre (cuando todos los vecinos ya respondieron)

##### Paso 1: Registrar la respuesta del emisor

```python
j = event.getSource()
self.ok[j] = True
```

Se marca que el vecino `j` ya envió un mensaje. Esto es crucial: **el nodo necesita escuchar de TODOS sus vecinos** antes de poder reportar al padre.

##### Paso 2: Si no ha sido visitado → adoptar padre y propagar

```python
if not self.visitado:
    self.padre = j
    AlgoritnmPIFShegall.padres[self.id] = j
    self.visitado = True
    for v in self.neighbors:
        if v != self.padre:
            newevent = Event("M", self.clock + 1, v, self.id)
            self.transmit(newevent)
            AlgoritnmPIFShegall.total_mensajes += 1
```

**Verbalmente**: "Soy un nodo no visitado. El primer nodo que me contacta (`j`) se convierte en mi padre. Me marco como visitado y propago el mensaje `M` a todos mis demás vecinos."

##### Paso 3: Recopilar información de hijos

```python
if AlgoritnmPIFShegall.padres.get(j) == self.id:
    self.hijos.append(j)
    self.descendientes[j] = AlgoritnmPIFShegall.info_descendientes.get(j, set())
```

**Verbalmente**: "Si el nodo `j` que me acaba de enviar un mensaje tiene registrado que YO soy su padre en la tabla global `padres`, entonces `j` es mi hijo. Anoto a `j` como hijo y copio la información de todos sus descendientes."

> **Nota técnica**: Esto funciona porque cuando `j` envía el mensaje de vuelta a su padre (feedback), ya ha completado su propia exploración y ha registrado `info_descendientes[j]` con toda su información de subárbol.

##### Paso 4: Verificación de completitud y retroalimentación

```python
if all(self.ok[n] for n in self.neighbors):
    todos_desc = set()
    for h in self.hijos:
        todos_desc.add(h)
        todos_desc.update(self.descendientes[h])
    AlgoritnmPIFShegall.info_descendientes[self.id] = todos_desc

    if self.padre != self.id:
        # Enviar feedback al padre
        newevent = Event("M", self.clock + 1, self.padre, self.id)
        self.transmit(newevent)
    else:
        # Soy la raíz → el árbol está completo
        print(f"[t={self.clock}] Arbol construido.")
```

**Verbalmente**: "Cuando TODOS mis vecinos ya respondieron (`ok` es `True` para todos):

1. Calculo mi conjunto total de descendientes: la unión de todos mis hijos y los descendientes de cada hijo.
2. Guardo esa información en la tabla global `info_descendientes`.
3. Si NO soy la raíz, envío un mensaje `M` a mi padre (retroalimentación).
4. Si SOY la raíz, el árbol está completo."

**Este es el mecanismo de convergencia de Segall**: la información fluye de las hojas hacia la raíz. Las hojas son los primeros nodos en completar su `ok` (pues no tienen hijos a quienes propagar). Luego los nodos intermedios completan uno a uno hasta llegar a la raíz.

---

#### 4.3.3 Evento `"MSG"` (líneas 77–119) — Enrutamiento de mensajes punto a punto

Una vez construido el árbol, se pueden enviar mensajes entre nodos arbitrarios:

```python
elif event.getName() == "MSG":
    clave = (self.id, self.clock, event.getSource())
    origen, destino = AlgoritnmPIFShegall.rutas.pop(clave)
```

Primero se recupera la información de enrutamiento: ¿quién envió originalmente el mensaje y hacia dónde va?

##### Caso 1: El mensaje llegó a su destino

```python
if destino == self.id:
    print(f"Mensaje de nodo {origen} ENTREGADO")
```

##### Caso 2: El destino está en el subárbol de algún hijo → encaminar hacia abajo

```python
hijo_destino = None
for h in self.hijos:
    if h == destino or destino in self.descendientes.get(h, set()):
        hijo_destino = h
        break

if hijo_destino is not None:
    # Reenviar hacia el hijo apropiado
    AlgoritnmPIFShegall.rutas[(hijo_destino, self.clock + 1, self.id)] = (origen, destino)
    newevent = Event("MSG", self.clock + 1, hijo_destino, self.id)
    self.transmit(newevent)
```

**Verbalmente**: "Busco entre mis hijos y sus descendientes si alguno contiene al destino. Si lo encuentro, reenvío el mensaje hacia ese hijo."

##### Caso 3: El destino no está en mi subárbol → encaminar hacia arriba (al padre)

```python
elif self.padre != self.id:
    AlgoritnmPIFShegall.rutas[(self.padre, self.clock + 1, self.id)] = (origen, destino)
    newevent = Event("MSG", self.clock + 1, self.padre, self.id)
    self.transmit(newevent)
```

**Verbalmente**: "No encontré al destino debajo de mí. Paso el mensaje a mi padre para que busque en otra rama."

##### Caso 4: Soy la raíz y el destino no existe → generar ERROR

```python
else:
    # Soy la raíz y destino no encontrado → ERROR
    print(f"Destino {destino} NO encontrado → ERROR a {origen}")
    # Buscar al hijo que contiene al origen y encaminar ERROR hacia allá
    hijo_origen = None
    for h in self.hijos:
        if h == origen or origen in self.descendientes.get(h, set()):
            hijo_origen = h
            break
    if hijo_origen is not None:
        AlgoritnmPIFShegall.rutas[(hijo_origen, self.clock + 1, self.id)] = (origen, destino)
        newevent = Event("ERROR", self.clock + 1, hijo_origen, self.id)
        self.transmit(newevent)
```

**Verbalmente**: "Si soy la raíz y el destino no está en ninguna parte del árbol, genero un evento `ERROR` y lo encamino de vuelta al nodo que originó el mensaje."

---

#### 4.3.4 Evento `"ERROR"` (líneas 121–145) — Propagación de errores de vuelta al emisor

```python
elif event.getName() == "ERROR":
    clave = (self.id, self.clock, event.getSource())
    origen, destino = AlgoritnmPIFShegall.rutas.pop(clave)

    if origen == self.id:
        print(f"*** ERROR - destino {destino} NO existe en el arbol ***")
    else:
        # Encaminar el error hacia el nodo origen
        # (búsqueda en hijos o subir al padre)
```

**Verbalmente**: El error se encamina usando la misma lógica que `MSG`, pero en dirección inversa: buscando al **nodo origen** (el que intentó enviar el mensaje) en lugar del destino. Si el nodo actual ES el origen, muestra el error. Si no, lo reenvía hacia el hijo que contiene al origen o hacia el padre.

---

### 4.4 Programa Principal — `main` (líneas 148–182)

```python
# Validación de argumentos
if len(sys.argv) != 2:
    print("Por favor proporcione el nombre de la grafica de comunicaciones")
    raise SystemExit(1)

# Crear simulación con tiempo máximo 50
experiment = Simulation(sys.argv[1], 50)

# Crear e instalar un modelo por cada nodo de la gráfica
for i in range(1, len(experiment.graph) + 1):
    m = AlgoritnmPIFShegall()
    experiment.setModel(m, i)

# Evento semilla: el nodo 1 inicia la exploración en t=0
seed = Event("INICIA", 0.0, 1, 1)
experiment.init(seed)
```

#### Pruebas de enrutamiento programadas

| Prueba | Tiempo | Origen | Destino | Esperado |
|--------|--------|--------|---------|----------|
| 1 | t=15 | Nodo 7 → Nodo 2 | Entrega exitosa (si nodo 7 existe) |
| 2 | t=25 | Nodo 3 → Nodo 99 | ERROR (nodo 99 no existe en la gráfica) |
| 3 | t=35 | Nodo 2 → Nodo 7 | Entrega exitosa (si nodo 7 existe) |

```python
# Prueba 1: Nodo 7 envía mensaje al nodo 2
AlgoritnmPIFShegall.rutas[(7, 15.0, 7)] = (7, 2)
test1 = Event("MSG", 15.0, 7, 7)
experiment.init(test1)

# Prueba 2: Nodo 3 envía mensaje a nodo 99 (no existe → ERROR)
AlgoritnmPIFShegall.rutas[(3, 25.0, 3)] = (3, 99)
test2 = Event("MSG", 25.0, 3, 3)
experiment.init(test2)

# Prueba 3: Nodo 2 envía mensaje al nodo 7
AlgoritnmPIFShegall.rutas[(2, 35.0, 2)] = (2, 7)
test3 = Event("MSG", 35.0, 2, 2)
experiment.init(test3)

experiment.run()

print(f"\nTotal de mensajes enviados: {AlgoritnmPIFShegall.total_mensajes}")
print(f"Costo en tiempo (unidades): {AlgoritnmPIFShegall.tiempo_final}")
```

> **Nota**: La tabla `rutas` se pre-carga antes de ejecutar la simulación. Cuando el evento `MSG` llega al nodo indicado en el tiempo indicado, el nodo extrae `(origen, destino)` de `rutas` para saber qué hacer.

---

## 5. Diferencias con la Versión Básica (`PIF_Segall.py`)

| Característica | Versión Básica | Versión B |
|----------------|---------------|-----------|
| Construcción del árbol | ✅ Sí | ✅ Sí |
| Registro de `padres` global | ❌ No | ✅ Sí (`padres = {}`) |
| Registro de `hijos` por nodo | ❌ No | ✅ Sí (`self.hijos`) |
| Registro de `descendientes` | ❌ No | ✅ Sí (`self.descendientes`, `info_descendientes`) |
| Enrutamiento de mensajes `MSG` | ❌ No | ✅ Sí |
| Manejo de errores `ERROR` | ❌ No | ✅ Sí |
| Pruebas de comunicación | ❌ No | ✅ 3 pruebas programadas |

---

## 6. Flujo Visual del Algoritmo

### Fase 1: Construcción del Árbol (PIF)

```
       ┌─── Onda de propagación (M) ───►
       │
  RAÍZ ──► Nodos intermedios ──► Hojas
       │
       ◄─── Onda de retroalimentación (M) ───┘
              (con info de hijos y descendientes)
```

### Fase 2: Enrutamiento de Mensajes (MSG)

```
  Nodo origen                          Nodo destino
      │                                    ▲
      ▼ (sube al padre)                    │ (baja al hijo)
    Padre                                Padre
      │                                    ▲
      ▼ (sube al padre)                    │ (baja al hijo)
   Ancestro ─── ─── ─── ─── ─── ──► Ancestro
      │             (punto de giro:              │
      │          el destino está en              │
      │          el subárbol de un hijo)          │
```

### Fase 3: Manejo de Errores (ERROR)

```
  Nodo origen ◄──── ERROR ────── RAÍZ
                                   ▲
                    MSG (destino   │
                    no encontrado) │
  Nodo origen ───── MSG ──────────┘
```

---

## 7. Complejidad del Algoritmo

### Fase de Construcción del Árbol

- **Mensajes**: Cada arista del grafo transporta exactamente 2 mensajes (uno en cada dirección). Total: **2|E|** mensajes, donde |E| es el número de aristas.
- **Tiempo**: Proporcional al **diámetro** del grafo (la distancia más larga entre la raíz y una hoja en el árbol resultante).

### Fase de Enrutamiento

- **Mensajes por comunicación**: En el peor caso, un mensaje sube desde una hoja hasta la raíz y luego baja hasta otra hoja. Esto es **O(profundidad del árbol)** mensajes.
- **Detección de error**: Similar complejidad; el error sube hasta la raíz y baja hasta el origen.

---

## 8. Pseudocódigo del Algoritmo

### 8.1 Variables

```
─── Variables de clase (globales / compartidas) ───

total_mensajes   ← 0                    // Contador global de mensajes
tiempo_final     ← 0                    // Último instante de reloj registrado
padres           ← {}                   // Mapa: nodo → padre en el árbol
info_descendientes ← {}                 // Mapa: nodo → conjunto de descendientes
rutas            ← {}                   // Mapa: (target, time, source) → (origen, destino)

─── Variables de instancia (por nodo) ───

visitado         ← falso                // ¿El nodo ya fue alcanzado?
padre            ← nulo                 // ID del padre en el árbol
ok               ← {v: falso ∀ v ∈ vecinos}  // Registro de respuestas de vecinos
hijos            ← []                   // Lista de hijos directos
descendientes    ← {}                   // Mapa: hijo → conjunto de descendientes de ese hijo
```

### 8.2 Fase 1 — Construcción del Árbol (PIF)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Al recibir evento INICIA en nodo p:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  padre(p)   ← p                        // p es la raíz: su padre es él mismo
  padres[p]  ← p                        // Registrar en tabla global
  visitado(p) ← verdadero

  para cada vecino v de p, v ≠ p:
      enviar ⟨M⟩ a v en tiempo (reloj + 1)
      total_mensajes ← total_mensajes + 1
```

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Al recibir evento M de nodo j en nodo p:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ok(p)[j] ← verdadero                  // Marcar que j ya respondió

  ── Propagación (si p no ha sido visitado) ──
  si visitado(p) = falso:
      padre(p)   ← j                    // j se convierte en mi padre
      padres[p]  ← j                    // Registrar en tabla global
      visitado(p) ← verdadero

      para cada vecino v de p, v ≠ padre(p):
          enviar ⟨M⟩ a v en tiempo (reloj + 1)
          total_mensajes ← total_mensajes + 1

  ── Recopilación de información de hijos ──
  si padres[j] = p:                      // j declaró a p como su padre
      agregar j a hijos(p)
      descendientes(p)[j] ← info_descendientes[j]   // (∅ si j es hoja)

  ── Retroalimentación (cuando todos los vecinos respondieron) ──
  si ∀ n ∈ vecinos(p): ok(p)[n] = verdadero:

      // Calcular el conjunto total de descendientes de p
      todos_desc ← ∅
      para cada hijo h de p:
          todos_desc ← todos_desc ∪ {h} ∪ descendientes(p)[h]
      info_descendientes[p] ← todos_desc

      si padre(p) ≠ p:                  // p NO es la raíz
          enviar ⟨M⟩ a padre(p) en tiempo (reloj + 1)
          total_mensajes ← total_mensajes + 1
          tiempo_final ← reloj
      sino:                              // p ES la raíz
          tiempo_final ← reloj
          imprimir "Árbol construido"
          imprimir "Raíz p — Hijos: hijos(p)"
          imprimir "Descendientes por hijo: descendientes(p)"
```

### 8.3 Fase 2 — Enrutamiento de Mensajes Punto a Punto

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Al recibir evento MSG en nodo p:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  (origen, destino) ← rutas.extraer(p, reloj, fuente)

  ── Caso 1: El mensaje llegó a su destino ──
  si destino = p:
      imprimir "Mensaje de origen ENTREGADO"

  ── Caso 2: Buscar destino en subárbol de algún hijo ──
  sino:
      hijo_destino ← nulo
      para cada hijo h de p:
          si h = destino  ∨  destino ∈ descendientes(p)[h]:
              hijo_destino ← h
              romper

      si hijo_destino ≠ nulo:
          // Encaminar hacia abajo
          rutas[(hijo_destino, reloj+1, p)] ← (origen, destino)
          enviar ⟨MSG⟩ a hijo_destino en tiempo (reloj + 1)
          total_mensajes ← total_mensajes + 1

      ── Caso 3: No está en mi subárbol → subir al padre ──
      sino si padre(p) ≠ p:
          rutas[(padre(p), reloj+1, p)] ← (origen, destino)
          enviar ⟨MSG⟩ a padre(p) en tiempo (reloj + 1)
          total_mensajes ← total_mensajes + 1

      ── Caso 4: Soy la raíz y destino no existe → ERROR ──
      sino:
          imprimir "Destino no encontrado → ERROR"
          hijo_origen ← nulo
          para cada hijo h de p:
              si h = origen  ∨  origen ∈ descendientes(p)[h]:
                  hijo_origen ← h
                  romper

          si hijo_origen ≠ nulo:
              rutas[(hijo_origen, reloj+1, p)] ← (origen, destino)
              enviar ⟨ERROR⟩ a hijo_origen en tiempo (reloj + 1)
              total_mensajes ← total_mensajes + 1
          sino:
              imprimir "ERROR — destino no existe en el árbol"
```

### 8.4 Fase 3 — Propagación de Errores

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Al recibir evento ERROR en nodo p:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  (origen, destino) ← rutas.extraer(p, reloj, fuente)

  ── Caso 1: Yo soy el emisor original ──
  si origen = p:
      imprimir "ERROR — destino no existe en el árbol"

  ── Caso 2: Encaminar error hacia el emisor original ──
  sino:
      hijo_origen ← nulo
      para cada hijo h de p:
          si h = origen  ∨  origen ∈ descendientes(p)[h]:
              hijo_origen ← h
              romper

      si hijo_origen ≠ nulo:
          // El emisor original está debajo de mí → bajar
          rutas[(hijo_origen, reloj+1, p)] ← (origen, destino)
          enviar ⟨ERROR⟩ a hijo_origen en tiempo (reloj + 1)
          total_mensajes ← total_mensajes + 1

      sino si padre(p) ≠ p:
          // El emisor original no está debajo de mí → subir
          rutas[(padre(p), reloj+1, p)] ← (origen, destino)
          enviar ⟨ERROR⟩ a padre(p) en tiempo (reloj + 1)
          total_mensajes ← total_mensajes + 1
```

### 8.5 Programa Principal

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Programa principal:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Leer gráfica G del archivo de entrada
  Crear simulación con tiempo_máximo = 50

  para cada nodo i en G:
      crear instancia del modelo AlgoritnmPIFShegall
      asociar modelo al proceso i

  // Iniciar construcción del árbol desde nodo 1
  insertar evento ⟨INICIA, t=0, destino=1, fuente=1⟩

  // Programar pruebas de enrutamiento
  rutas[(7, 15, 7)] ← (7, 2)
  insertar evento ⟨MSG, t=15, destino=7, fuente=7⟩       // Nodo 7 → Nodo 2

  rutas[(3, 25, 3)] ← (3, 99)
  insertar evento ⟨MSG, t=25, destino=3, fuente=3⟩       // Nodo 3 → Nodo 99 (no existe)

  rutas[(2, 35, 2)] ← (2, 7)
  insertar evento ⟨MSG, t=35, destino=2, fuente=2⟩       // Nodo 2 → Nodo 7

  ejecutar simulación

  imprimir total_mensajes
  imprimir tiempo_final
```

---

## 9. Resumen Ejecutivo

`PIF_Segall_b.py` implementa un algoritmo distribuido en dos fases:

1. **Fase PIF (Propagation of Information with Feedback)**: Construye un árbol de expansión a partir de un nodo raíz mediante inundación controlada. Durante la retroalimentación, cada nodo reporta a su padre la lista completa de sus descendientes.

2. **Fase de Enrutamiento**: Usa las tablas de descendientes para encaminar mensajes unicast entre cualquier par de nodos. El enrutamiento sigue una política de "subir al padre si el destino no está en mi subárbol, bajar al hijo apropiado si está". Si el destino no existe en el árbol, se genera un mensaje de error que se encamina de vuelta al emisor original.

El algoritmo se ejecuta sobre un simulador de eventos discretos que modela el paso de mensajes en una red distribuida con tiempos discretos.
