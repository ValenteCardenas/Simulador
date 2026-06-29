# Documentación: Difusión Causal de Birman

**Archivo:** `DifusiónCausalBirdman.py`  
**Clase principal:** `AlgoritmoDCB` (hereda de `Model`)  
**Práctica:** 7 — Algoritmos Distribuidos, Trimestre 26P

---

## Descripción general

Implementación del algoritmo de **Difusión Causal de Birman** usando simulación de eventos discretos. Cada nodo mantiene un reloj vectorial y una cola de mensajes pendientes. Antes de entregar un mensaje a la aplicación, verifica que se respete el orden causal: no se libera ningún mensaje hasta que todos los mensajes que causalmente lo preceden hayan sido entregados primero.

---

## Variables de inicialización (`init`)

Estas variables se crean en el método `init` y representan el estado interno de **cada nodo** durante la simulación.

| Variable | Tipo | Valor inicial | Descripción |
|---|---|---|---|
| `self.total_nodos` | `int` | `len(self.neighbors) + 1` | Número total de nodos en la red. Se calcula sumando los vecinos del nodo más él mismo. |
| `self.reloj_vectorial` | `list[int]` | `[0, 0, ..., 0]` | Reloj vectorial del nodo. Tiene una entrada por cada nodo en la red. Cada posición `i` representa cuántos mensajes del nodo `i+1` han sido enviados (en el caso del nodo propio) o vistos causalmente (en el caso de los demás). |
| `self.cola_retraso` | `list[Event]` | `[]` | Cola de mensajes recibidos que aún no pueden ser entregados por no satisfacer el orden causal. Los mensajes esperan aquí hasta que sus predecesores causales sean liberados. |
| `self.id_mensaje_siguiente` | `int` | `0` | Contador local que asigna un identificador único a cada mensaje que este nodo difunde. Se incrementa cada vez que el nodo envía un nuevo mensaje. |

---

## Funciones de la clase `AlgoritmoDCB`

---

### `init(self)`
**Línea:** 8

Inicializa el estado interno del nodo antes de que comience la simulación. Es llamado automáticamente por el framework al configurar cada nodo.

- Calcula el total de nodos en la red.
- Inicializa el reloj vectorial con ceros.
- Prepara la cola de mensajes pendientes vacía.
- Pone el contador de mensajes en cero.

---

### `receive(self, event)`
**Línea:** 14

Manejador central de eventos. Es el punto de entrada que el simulador llama cada vez que un evento llega al nodo. Contiene toda la lógica de comportamiento del nodo directamente (sin delegar a funciones auxiliares de envío o recepción), y despacha según el tipo de evento:

| Tipo de evento | Acción |
|---|---|
| `"INICIA"` | Imprime el estado inicial del nodo. Con probabilidad `1/n`, programa un primer envío con retardo aleatorio en `[1, 4n]`. |
| `"ENVIA"` | Ejecuta directamente la difusión: incrementa el VC propio, crea un evento `"MENSAJE"` por cada vecino con retardo individual aleatorio en `[1, 3n]`, y los transmite. Con probabilidad `1/2n`, programa otro envío posterior con retardo en `[1, 4n]`. |
| `"MENSAJE"` | Procesa directamente la llegada: extrae el vector y el origen, imprime la traza de recepción, agrega el mensaje a `cola_retraso` y llama a `entregar_mensajes_listos()`. |

> El retardo `[1, 4n]` para eventos propios y `[1, 3n]` para mensajes entre vecinos aumentan la varianza en los tiempos de llegada, forzando más situaciones donde los mensajes llegan fuera de orden y quedan bloqueados en la cola causal.

**Detalle del bloque `"ENVIA"`:**

```python
self.reloj_vectorial[self.id - 1] += 1      # incrementa VC propio
self.id_mensaje_siguiente += 1              # asigna ID al mensaje
vector_mensaje = self.reloj_vectorial.copy()# sello temporal del mensaje

for vecino in self.neighbors:
    retraso = random.randint(1, self.total_nodos * 3)  # retardo por canal
    nuevo_evento = Event("MENSAJE", self.clock + retraso, vecino, self.id)
    nuevo_evento.vector = vector_mensaje.copy()
    nuevo_evento.message_id = self.id_mensaje_siguiente
    self.transmit(nuevo_evento)
```

---

### `entregar_mensajes_listos(self)`
**Línea:** 49

Recorre repetidamente la cola de mensajes pendientes e intenta liberar todos los que ya satisfacen el orden causal.

- Usa un bucle `while` que se repite mientras pueda liberar al menos un mensaje por iteración.
- En cada pasada, itera sobre la cola y llama a `es_entregable()` para cada mensaje.
- Si un mensaje es entregable:
  - Lo elimina de la cola.
  - Lo entrega con `entregar_mensaje()`.
  - Con probabilidad `1/2n`, programa un nuevo envío propio con retardo en `[1, 4n]`.
  - Reinicia el bucle (`break`) para volver a revisar desde el principio, ya que la entrega pudo haber habilitado más mensajes.

