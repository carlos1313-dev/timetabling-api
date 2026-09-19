"""
Métricas independientes del algoritmo, usadas para comparar el modo
PROPUESTA (con vetos y refinamiento de sede) contra el modo BASELINE
(sin esas restricciones) sobre el mismo resultado ya generado.

A diferencia de OptimizadorTrasladosService, este módulo no participa en
la generación del horario: solo lo audita después de que ya existe.
"""

from typing import List
from collections import defaultdict

from core.entities import Grupo, HistorialReprobacion


def contar_violaciones_veto(grupos_asignados: List[Grupo], historial: List[HistorialReprobacion]) -> int:
    """
    Cuenta cuántos estudiantes terminan viendo una materia con el profesor
    que los reprobó, sin importar si el algoritmo que generó `grupos_asignados`
    consideró o no la restricción de veto al asignar profesores.

    Es la métrica de "restricciones de veto violadas" que se reporta en el
    artículo: en el modo PROPUESTA debería tender a 0 (salvo el caso raro del
    rescate de AsignadorProfesoresService cuando no hay otro profesor idóneo);
    en el modo BASELINE puede ser cualquier número, porque nunca se filtró.
    """
    vetos_por_materia_profe = defaultdict(lambda: defaultdict(set))
    for registro in historial:
        vetos_por_materia_profe[registro.id_materia][registro.id_profesor_vetado].add(registro.id_estudiante)

    violaciones = 0
    for grupo in grupos_asignados:
        if grupo.profesor_asignado is None:
            continue
        vetados = vetos_por_materia_profe.get(grupo.materia.id_materia, {}).get(
            grupo.profesor_asignado.id_profesor, set()
        )
        violaciones += len(vetados.intersection(grupo.estudiantes_inscritos))
    return violaciones
