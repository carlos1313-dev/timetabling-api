"""
Runner de benchmark de escalabilidad.

Para cada tamaño en ESCALAS_ESTUDIANTES, genera UN dataset sintético (misma
semilla para ambos modos, para que la comparación sea justa) y lo corre dos
veces por el pipeline completo:

    - "baseline"  -> AsignadorProfesoresService(respetar_vetos=False)
                     GeneradorHorariosService.ejecutar(aplicar_refinamiento_sede=False)
                     (equivalente a un UCTP genérico, sin las restricciones
                      contextuales propuestas en el artículo)

    - "propuesta" -> comportamiento actual completo (vetos + refinamiento de sede)

Guarda una fila por corrida en experimentos/resultados_benchmark.csv con
tiempos por etapa y las métricas de violaciones (traslados, vetos, franjas).

Uso:
    python experimentos/run_benchmark.py
    python experimentos/run_benchmark.py --escalas 20 50 100 250 500
    python experimentos/run_benchmark.py --incluir-techo   # agrega 5000 al final

ADVERTENCIA: la escala 5000 (el techo real de la universidad) puede tardar
varios minutos y no se corre por defecto — actívala explícitamente con
--incluir-techo cuando quieras estresar el límite superior.
"""

from __future__ import annotations
import argparse
import csv
import os
import sys
import time
import traceback
from typing import Any, Dict, List

# Asegura que el repo raíz esté en sys.path sin importar desde dónde se llame el script.
RAIZ_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ_REPO not in sys.path:
    sys.path.insert(0, RAIZ_REPO)

from core.services.assign_professors import AsignadorProfesoresService
from core.services.schedule_generator import GeneradorHorariosService
from core.services.metricas import contar_violaciones_veto
from core.rules.default_rules import (
    ReglaMismoProfesor,
    ReglaEstudiantesCompartidos,
    ReglaSesionesMismoGrupo,
)

from experimentos.generador_dataset import generar_dataset
from experimentos.hidratar import hidratar_desde_dict


ESCALAS_ESTUDIANTES_DEFECTO = [20, 50, 100, 250, 500, 1000, 2000]
ESCALA_TECHO_REAL = 5000
SEMILLAS_DEFECTO = [42]

# Horario real de la universidad (bloques de 2h, 6:00 AM - 8:00 PM, Lunes a Sábado)
FRANJAS_POR_DIA_REAL = 7
DIAS_HABILES_REAL = 6

# Tres modos de comparación:
#   - baseline_dsatur       : tu propio algoritmo, SIN veto ni refinamiento de sede
#                             (ablación: aísla el efecto de tus restricciones)
#   - baseline_welsh_powell : algoritmo clásico de la literatura, SIN veto ni
#                             refinamiento (referencia externa, no inventada por ti)
#   - propuesta             : DSatur + veto + refinamiento de sede (tu propuesta completa)
CONFIGURACION_MODOS = {
    "baseline_dsatur": {"algoritmo": "dsatur", "respetar_vetos": False, "refinar": False},
    "baseline_welsh_powell": {"algoritmo": "welsh_powell", "respetar_vetos": False, "refinar": False},
    "propuesta": {"algoritmo": "dsatur", "respetar_vetos": True, "refinar": True},
}


def _reglas_conflicto() -> List:
    # ReglaMismoSemestre se deja fuera deliberadamente: exigía "mismo nivel"
    # SIN comprobar estudiantes compartidos, generando un clique completo por
    # nivel (todas las materias de un semestre mutuamente en conflicto, aunque
    # ningún estudiante real tomara ambas). ReglaEstudiantesCompartidos ya
    # captura el conflicto real -- mismo nivel + estudiantes compartidos es
    # matemáticamente idéntico a solo estudiantes compartidos, así que
    # agregar de vuelta la condición de nivel no cambia nada, solo la quita.
    return [ReglaSesionesMismoGrupo(), ReglaMismoProfesor(), ReglaEstudiantesCompartidos()]


def _correr_una_combinacion(datos_crudos: Dict[str, Any], modo: str) -> Dict[str, Any]:
    """
    Corre el pipeline completo una vez, según la configuración de `modo`
    (ver CONFIGURACION_MODOS), y devuelve una fila de resultados lista para
    el CSV. Usa el Hmax REAL de la universidad (franjas de 2h, 6am-8pm,
    Lunes a Sábado), no el de 36 del demo original de 100 estudiantes.
    """
    config = CONFIGURACION_MODOS[modo]

    t_inicio_total = time.perf_counter()

    profesores, grupos, historial = hidratar_desde_dict(datos_crudos)

    t_inicio_matching = time.perf_counter()
    asignador = AsignadorProfesoresService(profesores, historial, respetar_vetos=config["respetar_vetos"])
    grupos_asignados, alertas_matching = asignador.ejecutar(grupos)
    tiempo_matching_s = time.perf_counter() - t_inicio_matching

    generador = GeneradorHorariosService(_reglas_conflicto())
    resultado = generador.ejecutar(
        grupos_asignados,
        algoritmo=config["algoritmo"],
        aplicar_refinamiento_sede=config["refinar"],
        franjas_por_dia=FRANJAS_POR_DIA_REAL,
        dias_habiles=DIAS_HABILES_REAL,
    )

    violaciones_veto = contar_violaciones_veto(grupos_asignados, historial)
    tiempo_total_s = time.perf_counter() - t_inicio_total

    traslados_antes = resultado["resultado_optimizacion_inicial"]
    traslados_despues = resultado["resultado_optimizacion_final"]
    reduccion_traslados_pct = (
        100.0 * (traslados_antes - traslados_despues) / traslados_antes if traslados_antes > 0 else 0.0
    )

    return {
        "modo": modo,
        "estado": "ok",
        "num_alertas_matching": len(alertas_matching),
        "num_alertas_decanatura": len(resultado["alertas_generador"]),
        "franjas_requeridas": resultado["total_franjas_requeridas"],
        "hmax_utilizado": resultado["hmax_utilizado"],
        "excede_hmax": resultado["total_franjas_requeridas"] > resultado["hmax_utilizado"],
        "violaciones_veto": violaciones_veto,
        "traslados_antes": traslados_antes,
        "traslados_despues": traslados_despues,
        "reduccion_traslados_pct": round(reduccion_traslados_pct, 2),
        "tiempo_matching_s": round(tiempo_matching_s, 4),
        "tiempo_construccion_grafo_s": round(resultado["tiempo_construccion_grafo_s"], 4),
        "tiempo_coloreo_s": round(resultado["tiempo_coloreo_s"], 4),
        "tiempo_refinamiento_s": round(resultado["tiempo_refinamiento_s"], 4),
        "tiempo_total_s": round(tiempo_total_s, 4),
    }


