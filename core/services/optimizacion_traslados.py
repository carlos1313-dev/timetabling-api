"""
Módulo de Optimización de Restricciones Blandas (Soft Constraints).

Responsabilidad: una vez que el Coloreo de Grafos (DSatur / Welsh-Powell / Voraz)
entrega una asignación de franjas horarias que respeta TODAS las restricciones
duras (idoneidad docente, vetos, mismo semestre, estudiantes compartidos, límite
físico de 36 franjas), este módulo REFINA esa asignación para reducir una
restricción blanda adicional: los traslados entre sedes en clases consecutivas
de un mismo estudiante.

Principio de diseño (coherente con el resto del sistema):
- Nunca aumenta el número de franjas ya usadas (no "inventa" horario nuevo).
- Nunca introduce una adyacencia inválida: cada intercambio de color se valida
  contra el mismo grafo de conflictos ya construido por GeneradorHorariosService.
- Sigue el mismo espíritu Fail-Safe del resto del proyecto: si no encuentra
  ninguna mejora, simplemente conserva el coloreo original sin lanzar error.

Este módulo NO es un algoritmo de coloreo nuevo. Opera DESPUÉS de
RepresentacionGrafo.coloreo_dsatur() / coloreo_welsh_powell() / coloreo_voraz(),
sobre su salida.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Set
import random

from core.entities import SesionGrupo
from core.algorithms.graph_coloring import RepresentacionGrafo


# Mismo supuesto usado en GeneradorHorariosService: Lunes a Sábado, 6 franjas/día.
FRANJAS_POR_DIA = 6


@dataclass
class ResultadoOptimizacion:
    """Resultado del proceso de refinamiento, con trazabilidad para el reporte."""
    colores: List[int]
    penalizacion_inicial: int
    penalizacion_final: int
    intercambios_aplicados: int


class OptimizadorTrasladosService:
    """
    Caso de uso: refinamiento local tipo hill-climbing sobre un coloreo ya
    válido, para minimizar los traslados entre sedes en sesiones consecutivas
    de un mismo estudiante.

    Uso típico:
        optimizador = OptimizadorTrasladosService(sesiones, grafo, sede_por_sesion)
        resultado = optimizador.ejecutar(colores_iniciales)
    """

    def __init__(
        self,
        sesiones: List[SesionGrupo],
        grafo: RepresentacionGrafo,
        sede_por_sesion: List[str],
    ):
        if len(sesiones) != grafo.n or len(sede_por_sesion) != grafo.n:
            raise ValueError(
                "sesiones, grafo y sede_por_sesion deben tener la misma longitud "
                "(un valor por nodo del grafo de conflictos)."
            )
        self.sesiones = sesiones
        self.grafo = grafo
        self.sede_por_sesion = sede_por_sesion
        self._sesiones_por_estudiante = self._indexar_sesiones_por_estudiante()

    # ------------------------------------------------------------------
    # Indexación auxiliar
    # ------------------------------------------------------------------
    def _indexar_sesiones_por_estudiante(self) -> Dict[str, List[int]]:
        """
        Para cada estudiante, la lista de índices de nodo (sesiones) en las
        que está matriculado, según el grupo padre de cada sesión.
        """
        indice: Dict[str, List[int]] = {}
        for idx, sesion in enumerate(self.sesiones):
            for id_estudiante in sesion.grupo_padre.estudiantes_inscritos:
                indice.setdefault(id_estudiante, []).append(idx)
        return indice

    # ------------------------------------------------------------------
    # Función objetivo (la restricción blanda como número medible)
    # ------------------------------------------------------------------
    def calcular_penalizacion(self, colores: List[int]) -> int:
        """
        Cuenta, sumando sobre todos los estudiantes, cuántos pares de sesiones
        consecutivas (mismo día, franja contigua) implican un cambio de sede.
        Este es el número que va directo a tu métrica de "restricciones
        violadas" para el artículo.
        """
        penalizacion = 0
        for indices_sesiones in self._sesiones_por_estudiante.values():
            eventos = []
            for idx in indices_sesiones:
                color = colores[idx]
                if color < 0:
                    continue  # sesión sin franja (cayó en Alerta de Decanatura)
                dia, franja = divmod(color, FRANJAS_POR_DIA)
                eventos.append((dia, franja, self.sede_por_sesion[idx]))

            eventos.sort()
            for (dia_a, franja_a, sede_a), (dia_b, franja_b, sede_b) in zip(eventos, eventos[1:]):
                if dia_a == dia_b and franja_b == franja_a + 1 and sede_a != sede_b:
                    penalizacion += 1
        return penalizacion

    # ------------------------------------------------------------------
    # Búsqueda de colores intercambiables válidos (respeta restricciones duras)
    # ------------------------------------------------------------------
    def _colores_prohibidos(self, nodo: int, colores: List[int]) -> Set[int]:
        prohibidos = set()
        for vecino in self.grafo.adj[nodo]:
            if colores[vecino] != -1:
                prohibidos.add(colores[vecino])
        return prohibidos

    def _candidatos_validos(self, nodo: int, colores: List[int], num_colores: int) -> List[int]:
        """
        Colores YA EXISTENTES en el horario (no crea franjas nuevas) que
        siguen siendo válidos para este nodo: ningún vecino en el grafo de
        conflictos los está usando actualmente.
        """
        prohibidos = self._colores_prohibidos(nodo, colores)
        return [c for c in range(num_colores) if c not in prohibidos and c != colores[nodo]]

    # ------------------------------------------------------------------
    # Refinamiento (hill-climbing)
    # ------------------------------------------------------------------
    def ejecutar(
        self,
        colores_iniciales: List[int],
        max_iteraciones: int = 3000,
        semilla: int = 42,
    ) -> ResultadoOptimizacion:
        """
        Intenta, iterativamente, reasignar sesiones a colores alternativos
        (ya existentes en el horario) que reduzcan la penalización total.
        Cada intento se revierte si no mejora, así que el resultado NUNCA es
        peor que el coloreo de entrada.
        """
        rng = random.Random(semilla)
        colores = colores_iniciales[:]
        num_colores = max(colores) + 1 if colores else 0

        penalizacion_actual = self.calcular_penalizacion(colores)
        penalizacion_inicial = penalizacion_actual
        intercambios_aplicados = 0

        # No tocamos sesiones que quedaron sin franja (Alerta de Decanatura: color == -1)
        nodos_afectables = [idx for idx in range(self.grafo.n) if colores[idx] != -1]

        for _ in range(max_iteraciones):
            if not nodos_afectables or penalizacion_actual == 0:
                break

            nodo = rng.choice(nodos_afectables)
            candidatos = self._candidatos_validos(nodo, colores, num_colores)
            if not candidatos:
                continue

            rng.shuffle(candidatos)
            color_original = colores[nodo]

            for color_candidato in candidatos:
                colores[nodo] = color_candidato
                nueva_penalizacion = self.calcular_penalizacion(colores)

                if nueva_penalizacion < penalizacion_actual:
                    penalizacion_actual = nueva_penalizacion
                    intercambios_aplicados += 1
                    break
                colores[nodo] = color_original  # no mejoró: revertir

        return ResultadoOptimizacion(
            colores=colores,
            penalizacion_inicial=penalizacion_inicial,
            penalizacion_final=penalizacion_actual,
            intercambios_aplicados=intercambios_aplicados,
        )