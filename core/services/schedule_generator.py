import time
from typing import List, Tuple, Dict, Any

from core.entities import Grupo, SesionGrupo
from core.rules.base_rule import ReglaConflictoStrategy
from core.algorithms.graph_coloring import RepresentacionGrafo
from core.services.optimizacion_traslados import OptimizadorTrasladosService
from core.config import FRANJAS_POR_DIA_DEFECTO, DIAS_HABILES_POR_SEMANA_DEFECTO

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

    def ejecutar(
        self,
        grupos: List[Grupo],
        algoritmo: str = "dsatur",
        aplicar_refinamiento_sede: bool = True,
        max_iteraciones_refinamiento: int = 3000,
        franjas_por_dia: int = FRANJAS_POR_DIA_DEFECTO,
        dias_habiles: int = DIAS_HABILES_POR_SEMANA_DEFECTO,
    ) -> Dict[str, Any]:
        """
        franjas_por_dia / dias_habiles: definen Hmax = franjas_por_dia * dias_habiles,
        el número de bloques de tiempo distintos disponibles a la semana. Los
        valores por defecto reproducen el demo original (36 = 6x6). Para una
        simulación con el horario real de la universidad (bloques de 2h,
        6am-8pm, Lunes a Sábado) usarías franjas_por_dia=7, dias_habiles=6 -> 42.
        """
        if any(not g.esta_asignado() for g in grupos):
            raise ValueError("Todos los grupos deben tener un profesor asignado.")

        # 1. Expandimos los nodos antes de construir el grafo
        sesiones = self._expandir_grupos_a_sesiones(grupos)

        # 2. Construcción de aristas sobre las SESIONES, no los grupos
        t_inicio_aristas = time.perf_counter()
        aristas_grafo, mapa_vertices = self._construir_aristas(sesiones)
        tiempo_construccion_grafo_s = time.perf_counter() - t_inicio_aristas
        num_vertices = len(sesiones)

        # 3. Módulo Matemático
        grafo = RepresentacionGrafo(num_vertices, aristas_grafo)

        t_inicio_coloreo = time.perf_counter()
        if algoritmo == "welsh_powell":
            colores, num_colores = grafo.coloreo_welsh_powell()
        elif algoritmo == "voraz":
            colores, num_colores = grafo.coloreo_voraz()
        else:
            colores, num_colores = grafo.coloreo_dsatur()
        tiempo_coloreo_s = time.perf_counter() - t_inicio_coloreo

        sede_por_sesion = [sesion.grupo_padre.sede for sesion in sesiones]
        optimizador = OptimizadorTrasladosService(sesiones, grafo, sede_por_sesion, franjas_por_dia=franjas_por_dia)

        t_inicio_refinamiento = time.perf_counter()
        penalizacion_inicial = optimizador.calcular_penalizacion(colores)
        if aplicar_refinamiento_sede:
            resultado_opt = optimizador.ejecutar(colores, max_iteraciones=max_iteraciones_refinamiento)
            colores = resultado_opt.colores
            penalizacion_final = resultado_opt.penalizacion_final
        else:
            penalizacion_final = penalizacion_inicial
        tiempo_refinamiento_s = time.perf_counter() - t_inicio_refinamiento

        if not grafo.es_coloreo_valido(colores):
            raise RuntimeError(f"Fallo crítico: El coloreo {algoritmo} contiene adyacencias inválidas.")

       # 4. Formatear salida aplicando la restricción física de Hmax franjas
        horario_generado = []
        alertas_infraestructura = [] # NUEVO: Alertas para el Decano
        MAX_FRANJAS_FISICAS = franjas_por_dia * dias_habiles

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
            "hmax_utilizado": MAX_FRANJAS_FISICAS,
            "alertas_generador": alertas_infraestructura,
            "asignaciones": horario_generado,
            "conflictos_resueltos": grafo.m,
            "resultado_optimizacion_inicial": penalizacion_inicial,
            "resultado_optimizacion_final": penalizacion_final,
            # Métricas de tiempo por etapa (segundos), para el benchmark de escalabilidad
            "tiempo_construccion_grafo_s": tiempo_construccion_grafo_s,
            "tiempo_coloreo_s": tiempo_coloreo_s,
            "tiempo_refinamiento_s": tiempo_refinamiento_s,
        }