def _fila_error(modo: str, excepcion: Exception) -> Dict[str, Any]:
    return {
        "modo": modo,
        "estado": f"error: {type(excepcion).__name__}: {excepcion}",
        "num_alertas_matching": None, "num_alertas_decanatura": None,
        "franjas_requeridas": None, "hmax_utilizado": None, "excede_hmax": None,
        "violaciones_veto": None, "traslados_antes": None, "traslados_despues": None,
        "reduccion_traslados_pct": None, "tiempo_matching_s": None,
        "tiempo_construccion_grafo_s": None, "tiempo_coloreo_s": None,
        "tiempo_refinamiento_s": None, "tiempo_total_s": None,
    }


def ejecutar_benchmark(escalas: List[int], semillas: List[int], ruta_salida_csv: str) -> List[Dict[str, Any]]:
    filas: List[Dict[str, Any]] = []

    for escala in escalas:
        for semilla in semillas:
            print(f"\n=== Escala: {escala} estudiantes | semilla: {semilla} ===")
            datos_crudos = generar_dataset(escala, semilla=semilla)
            metadata = datos_crudos["_metadata"]
            print(
                f"  Dataset generado -> materias={metadata['num_materias']} "
                f"profesores={metadata['num_profesores']} grupos={metadata['num_grupos']} "
                f"vetos={metadata['num_vetos']}"
            )

            for modo in CONFIGURACION_MODOS:
                print(f"  Corriendo modo '{modo}'...", end=" ", flush=True)
                try:
                    fila = _correr_una_combinacion(datos_crudos, modo)
                    print(
                        f"OK ({fila['tiempo_total_s']}s, "
                        f"traslados {fila['traslados_antes']}->{fila['traslados_despues']}, "
                        f"vetos={fila['violaciones_veto']}, franjas={fila['franjas_requeridas']}/{fila['hmax_utilizado']})"
                    )
                except Exception as exc:  # noqa: BLE001 - capturamos cualquier falla y seguimos con la siguiente combinación
                    fila = _fila_error(modo, exc)
                    print(f"FALLÓ: {exc}")
                    traceback.print_exc()

                fila_completa = {
                    "num_estudiantes": escala,
                    "semilla": semilla,
                    "num_materias": metadata["num_materias"],
                    "num_profesores": metadata["num_profesores"],
                    "num_grupos": metadata["num_grupos"],
                    "num_vetos_generados": metadata["num_vetos"],
                    **fila,
                }
                filas.append(fila_completa)

    os.makedirs(os.path.dirname(ruta_salida_csv), exist_ok=True)
    campos = list(filas[0].keys()) if filas else []
    with open(ruta_salida_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(filas)

    print(f"\nBenchmark completo. Resultados guardados en: {ruta_salida_csv}")
    return filas


def main():
    parser = argparse.ArgumentParser(description="Benchmark de escalabilidad UCTP (baseline_dsatur vs baseline_welsh_powell vs propuesta).")
    parser.add_argument("--escalas", type=int, nargs="+", default=ESCALAS_ESTUDIANTES_DEFECTO,
                         help="Lista de tamaños (num_estudiantes) a probar. Longitud y valores libres.")
    parser.add_argument("--semillas", type=int, nargs="+", default=SEMILLAS_DEFECTO,
                         help="Lista de semillas a probar por cada escala (para promedio ± desviación).")
    parser.add_argument("--incluir-techo", action="store_true",
                         help=f"Agrega la escala {ESCALA_TECHO_REAL} (techo real de la universidad) al final.")
    parser.add_argument("--salida", type=str,
                         default=os.path.join(os.path.dirname(__file__), "resultados_benchmark.csv"),
                         help="Ruta del CSV de salida.")
    args = parser.parse_args()

    escalas = list(args.escalas)
    if args.incluir_techo and ESCALA_TECHO_REAL not in escalas:
        escalas.append(ESCALA_TECHO_REAL)

    ejecutar_benchmark(escalas, list(args.semillas), args.salida)


if __name__ == "__main__":
    main()
