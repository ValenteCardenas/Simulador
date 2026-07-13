import random
import sys

def genera_topologia(n=50, min_grado=4, max_grado=7, semilla=42):
    """
    Genera una topología P2P no estructurada con n nodos donde cada nodo
    tiene un grado en [min_grado, max_grado].
    
    Estrategia:
    1. Anillo + saltos de 2: garantiza grado 4 y conectividad
    2. Aristas aleatorias adicionales: variedad en grados (5, 6 o 7)
    """
    random.seed(semilla)
    
    # Listas de adyacencia (1-indexado)
    adj = {i: set() for i in range(1, n + 1)}
    
    def agregar_arista(u, v):
        """Agrega arista u-v si es válida (sin loops, sin duplicados, sin exceder grado máximo)"""
        if u != v and v not in adj[u] and len(adj[u]) < max_grado and len(adj[v]) < max_grado:
            adj[u].add(v)
            adj[v].add(u)
            return True
        return False
    
    # Paso 1: Anillo (grado 2)
    # Nodo i se conecta con nodo i+1 (mod n)
    for i in range(1, n + 1):
        j = (i % n) + 1
        agregar_arista(i, j)
    
    # Paso 2: Saltos de 2 (grado 4)
    # Nodo i se conecta con nodo i+2 (mod n)
    for i in range(1, n + 1):
        j = ((i + 1) % n) + 1
        agregar_arista(i, j)
    
    # Paso 3: Aristas aleatorias adicionales para variedad
    # Agrega aristas extra para que algunos nodos tengan grado 5, 6 o 7
    nodos = list(range(1, n + 1))
    aristas_extra = n // 2  # Aproximadamente n/2 aristas adicionales
    intentos = 0
    agregadas = 0
    
    while agregadas < aristas_extra and intentos < n * 50:
        u = random.choice(nodos)
        v = random.choice(nodos)
        if agregar_arista(u, v):
            agregadas += 1
        intentos += 1
    
    return adj


def verificar_conectividad(adj):
    """Verifica que el grafo sea conexo usando BFS"""
    n = len(adj)
    visitados = set()
    cola = [1]
    while cola:
        v = cola.pop(0)
        if v not in visitados:
            visitados.add(v)
            for u in adj[v]:
                if u not in visitados:
                    cola.append(u)
    return len(visitados) == n


def escribir_topologia(adj, archivo):
    """Escribe la topología en formato compatible con el simulador.
    Cada línea i contiene los vecinos del nodo i+1, separados por espacios."""
    n = len(adj)
    with open(archivo, 'w') as f:
        for i in range(1, n + 1):
            vecinos = sorted(adj[i])
            linea = ' '.join(map(str, vecinos))
            f.write(linea)
            if i < n:
                f.write('\n')


def imprimir_estadisticas(adj):
    """Imprime estadísticas del grafo generado"""
    n = len(adj)
    grados = [len(adj[i]) for i in range(1, n + 1)]
    
    print(f"=== Topología P2P Generada ===")
    print(f"Nodos: {n}")
    print(f"Aristas: {sum(grados) // 2}")
    print(f"Grado mínimo: {min(grados)}")
    print(f"Grado máximo: {max(grados)}")
    print(f"Grado promedio: {sum(grados) / len(grados):.2f}")
    print(f"Conectada: {'Sí' if verificar_conectividad(adj) else 'No'}")
    
    # Distribución de grados
    from collections import Counter
    dist = Counter(grados)
    print(f"\nDistribución de grados:")
    for grado in sorted(dist.keys()):
        print(f"  Grado {grado}: {dist[grado]} nodos")
    
    # Ejemplo: mostrar detalle del nodo 1
    print(f"\n=== Detalle del Nodo 1 ===")
    print(f"  Vecinos: {sorted(adj[1])}")
    print(f"  Grado: {len(adj[1])}")


## main

if __name__ == '__main__':
    # Parámetros configurables
    n = 200
    min_grado = 4
    max_grado = 7
    semilla = 42
    archivo_salida = 'g_p2p_50.txt'
    
    # Permitir especificar el número de nodos por argumento
    if len(sys.argv) >= 2:
        n = int(sys.argv[1])
        archivo_salida = f'g_p2p_{n}.txt'
    
    # Generar topología
    adj = genera_topologia(n, min_grado, max_grado, semilla)
    
    # Imprimir estadísticas
    imprimir_estadisticas(adj)
    
    # Verificar grados válidos
    errores = False
    for i in range(1, n + 1):
        grado = len(adj[i])
        if grado < min_grado or grado > max_grado:
            print(f"ERROR: Nodo {i} tiene grado {grado} (fuera de [{min_grado},{max_grado}])")
            errores = True
    
    if not errores:
        print(f"\n[OK] Todos los nodos tienen grado en [{min_grado},{max_grado}]")
    
    # Escribir archivo
    escribir_topologia(adj, archivo_salida)
    print(f"\nTopología guardada en: {archivo_salida}")