---

### `entregar_mensaje(self, event)`
**Línea:** 65

Realiza la entrega formal de un mensaje a la aplicación hipotética y actualiza el reloj vectorial del nodo.

1. Extrae el vector del mensaje y el identificador del emisor.
2. **No incrementa** `self.reloj_vectorial[self.id - 1]`: según el modelo del curso, entregar un mensaje a la aplicación no genera un nuevo evento en el nodo receptor.
3. Actualiza el reloj vectorial tomando el **máximo componente a componente** entre el VC propio y el del mensaje recibido:
   ```
   VC[i] = max(VC[i], Vm[i])  para todo i
   ```
4. Imprime una **traza de liberación**: `[t=...] Nodo X libera mY de Z y actualiza VC=[...]` mostrando el VC propio ya actualizado.

---

### `es_entregable(self, event)`
**Línea:** 79

Verifica si un mensaje satisface las condiciones del **orden causal de Birman** para poder ser entregado. Retorna `True` si el mensaje puede liberarse, `False` en caso contrario.

**Condición 1 — Orden del emisor:**
```
Vm[k] == VC[k] + 1
```
Donde `k` es el índice del nodo emisor. Garantiza que el mensaje es el siguiente esperado del emisor (no hay saltos ni duplicados).

**Condición 2 — Causalidad con otros nodos:**
```
Vm[j] <= VC[j]  para todo j distinto de k
```
Garantiza que todos los mensajes de otros nodos que el emisor ya conocía cuando envió este mensaje, ya fueron entregados en el receptor.

Si alguna condición falla, imprime una traza explicando el motivo del bloqueo y retorna `False`.

---

### `vector_a_texto(self, vector=None)`
**Línea:** 96

Convierte un reloj vectorial (lista de enteros) a su representación como cadena de texto legible.

- Si no se pasa ningún `vector`, usa `self.reloj_vectorial` por defecto.
- Devuelve una cadena con formato `[v1, v2, ..., vn]`.

**Uso típico en trazas:**
```python
self.vector_a_texto()           # Ejemplo: "[1, 0, 2]"  (VC propio)
self.vector_a_texto(otro_vec)   # Ejemplo: "[0, 3, 1]"  (vector arbitrario)
```

---

## Bloque principal (`main`)

**Líneas:** 102–119

Código de ejecución que se corre al lanzar el script directamente.

1. Valida que se proporcione exactamente un argumento (nombre del archivo de grafo).
2. Crea la simulación con duración máxima de `500` unidades de tiempo.
3. Instancia un `AlgoritmoDCB` por cada nodo del grafo y lo registra en la simulación.
4. Inyecta un evento `"INICIA"` a cada nodo en tiempo `0.0` para arrancar el algoritmo.
5. Ejecuta la simulación con `experiment.run()`.

**Ejemplo de uso:**
```bash
python DifusiónCausalBirdman.py g7.txt
```

---

## Flujo general del algoritmo

```
INICIA
  └─→ (prob 1/n) → programa ENVIA con retardo [1, 4n]

ENVIA  [lógica inlining en receive()]
  ├─ incrementa VC propio
  ├─ envía MENSAJE a CADA vecino con retardo individual [1, 3n]
  └─→ (prob 1/2n) → programa otro ENVIA con retardo [1, 4n]

MENSAJE (llega al receptor)  [lógica inlining en receive()]
  ├─ imprime traza de RECEPCIÓN
  ├─ agrega a cola_retraso
  └─→ entregar_mensajes_listos()
        └─ para cada pendiente en cola:
              ├─ es_entregable()?
              │     ├─ Cond 1: Vm[k] == VC[k] + 1
              │     └─ Cond 2: Vm[j] <= VC[j] para todo j distinto de k
              └─ Si True:
                    ├─ entregar_mensaje() → actualiza VC (max componente a componente)
                    ├─ imprime traza de LIBERACIÓN
                    └─ (prob 1/2n) → programa ENVIA
```

---

## Funciones eliminadas en la versión actual

Estas funciones existían en versiones anteriores del código y fueron **refactorizadas como lógica inlining** dentro de `receive()` para simplificar la estructura:

| Función | Motivo de eliminación |
|---|---|
| `recibir_mensaje(self, event)` | Su lógica fue movida directamente al bloque `elif event.getName() == "MENSAJE"` de `receive()`. |
| `difundir_mensaje(self)` | Su lógica fue movida directamente al bloque `elif event.getName() == "ENVIA"` de `receive()`. |
| `debe_enviar_inicialmente(self)` | Era una función auxiliar de probabilidad; la lógica equivalente está aplicada directamente en el bloque `"INICIA"` de `receive()`. |
