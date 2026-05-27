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

        # 2. Validar Restricción de Repitentes (Vetos) de forma SEGURA
        # Obtenemos los vetos de la materia, si no hay, devolvemos un dict vacío {}
        vetos_materia = self.vetos_por_materia_profe.get(grupo.materia.id_materia, {})
        
        # Obtenemos los estudiantes que vetaron a este profe, si no hay, devolvemos un set vacío set()
        estudiantes_que_vetan = vetos_materia.get(profesor.id_profesor, set())
        
        # Intersección matemática O(1)
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
        
        # 1. Construir la Lista de Adyacencia del Grafo Bipartito (CON SLOTS)
        grafo_bipartito = defaultdict(list)
        
        # Diccionario para saber qué profesor original es cada slot
        mapa_slots_a_profesor: Dict[str, Profesor] = {}
        
        for profe in self.profesores:
            # ¿Cuántos cursos puede dictar este profe? 
            # (Asumamos un cálculo simple: max_creditos / 3 como ejemplo, 
            #  o podrías agregar una propiedad 'max_grupos' a la entidad Profesor)
            # Para este ejemplo, digamos que todos pueden dictar hasta 3 grupos.
            max_grupos_profe = 3 
            
            for i in range(max_grupos_profe):
                id_slot = f"{profe.id_profesor}_slot_{i}"
                mapa_slots_a_profesor[id_slot] = profe
                
                for grupo in grupos:
                    if self._profesor_es_valido(profe, grupo):
                        # Conectamos el SLOT al grupo, no al profesor directamente
                        grafo_bipartito[id_slot].append(grupo.id_grupo)

        # 2. Ejecutar Algoritmo de Emparejamiento Máximo Bipartito
        asignaciones_optimas: Dict[str, str] = {} # Mapea id_grupo -> id_slot
        
        for id_slot in mapa_slots_a_profesor.keys():
            visitados = set()
            self._dfs_matching(id_slot, grafo_bipartito, visitados, asignaciones_optimas)

        # 3. Aplicar resultados a las entidades y manejar excepciones
        for grupo in grupos:
            if grupo.id_grupo in asignaciones_optimas:
                # El algoritmo logró emparejarlo con un slot
                id_slot_asignado = asignaciones_optimas[grupo.id_grupo]
                profesor_real = mapa_slots_a_profesor[id_slot_asignado]
                grupo.asignar_profesor(profesor_real)
            else:
                if not self.profesores:
                    raise RuntimeError("Falla crítica: La facultad no tiene profesores.")
                
                # 1. Buscar profesores que al menos sepan dictar el área (ignorar vetos)
                profesores_idoneos = [
                    p for p in self.profesores 
                    if grupo.materia.area_conocimiento in p.areas_habilitadas
                ]
                
                # 2. Asignar rescate de forma más inteligente
                if profesores_idoneos:
                    profesor_rescate = profesores_idoneos[0]
                    motivo_alerta = "Rompimiento de restricción por repitentes."
                else:
                    # Peor escenario: Nadie sabe dictar esto en toda la facultad
                    profesor_rescate = self.profesores[0]
                    motivo_alerta = "Rompimiento CRÍTICO: Docente sin área habilitada y restricción de repitentes."

                grupo.asignar_profesor(profesor_rescate)
                
                alerta = (
                    f"⚠️ ALERTA ACADÉMICA - Grupo {grupo.id_grupo} ({grupo.materia.nombre}): "
                    f"Asignado al docente {profesor_rescate.nombre} por falta de personal. "
                    f"{motivo_alerta}"
                )
                alertas_academicas.append(alerta)
                logger.warning(alerta)
        return grupos, alertas_academicas