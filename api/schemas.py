from pydantic import BaseModel
from typing import List

class AsignacionResponse(BaseModel):
    id_nodo: str             # Para identificar la sesión específica
    id_grupo: str
    materia: str
    id_materia: str
    nivel_materia: int
    numero_sesion: int       # ¿Es la clase 1, 2 o 3 de la semana?
    profesor: str
    color_franja_horaria: int
    cantidad_inscritos: int
    estudiantes_inscritos: List[str]

class HorarioResponse(BaseModel):
    estado: str
    total_franjas_requeridas: int
    alertas: List[str]
    estudiantes_sin_carga: List[str]
    asignaciones: List[AsignacionResponse]