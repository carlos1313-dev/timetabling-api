"""
Hidratación en memoria de un dataset sintético (dict) hacia las entidades de
dominio. Es la misma lógica de FacultadJSONRepository.cargar_datos_completos,
pero recibe el dict directamente en vez de leerlo desde un archivo — así el
benchmark no tiene que escribir/leer un JSON de miles de estudiantes en cada
una de las iteraciones.
"""

from typing import Any, Dict, List, Tuple

from core.entities import Materia, Profesor, Grupo, HistorialReprobacion


def hidratar_desde_dict(datos_crudos: Dict[str, Any]) -> Tuple[List[Profesor], List[Grupo], List[HistorialReprobacion]]:
    diccionario_materias: Dict[str, Materia] = {
        m['id']: Materia(
            id_materia=m['id'],
            nombre=m['nombre'],
            nivel=m['nivel'],
            creditos=m.get('creditos', 3),
            sesiones_semanales=m.get('sesiones_semanales', 2),
            area_conocimiento=m.get('area_conocimiento', 'General')
        )
        for m in datos_crudos.get('materias', [])
    }

    profesores = [
        Profesor(
            id_profesor=p['id'],
            nombre=p['nombre'],
            tipo_contrato=p.get('tipo_contrato', 'Ocasional'),
            max_creditos_docencia=p.get('max_creditos_docencia', 8),
            areas_habilitadas=p.get('areas_habilitadas', ['General'])
        )
        for p in datos_crudos.get('profesores', [])
    ]

    historial = [
        HistorialReprobacion(
            id_estudiante=h['id_estudiante'],
            id_materia=h['id_materia'],
            id_profesor_vetado=h['id_profesor_vetado']
        )
        for h in datos_crudos.get('historial_reprobacion', [])
    ]

    grupos = []
    for g_data in datos_crudos.get('grupos_abiertos', []):
        id_mat = g_data['id_materia']
        if id_mat not in diccionario_materias:
            raise ValueError(f"Inconsistencia de datos: La materia {id_mat} no existe en el catálogo.")

        grupos.append(Grupo(
            id_grupo=g_data['id_grupo'],
            materia=diccionario_materias[id_mat],
            cupo=g_data['cupo'],
            sede=g_data.get('sede', 'Sede Principal'),
            estudiantes_inscritos=set(g_data.get('estudiantes_inscritos', []))
        ))

    return profesores, grupos, historial
