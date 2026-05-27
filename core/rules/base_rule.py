from abc import ABC, abstractmethod
from core.entities import SesionGrupo 

class ReglaConflictoStrategy(ABC):
    """
    Interfaz abstracta (Contrato) para definir estrategias de conflicto 
    entre grupos académicos.
    
    Cualquier nueva regla de la facultad (ej. choques de laboratorio, 
    preferencias de docentes) debe implementar esta interfaz.
    """
    
class ReglaConflictoStrategy(ABC):
    @abstractmethod
    def existe_conflicto(self, sesion_a: SesionGrupo, sesion_b: SesionGrupo) -> bool:
        pass