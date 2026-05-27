from typing import List, Tuple, Set

class RepresentacionGrafo:
    """
    Módulo puro de teoría de grafos.
    Responsabilidad: Construcción estructural y ejecución de algoritmos de coloreo.
    Cero acoplamiento con reglas de negocio (Salones, Profesores, etc).
    """
    
    def __init__(self, num_vertices: int, aristas: List[Tuple[int, int, int]]):
        self.n = num_vertices
        self.aristas = aristas
        self.m = len(aristas)
        # Pre-calculamos la lista de adyacencia al instanciar para optimizar llamadas futuras
        self.adj = self._construir_lista_adyacencia()

    def _construir_lista_adyacencia(self) -> List[List[int]]:
        lista = [[] for _ in range(self.n)]
        for u, v, _ in self.aristas:
            lista[u].append(v)
            lista[v].append(u)
        return lista

    def grados_vertices(self) -> List[int]:
        return [len(vecinos) for vecinos in self.adj]

    def es_coloreo_valido(self, colores: List[int]) -> bool:
        for u, v, _ in self.aristas:
            # Si un vértice no ha sido coloreado (-1), ignoramos el chequeo temporalmente
            if colores[u] != -1 and colores[v] != -1:
                if colores[u] == colores[v]:
                    return False
        return True

    def numero_colores_usados(self, colores: List[int]) -> int:
        # Filtramos los -1 (no coloreados) antes de contar
        return len(set(c for c in colores if c != -1))

    # ---------------------------------------------------------
    # Algoritmos de Coloreo
    # ---------------------------------------------------------

    def coloreo_voraz(self) -> Tuple[List[int], int]:
        """
        Asigna colores de forma secuencial y voraz (Greedy puro).
        A cada vértice se le asigna el primer color disponible (el más bajo)
        que no esté siendo usado por ninguno de sus vecinos adyacentes.
        """
        colores = [-1] * self.n

        for v in range(self.n):
            # 1. Identificar qué colores ya tienen los vecinos de este vértice
            colores_vecinos = set()
            for vecino in self.adj[v]:
                if colores[vecino] != -1:
                    colores_vecinos.add(colores[vecino])
            
            # 2. Buscar el color más bajo que no esté en la lista de los vecinos
            color_elegido = 0
            while color_elegido in colores_vecinos:
                color_elegido += 1
                
            # 3. Asignar el color
            colores[v] = color_elegido

        # El total de franjas es el color más alto asignado + 1 (porque empezamos en 0)
        num_colores = max(colores) + 1 if self.n > 0 else 0
        return colores, num_colores

    def coloreo_welsh_powell(self) -> Tuple[List[int], int]:
        """
        Asigna colores a los vértices usando el algoritmo estático Welsh-Powell.
        1. Ordena los vértices por grado de forma descendente.
        2. Asigna colores iterativamente a los vértices no adyacentes.
        """
        colores = [-1] * self.n
        
        # Calcular el grado de cada vértice (cuántas aristas tiene)
        grados = [len(self.adj[i]) for i in range(self.n)]
        
        # Ordenar los vértices de mayor a menor grado
        vertices_ordenados = sorted(range(self.n), key=lambda x: grados[x], reverse=True)
        
        color_actual = 0
        vertices_coloreados = 0
        
        while vertices_coloreados < self.n:
            # En cada pasada de color, intentamos pintar los que más podamos
            vertices_pintados_en_esta_ronda = []
            
            for v in vertices_ordenados:
                if colores[v] == -1:
                    # Verificar si este vértice choca con alguno que ya pintamos con el color_actual
                    puede_colorearse = True
                    for vecino in self.adj[v]:
                        if vecino in vertices_pintados_en_esta_ronda:
                            puede_colorearse = False
                            break
                    
                    if puede_colorearse:
                        colores[v] = color_actual
                        vertices_pintados_en_esta_ronda.append(v)
                        vertices_coloreados += 1
                        
            color_actual += 1
            
        return colores, color_actual

    def coloreo_dsatur(self) -> Tuple[List[int], int]:
        grados = self.grados_vertices()
        colores = [-1] * self.n
        vertices_no_coloreados = set(range(self.n))

        while vertices_no_coloreados:
            mejor_vertice = -1
            mejor_saturacion = -1
            mejor_grado = -1

            for v in vertices_no_coloreados:
                colores_vecinos = set()
                for vecino in self.adj[v]:
                    if colores[vecino] != -1:
                        colores_vecinos.add(colores[vecino])

                saturacion = len(colores_vecinos)

                if (saturacion > mejor_saturacion or
                    (saturacion == mejor_saturacion and grados[v] > mejor_grado) or
                    (saturacion == mejor_saturacion and grados[v] == mejor_grado and 
                     (mejor_vertice == -1 or v < mejor_vertice))):
                    
                    mejor_vertice = v
                    mejor_saturacion = saturacion
                    mejor_grado = grados[v]

            colores_prohibidos = set()
            for vecino in self.adj[mejor_vertice]:
                if colores[vecino] != -1:
                    colores_prohibidos.add(colores[vecino])

            color = 0
            while color in colores_prohibidos:
                color += 1

            colores[mejor_vertice] = color
            vertices_no_coloreados.remove(mejor_vertice)

        return colores, self.numero_colores_usados(colores)