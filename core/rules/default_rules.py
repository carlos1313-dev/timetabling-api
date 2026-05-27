from core.rules.base_rule import ReglaConflictoStrategy
from core.entities import SesionGrupo

class ReglaSesionesMismoGrupo(ReglaConflictoStrategy):
    """
    Si son la Sesión 1 y la Sesión 2 del mismo grupo de Ecuaciones Diferenciales,
    DEBEN tener una arista de conflicto para que ocurran en días distintos.
    """
    def existe_conflicto(self, sesion_a: SesionGrupo, sesion_b: SesionGrupo) -> bool:
        return sesion_a.grupo_padre.id_grupo == sesion_b.grupo_padre.id_grupo

class ReglaMismoProfesor(ReglaConflictoStrategy):
    def existe_conflicto(self, sesion_a: SesionGrupo, sesion_b: SesionGrupo) -> bool:
        prof_a = sesion_a.grupo_padre.profesor_asignado
        prof_b = sesion_b.grupo_padre.profesor_asignado
        if not prof_a or not prof_b:
            return False
        return prof_a.id_profesor == prof_b.id_profesor

class ReglaMismoSemestre(ReglaConflictoStrategy):
    def existe_conflicto(self, sesion_a: SesionGrupo, sesion_b: SesionGrupo) -> bool:
        return sesion_a.grupo_padre.materia.nivel == sesion_b.grupo_padre.materia.nivel

class ReglaEstudiantesCompartidos(ReglaConflictoStrategy):
    def existe_conflicto(self, sesion_a: SesionGrupo, sesion_b: SesionGrupo) -> bool:
        return bool(
            sesion_a.grupo_padre.estudiantes_inscritos.intersection(
                sesion_b.grupo_padre.estudiantes_inscritos
            )
        )