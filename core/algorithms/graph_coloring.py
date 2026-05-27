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

    def coloreo_voraz(self, orden_vertices: List[int] = None) -> Tuple[List[int], int]:
        if orden_vertices is None:
            orden_vertices = list(range(self.n))

        colores = [-1] * self.n

        for vertice in orden_vertices:
            colores_usados_vecinos: Set[int] = set()

            for vecino in self.adj[vertice]:
                if colores[vecino] != -1:
                    colores_usados_vecinos.add(colores[vecino])

            color = 0
            while color in colores_usados_vecinos:
                color += 1

            colores[vertice] = color

        return colores, self.numero_colores_usados(colores)

    def coloreo_welsh_powell(self) -> Tuple[List[int], int]:
        grados = self.grados_vertices()
        
        # Ordenar vértices de mayor a menor grado
        orden_vertices = sorted(
            range(self.n),
            key=lambda v: grados[v],
            reverse=True
        )

        return self.coloreo_voraz(orden_vertices)

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