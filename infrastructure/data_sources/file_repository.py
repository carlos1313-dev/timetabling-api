import json
from typing import List, Tuple, Dict
import logging

from core.entities import Materia, Profesor, Estudiante, Grupo, HistorialReprobacion

logger = logging.getLogger(__name__)

class FacultadJSONRepository:
    """
    Patrón Repository: Abstrae el origen de los datos. 
    Si mañana la facultad cambia este JSON por una base de datos SQL, 
    solo modificamos esta clase, el resto de la arquitectura queda intacta.
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path

    def cargar_datos_completos(self) -> Tuple[List[Profesor], List[Grupo], List[HistorialReprobacion]]:
        """
        Lee el archivo JSON, instancia las entidades del dominio y resuelve 
        las relaciones (hidratación de objetos).
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                datos_crudos = json.load(file)
        except FileNotFoundError:
            logger.error(f"El archivo de datos no fue encontrado en la ruta: {self.file_path}")
            raise RuntimeError("Fallo en infraestructura: Base de datos no disponible.")
        except json.JSONDecodeError:
            logger.error(f"El archivo {self.file_path} está corrupto o no es un JSON válido.")
            raise RuntimeError("Fallo en infraestructura: Error de lectura de datos.")

        # 1. Hidratar Catálogos Base
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

        # 2. Hidratar Agregados (Grupos) resolviendo la relación con Materia
        grupos = []
        for g_data in datos_crudos.get('grupos_abiertos', []):
            id_mat = g_data['id_materia']
            if id_mat not in diccionario_materias:
                raise ValueError(f"Inconsistencia de datos: La materia {id_mat} no existe en el catálogo.")
            
            nuevo_grupo = Grupo(
    id_grupo=g_data['id_grupo'],
    materia=diccionario_materias[id_mat],
    cupo=g_data['cupo'],
    sede=g_data.get('sede', 'Sede Principal'),
    estudiantes_inscritos=set(g_data.get('estudiantes_inscritos', []))
)
            grupos.append(nuevo_grupo)

        return profesores, grupos, historial