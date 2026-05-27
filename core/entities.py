from dataclasses import dataclass, field
from typing import List, Set, Optional


@dataclass(frozen=True)
class Materia:
    """
    Entidad inmutable que representa una asignatura del pensum.
    """
    id_materia: str
    nombre: str
    nivel: int  # Semestre sugerido en la malla curricular
    creditos: int # Para validar límite de 18 y horas por semana
    sesiones_semanales: int  # Cuántos días distintos a la semana debe ir el grupo
    area_conocimiento: str  # A qué departamento pertenece (Ej: Matemáticas)

@dataclass(frozen=True)
class Profesor:
    """
    Entidad inmutable que representa a un docente de la facultad.
    """
    id_profesor: str
    nombre: str
    tipo_contrato: str  #'Planta', 'Ocasional', 'Catedratico'
    max_creditos_docencia: int  # Límite de carga según contrato
    areas_habilitadas: List[str]  # Qué áreas puede dictar este docente


@dataclass(frozen=True)
class Estudiante:
    """
    Entidad inmutable que representa a un estudiante.
    """
    id_estudiante: str
    nombre: str


@dataclass(frozen=True)
class HistorialReprobacion:
    """
    Representa el evento histórico donde un estudiante reprobó
    una materia específica con un profesor específico.
    """
    id_estudiante: str
    id_materia: str
    id_profesor_vetado: str


@dataclass
class Grupo:
    """
    Entidad principal de agregación. Representa la oferta de un curso.
    No es frozen porque su estado muta al asignarle un profesor.
    
    Nota arquitectónica: Vinculamos el objeto Materia completo, no solo su ID,
    para evitar acoplamiento con diccionarios o bases de datos en la lógica de negocio.
    """
    id_grupo: str
    materia: Materia
    cupo: int
    estudiantes_inscritos: Set[str] = field(default_factory=set)
    profesor_asignado: Optional[Profesor] = None

    def asignar_profesor(self, profesor: Profesor) -> None:
        """
        Método de dominio que encapsula el cambio de estado.
        """
        self.profesor_asignado = profesor
        
    def esta_asignado(self) -> bool:
        return self.profesor_asignado is not None

@dataclass
class SesionGrupo:
    """
    Representa una de las múltiples clases que tiene un grupo en la semana.
    Si Ecuaciones (3 créditos) = 3 sesiones de 2 horas. 
    Esta entidad será el VERDADERO NODO en nuestro grafo.
    """
    id_sesion_nodo: str       # Ej: "G01_ECU_Sesion_1"
    grupo_padre: Grupo        # Referencia al grupo original
    numero_sesion: int        # Ej: 1, 2 o 3