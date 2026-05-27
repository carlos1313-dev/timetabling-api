from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
import logging

from core.entities import Profesor, Grupo, HistorialReprobacion

logger = logging.getLogger(__name__)

class AsignadorProfesoresService:
    """
    Caso de Uso: Asignación de docentes utilizando el algoritmo de 
    Emparejamiento Máximo Bipartito (Maximum Bipartite Matching) basado en DFS.
    """
    def __init__(self, profesores: List[Profesor], historial: List[HistorialReprobacion]):
        self.profesores = profesores
        self.vetos_por_materia_profe = self._construir_indice_vetos(historial)

    def _construir_indice_vetos(self, historial: List[HistorialReprobacion]) -> Dict[str, Dict[str, Set[str]]]:
        indice = defaultdict(lambda: defaultdict(set))
        for registro in historial:
            indice[registro.id_materia][registro.id_profesor_vetado].add(registro.id_estudiante)
        return indice

    def _profesor_es_valido(self, profesor: Profesor, grupo: Grupo) -> bool:
        # 1. Validar Idoneidad Docente (Hard Constraint)
        area_materia = grupo.materia.area_conocimiento
        if area_materia not in profesor.areas_habilitadas:
            return False # El profesor no sabe dictar esta área

        # 2. Validar Restricción de Repitentes (Vetos)
        estudiantes_que_vetan = self.vetos_por_materia_profe[grupo.materia.id_materia][profesor.id_profesor]
        hay_conflicto = bool(estudiantes_que_vetan.intersection(grupo.estudiantes_inscritos))
        return not hay_conflicto

    def _dfs_matching(self, u: str, grafo_bipartito: Dict[str, List[str]], 
                      visitados: Set[str], asignaciones: Dict[str, str]) -> bool:
        """
        Algoritmo de búsqueda de camino aumentante usando DFS (Depth-First Search).
        Busca reasignar profesores dinámicamente si hay un conflicto, logrando 
        el emparejamiento óptimo global.
        """
        for v in grafo_bipartito[u]:
            if v not in visitados:
                visitados.add(v)
                
                # Si el grupo 'v' no tiene profesor asignado aún, 
                # o si el profesor que lo tiene asignado puede ser reasignado a otro grupo...
                if v not in asignaciones or self._dfs_matching(asignaciones[v], grafo_bipartito, visitados, asignaciones):
                    asignaciones[v] = u # Se forma la arista en el grafo bipartito
                    return True
        return False

    def ejecutar(self, grupos: List[Grupo]) -> Tuple[List[Grupo], List[str]]:
        alertas_academicas = []
        
        # 1. Construir la Lista de Adyacencia del Grafo Bipartito
        # Nodos U = Profesores, Nodos V = Grupos
        # Una arista existe si el profesor es idóneo y no está vetado.
        grafo_bipartito = defaultdict(list)
        for profe in self.profesores:
            for grupo in grupos:
                if self._profesor_es_valido(profe, grupo):
                    grafo_bipartito[profe.id_profesor].append(grupo.id_grupo)

        # 2. Ejecutar Algoritmo de Emparejamiento Máximo Bipartito
        asignaciones_optimas: Dict[str, str] = {} # Mapea id_grupo -> id_profesor
        
        for profe in self.profesores:
            visitados = set()
            self._dfs_matching(profe.id_profesor, grafo_bipartito, visitados, asignaciones_optimas)

        # 3. Aplicar resultados a las entidades y manejar excepciones (Soft Constraints)
        diccionario_profesores = {p.id_profesor: p for p in self.profesores}
        
        for grupo in grupos:
            if grupo.id_grupo in asignaciones_optimas:
                # El algoritmo logró emparejarlos sin romper reglas
                id_profe_asignado = asignaciones_optimas[grupo.id_grupo]
                grupo.asignar_profesor(diccionario_profesores[id_profe_asignado])
            else:
                # El algoritmo determinó que es matemáticamente imposible emparejar
                # a este grupo sin romper la regla de vetos (Falta de personal).
                if not self.profesores:
                    raise RuntimeError("Falla crítica: La facultad no tiene profesores.")
                
                profesor_rescate = self.profesores[0] 
                grupo.asignar_profesor(profesor_rescate)
                
                alerta = (
                    f"⚠️ ALERTA ACADÉMICA - Grupo {grupo.id_grupo} ({grupo.materia.nombre}): "
                    f"Asignado al docente {profesor_rescate.nombre} por falta de personal. "
                    f"Rompimiento de restricción por repitentes."
                )
                alertas_academicas.append(alerta)
                logger.warning(alerta)
                
        return grupos, alertas_academicas