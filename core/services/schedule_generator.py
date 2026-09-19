from typing import List, Tuple, Dict, Any

from core.entities import Grupo, SesionGrupo
from core.rules.base_rule import ReglaConflictoStrategy
from core.algorithms.graph_coloring import RepresentacionGrafo
from core.services.optimizacion_traslados import OptimizadorTrasladosService

class GeneradorHorariosService:

    def __init__(self, reglas_conflicto: List[ReglaConflictoStrategy]):
        self.reglas_conflicto = reglas_conflicto

    def _expandir_grupos_a_sesiones(self, grupos: List[Grupo]) -> List[SesionGrupo]:
        sesiones_totales = []
        for grupo in grupos:
            # USAMOS sesiones_semanales
            for num_sesion in range(1, grupo.materia.sesiones_semanales + 1):
                nueva_sesion = SesionGrupo(
                    id_sesion_nodo=f"{grupo.id_grupo}_S{num_sesion}",
                    grupo_padre=grupo,
                    numero_sesion=num_sesion
                )
                sesiones_totales.append(nueva_sesion)
        return sesiones_totales
    def _construir_aristas(self, sesiones: List[SesionGrupo]) -> Tuple[List[Tuple[int, int, int]], Dict[int, SesionGrupo]]:
        aristas = []
        mapa_indices = {i: sesion for i, sesion in enumerate(sesiones)}
        num_nodos = len(sesiones)

        for i in range(num_nodos):
            for j in range(i + 1, num_nodos):
                sesion_i = mapa_indices[i]
                sesion_j = mapa_indices[j]

                hay_conflicto = any(
                    regla.existe_conflicto(sesion_i, sesion_j) 
                    for regla in self.reglas_conflicto
                )

                if hay_conflicto:
                    aristas.append((i, j, 1))

        return aristas, mapa_indices

    def ejecutar(self, grupos: List[Grupo], algoritmo: str = "dsatur") -> Dict[str, Any]:
        if any(not g.esta_asignado() for g in grupos):
            raise ValueError("Todos los grupos deben tener un profesor asignado.")

        # 1. Expandimos los nodos antes de construir el grafo
        sesiones = self._expandir_grupos_a_sesiones(grupos)

        # 2. Construcción de aristas sobre las SESIONES, no los grupos
        aristas_grafo, mapa_vertices = self._construir_aristas(sesiones)
        num_vertices = len(sesiones)

        # 3. Módulo Matemático
        grafo = RepresentacionGrafo(num_vertices, aristas_grafo)
        
        
        if algoritmo == "welsh_powell":
            colores, num_colores = grafo.coloreo_welsh_powell()
        elif algoritmo == "voraz":
            colores, num_colores = grafo.coloreo_voraz()
        else:
            colores, num_colores = grafo.coloreo_dsatur()

        sede_por_sesion = [sesion.grupo_padre.sede for sesion in sesiones]
        optimizador = OptimizadorTrasladosService(sesiones, grafo, sede_por_sesion)
        resultado_opt = optimizador.ejecutar(colores)
        colores = resultado_opt.colores  # usar el coloreo refinado en el resto del método

        if not grafo.es_coloreo_valido(colores):
            raise RuntimeError(f"Fallo crítico: El coloreo {algoritmo} contiene adyacencias inválidas.")

       # 4. Formatear salida aplicando la restricción física de 36 franjas
        horario_generado = []
        alertas_infraestructura = [] # NUEVO: Alertas para el Decano
        MAX_FRANJAS_FISICAS = 36     # Lunes a Sábado, 6 franjas diarias

        for vertice_idx, color in enumerate(colores):
            sesion = mapa_vertices[vertice_idx]
            grupo = sesion.grupo_padre
            
            # Si DSatur usó un color superior a la capacidad del edificio:
            if color >= MAX_FRANJAS_FISICAS:
                alerta = (
                    f"🛑 ALERTA DECANATURA - {grupo.materia.nombre} (Grupo {grupo.id_grupo}): "
                    f"Imposible programar la Clase {sesion.numero_sesion}. Límite físico de {MAX_FRANJAS_FISICAS} franjas excedido "
                    f"por alta densidad de cruces estudiantiles. Acción sugerida: Abrir nuevo grupo o redistribuir carga docente."
                )
                alertas_infraestructura.append(alerta)
                continue # Omitimos esta asignación porque no hay dónde dar la clase
            
            horario_generado.append({
                "id_nodo": sesion.id_sesion_nodo,
                "id_grupo": grupo.id_grupo,
                "materia": grupo.materia.nombre,
                "id_materia": grupo.materia.id_materia,
                "nivel_materia": grupo.materia.nivel,
                "numero_sesion": sesion.numero_sesion,
                "profesor": grupo.profesor_asignado.nombre,
                "color_franja_horaria": color,
                "cantidad_inscritos": len(grupo.estudiantes_inscritos)
            })

        return {
            "estado": "exito",
            "total_nodos_procesados": num_vertices,
            "total_franjas_requeridas": num_colores,
            "alertas_generador": alertas_infraestructura, 
            "asignaciones": horario_generado,
            "conflictos_resueltos": grafo.m,
            "resultado_optimizacion_inicial": resultado_opt.penalizacion_inicial,
            "resultado_optimizacion_final": resultado_opt.penalizacion_final
        }