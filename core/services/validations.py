from typing import List, Dict
from core.entities import Grupo

class ValidadorInscripcionesService:
    """
    Valida las reglas de negocio de la Universidad referentes a la matrícula
    antes de ejecutar los algoritmos de optimización.
    """
    def __init__(self, limite_creditos: int = 18):
        self.limite_creditos = limite_creditos

    def validar_limite_creditos(self, grupos: List[Grupo]) -> None:
        """
        Suma los créditos de todas las materias inscritas por cada estudiante.
        Lanza un ValueError si alguien supera el límite.
        """
        creditos_por_estudiante: Dict[str, int] = {}
        
        for grupo in grupos:
            # Los créditos provienen de la materia asociada al grupo
            creditos_materia = grupo.materia.creditos
            
            for id_estudiante in grupo.estudiantes_inscritos:
                # Inicializar el contador si es la primera materia del estudiante
                if id_estudiante not in creditos_por_estudiante:
                    creditos_por_estudiante[id_estudiante] = 0
                
                # Sumar los créditos
                creditos_por_estudiante[id_estudiante] += creditos_materia

        # Filtrar a los infractores
        estudiantes_excedidos = [
            f"{est_id} ({total} créditos)" 
            for est_id, total in creditos_por_estudiante.items() 
            if total > self.limite_creditos
        ]
        
        if estudiantes_excedidos:
            mensaje = "Inscripción bloqueada. Los siguientes estudiantes superan el límite de {} créditos: {}".format(
                self.limite_creditos, ", ".join(estudiantes_excedidos)
            )
            raise ValueError(mensaje)