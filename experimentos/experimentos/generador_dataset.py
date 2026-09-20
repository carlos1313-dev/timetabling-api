"""
Generador paramétrico de datasets sintéticos para el benchmark de escalabilidad.

A diferencia de seed_data.py (que genera SIEMPRE el mismo dataset fijo de 100
estudiantes), este módulo genera un dataset de cualquier tamaño, conservando
las mismas proporciones aproximadas de la Facultad real:

    - 250 materias / 5000 estudiantes  -> 0.05 materias por estudiante
    - 120 profesores / 5000 estudiantes -> 0.024 profesores por estudiante
    -  40 vetos / 100 estudiantes (banco de pruebas original) -> 0.40 vetos/estudiante
    - Reparto de sedes ~40% / 40% / 20% (Calle 40 / Universidad ECCI / Calle 34)

5000 estudiantes es el techo real declarado; no se asume que el software
necesariamente lo soporte con buen desempeño — para eso es el benchmark.
"""

from __future__ import annotations
import math
import random
from typing import Dict, List, Any


# ---------------------------------------------------------------------------
# Proporciones de referencia (calibradas con el techo real de la universidad)
# ---------------------------------------------------------------------------
ESTUDIANTES_MAXIMOS_REFERENCIA = 5000
MATERIAS_MAXIMAS_REFERENCIA = 250
PROFESORES_MAXIMOS_REFERENCIA = 120
VETOS_POR_ESTUDIANTE = 0.40  # calibrado con el banco de pruebas original (40 vetos / 100 estudiantes)

PROPORCION_MATERIAS_POR_ESTUDIANTE = MATERIAS_MAXIMAS_REFERENCIA / ESTUDIANTES_MAXIMOS_REFERENCIA   # 0.05
PROPORCION_PROFESORES_POR_ESTUDIANTE = PROFESORES_MAXIMOS_REFERENCIA / ESTUDIANTES_MAXIMOS_REFERENCIA  # 0.024

AREAS_CONOCIMIENTO = ["Ciencias Básicas", "Física", "Programación", "Ingeniería de Computadores"]

# Reparto de sedes ~40% / 40% / 20%: patrón cíclico de longitud 5 que reproduce
# exactamente esa proporción (2/5, 2/5, 1/5) sin depender de aleatoriedad.
PATRON_SEDES = [
    "CALLE 40 (SABIO CALDAS / ADMINISTRATIVO)",
    "CALLE 40 (SABIO CALDAS / ADMINISTRATIVO)",
    "UNIVERSIDAD (ECCI S)",
    "UNIVERSIDAD (ECCI S)",
    "CALLE 34",
]

TIPOS_CONTRATO = [
    ("Planta", 12),
    ("Ocasional", 8),
    ("Catedratico", 6),
]

# Créditos y sesiones semanales típicos, ciclados para dar variedad realista
CREDITOS_CICLO = [2, 3, 3, 4]
SESIONES_SEMANALES_CICLO = [1, 2, 2, 3]
NIVEL_MAXIMO = 6  # ciclo básico + primeros semestres de ciclo profesional

# Piso mínimo de materias por nivel: a escalas pequeñas, la proporción real
# (0.05 materias/estudiante) no alcanza a llenar los 6 niveles con opciones
# suficientes para que el sesgo por cohorte tenga sentido. Este piso garantiza
# que siempre haya al menos MATERIAS_MINIMAS_POR_NIVEL materias por nivel,
# aunque eso implique apartarse un poco de la proporción estricta en escalas
# muy chicas (a partir de unos cientos de estudiantes, la proporción real
# domina y este piso deja de tener efecto).
MATERIAS_MINIMAS_POR_NIVEL = 2

# Probabilidad de que una inscripción individual "cruce" de nivel (el
# estudiante adelantado/atrasado de tu propio anteproyecto) en vez de tomar
# una materia de su propio nivel. 0.15 refleja que es la EXCEPCIÓN, no la
# norma -- a diferencia de la versión anterior de este generador, que
# inscribía a todo el mundo sin ninguna preferencia por nivel.
PROBABILIDAD_CRUCE_DE_NIVEL = 0.15

# --- Modelo de demanda por materia (grupos ya NO son un número fijo) ---
# Una materia "troncal" por nivel (la obligatoria que ve todo el mundo de ese
# semestre, tipo Cálculo I) escala su número de grupos según cuántos
# estudiantes hay en ese nivel, con techo de 8 -- el máximo real observado en
# la universidad. Las demás materias del nivel son electivas, con un número
# bajo y fijo de grupos (la demanda se diluye entre varias opciones).
CUPO_POR_GRUPO = 35
GRUPOS_POR_ELECTIVA = 2
MAX_GRUPOS_TRONCAL = 8


def _generar_materias(num_materias: int) -> List[Dict[str, Any]]:
    materias = []
    for i in range(num_materias):
        area = AREAS_CONOCIMIENTO[i % len(AREAS_CONOCIMIENTO)]
        materias.append({
            "id": f"M{i:04d}",
            "nombre": f"Materia Sintética {i:04d} ({area})",
            "nivel": (i % NIVEL_MAXIMO) + 1,
            "creditos": CREDITOS_CICLO[i % len(CREDITOS_CICLO)],
            "sesiones_semanales": SESIONES_SEMANALES_CICLO[i % len(SESIONES_SEMANALES_CICLO)],
            "area_conocimiento": area,
            "sede": PATRON_SEDES[i % len(PATRON_SEDES)],
            # Las primeras NIVEL_MAXIMO materias generadas son, por construcción,
            # la primera aparición de cada nivel (i=0 -> nivel 1, i=1 -> nivel 2,
            # ..., i=NIVEL_MAXIMO-1 -> nivel NIVEL_MAXIMO) -- esa es la troncal
            # obligatoria de ese semestre. El resto son electivas.
            "es_troncal": i < NIVEL_MAXIMO,
        })
    return materias


def _generar_profesores(num_profesores: int, rng: random.Random) -> List[Dict[str, Any]]:
    profesores = []
    for i in range(num_profesores):
        tipo_contrato, max_creditos = TIPOS_CONTRATO[i % len(TIPOS_CONTRATO)]

        # Cada ~5to profesor es "comodín" (dicta 2 áreas) para que el matching
        # bipartito tenga margen de maniobra, igual que en seed_data.py original.
        if i % 5 == 0:
            areas = rng.sample(AREAS_CONOCIMIENTO, k=2)
        else:
            areas = [AREAS_CONOCIMIENTO[i % len(AREAS_CONOCIMIENTO)]]

        profesores.append({
            "id": f"P_{i:04d}",
            "nombre": f"Docente Sintético {i:04d}",
            "tipo_contrato": tipo_contrato,
            "max_creditos_docencia": max_creditos,
            "areas_habilitadas": areas,
        })

    # Garantía de cobertura: a escalas pequeñas, la asignación cíclica de arriba
    # puede dejar un área sin NINGÚN profesor (por azar en los comodines). Si
    # eso pasa, cualquier materia de esa área cae siempre en el rescate del
    # AsignadorProfesoresService, sin importar el modo (baseline/propuesta),
    # contaminando la comparación de violaciones de veto. Se fuerza aquí.
    areas_cubiertas = {area for p in profesores for area in p["areas_habilitadas"]}
    areas_faltantes = [a for a in AREAS_CONOCIMIENTO if a not in areas_cubiertas]
    for idx, area_faltante in enumerate(areas_faltantes):
        profesor_receptor = profesores[idx % len(profesores)]
        if area_faltante not in profesor_receptor["areas_habilitadas"]:
            profesor_receptor["areas_habilitadas"].append(area_faltante)

    return profesores


def _generar_estudiantes(num_estudiantes: int) -> List[Dict[str, Any]]:
    return [
        {"id": f"EST_{i:05d}", "nombre": f"Estudiante Sintético {i:05d}"}
        for i in range(1, num_estudiantes + 1)
    ]


def _calcular_grupos_troncal(num_estudiantes: int) -> int:
    """
    Estima cuántos grupos necesita la materia troncal de un nivel, asumiendo
    que TODOS los estudiantes de ese nivel la toman (es obligatoria) y que la
    población se reparte parejo entre los NIVEL_MAXIMO niveles (igual que
    _asignar_cohortes). Techo real de la universidad: MAX_GRUPOS_TRONCAL.
    """
    estudiantes_por_nivel = num_estudiantes / NIVEL_MAXIMO
    grupos_necesarios = math.ceil(estudiantes_por_nivel / CUPO_POR_GRUPO)
    return max(1, min(MAX_GRUPOS_TRONCAL, grupos_necesarios))


def _generar_grupos(materias: List[Dict[str, Any]], num_estudiantes: int) -> List[Dict[str, Any]]:
    grupos_troncal = _calcular_grupos_troncal(num_estudiantes)

    grupos = []
    for materia in materias:
        num_grupos_materia = grupos_troncal if materia["es_troncal"] else GRUPOS_POR_ELECTIVA
        for num_grupo in range(1, num_grupos_materia + 1):
            grupos.append({
                "id_grupo": f"G{num_grupo:02d}_{materia['id']}",
                "id_materia": materia["id"],
                "sede": materia["sede"],
                "cupo": CUPO_POR_GRUPO,
                "estudiantes_inscritos": [],
                "_creditos": materia["creditos"],  # temporal, se limpia después
            })
    return grupos


def _asignar_cohortes(estudiantes: List[Dict[str, Any]]) -> None:
    """
    Asigna a cada estudiante un nivel de cohorte (en qué semestre está),
    repartido de forma pareja entre 1 y NIVEL_MAXIMO. Es lo que permite luego
    preferir materias de su propio nivel al inscribirlo.
    """
    for idx, estudiante in enumerate(estudiantes):
        estudiante["_nivel_cohorte"] = (idx % NIVEL_MAXIMO) + 1


def _inscribir_estudiantes(
    estudiantes: List[Dict[str, Any]],
    grupos: List[Dict[str, Any]],
    materias_por_id: Dict[str, Dict[str, Any]],
    rng: random.Random,
    limite_creditos: int = 18,
    intentos_electivas: int = 4,
) -> None:
    """
    Cada estudiante:
      1. Se inscribe SIEMPRE en la troncal de su nivel (es obligatoria), repartido
         en round-robin entre los grupos de esa troncal -- así se respeta el
         dimensionamiento hecho en _calcular_grupos_troncal en vez de que todos
         caigan por azar en el mismo primer grupo.
      2. Completa con `intentos_electivas` materias electivas, con la misma
         lógica de antes: mayoría de su propio nivel, una minoría
         (PROBABILIDAD_CRUCE_DE_NIVEL) de otro nivel (adelantado/atrasado).
    """
    _asignar_cohortes(estudiantes)

    grupos_por_nivel: Dict[int, List[Dict[str, Any]]] = defaultdict_lista(NIVEL_MAXIMO)
    grupos_troncal_por_nivel: Dict[int, List[Dict[str, Any]]] = defaultdict_lista(NIVEL_MAXIMO)
    for grupo in grupos:
        materia = materias_por_id[grupo["id_materia"]]
        grupos_por_nivel[materia["nivel"]].append(grupo)
        if materia["es_troncal"]:
            grupos_troncal_por_nivel[materia["nivel"]].append(grupo)

    creditos_por_estudiante = {est["id"]: 0 for est in estudiantes}
    contador_troncal_por_nivel = {nivel: 0 for nivel in range(1, NIVEL_MAXIMO + 1)}

    for estudiante in estudiantes:
        nivel_propio = estudiante["_nivel_cohorte"]

        # 1. Troncal obligatoria, repartida round-robin entre sus grupos.
        grupos_troncal = grupos_troncal_por_nivel.get(nivel_propio)
        if grupos_troncal:
            idx = contador_troncal_por_nivel[nivel_propio] % len(grupos_troncal)
            grupo_troncal = grupos_troncal[idx]
            contador_troncal_por_nivel[nivel_propio] += 1
            if creditos_por_estudiante[estudiante["id"]] + grupo_troncal["_creditos"] <= limite_creditos:
                grupo_troncal["estudiantes_inscritos"].append(estudiante["id"])
                creditos_por_estudiante[estudiante["id"]] += grupo_troncal["_creditos"]

        # 2. Electivas.
        pool_propio = grupos_por_nivel.get(nivel_propio) or grupos
        for _ in range(intentos_electivas):
            es_cruce = rng.random() < PROBABILIDAD_CRUCE_DE_NIVEL
            pool = grupos if es_cruce else pool_propio
            if not pool:
                continue
            grupo = rng.choice(pool)

            if creditos_por_estudiante[estudiante["id"]] + grupo["_creditos"] > limite_creditos:
                continue

            materia_id = grupo["id_materia"]
            ya_inscrito_en_materia = any(
                estudiante["id"] in g["estudiantes_inscritos"]
                for g in grupos if g["id_materia"] == materia_id
            )
            if not ya_inscrito_en_materia:
                grupo["estudiantes_inscritos"].append(estudiante["id"])
                creditos_por_estudiante[estudiante["id"]] += grupo["_creditos"]


def defaultdict_lista(nivel_maximo: int) -> Dict[int, List[Dict[str, Any]]]:
    return {nivel: [] for nivel in range(1, nivel_maximo + 1)}


def _generar_historial_reprobacion(
    estudiantes: List[Dict[str, Any]],
    materias: List[Dict[str, Any]],
    profesores: List[Dict[str, Any]],
    num_vetos: int,
    rng: random.Random,
) -> List[Dict[str, Any]]:
    historial = []
    intentos = 0
    # Límite de intentos para no colgarse si num_vetos es más grande que las
    # combinaciones únicas posibles en datasets muy pequeños.
    max_intentos = num_vetos * 20

    while len(historial) < num_vetos and intentos < max_intentos:
        intentos += 1
        veto = {
            "id_estudiante": rng.choice(estudiantes)["id"],
            "id_materia": rng.choice(materias)["id"],
            "id_profesor_vetado": rng.choice(profesores)["id"],
        }
        if veto not in historial:
            historial.append(veto)
    return historial


def generar_dataset(num_estudiantes: int, semilla: int = 42) -> Dict[str, Any]:
    """
    Genera un dataset sintético completo para `num_estudiantes`, escalando
    materias, profesores y vetos según las proporciones reales de la
    universidad (ver constantes al inicio del módulo).
    """
    rng = random.Random(semilla)

    num_materias = max(4, round(num_estudiantes * PROPORCION_MATERIAS_POR_ESTUDIANTE), NIVEL_MAXIMO * MATERIAS_MINIMAS_POR_NIVEL)
    num_vetos = max(1, round(num_estudiantes * VETOS_POR_ESTUDIANTE))

    # Total de grupos esperado con el modelo de demanda troncal/electiva
    # (antes de generarlos), para poder dimensionar profesores con margen real
    # de capacidad y no solo con la proporción de estudiantes.
    grupos_troncal = _calcular_grupos_troncal(num_estudiantes)
    total_grupos_esperado = (num_materias - NIVEL_MAXIMO) * GRUPOS_POR_ELECTIVA + NIVEL_MAXIMO * grupos_troncal

    # Capacidad mínima asumiendo el peor caso (2 grupos/profesor, contrato
    # Catedrático) para que el matching real tenga margen y no caiga
    # sistemáticamente en el rescate por escasez, además de la proporción real.
    CAPACIDAD_MINIMA_POR_PROFESOR = 2
    profesores_por_capacidad = math.ceil(total_grupos_esperado / CAPACIDAD_MINIMA_POR_PROFESOR)

    num_profesores = max(
        3,
        len(AREAS_CONOCIMIENTO),
        round(num_estudiantes * PROPORCION_PROFESORES_POR_ESTUDIANTE),
        profesores_por_capacidad,
    )

    materias = _generar_materias(num_materias)
    materias_por_id = {m["id"]: m for m in materias}
    profesores = _generar_profesores(num_profesores, rng)
    estudiantes = _generar_estudiantes(num_estudiantes)
    grupos_abiertos = _generar_grupos(materias, num_estudiantes)

    _inscribir_estudiantes(estudiantes, grupos_abiertos, materias_por_id, rng)

    historial_reprobacion = _generar_historial_reprobacion(
        estudiantes, materias, profesores, num_vetos, rng
    )

    # Limpiar el campo temporal de créditos
    for grupo in grupos_abiertos:
        del grupo["_creditos"]

    return {
        "materias": materias,
        "profesores": profesores,
        "estudiantes": estudiantes,
        "grupos_abiertos": grupos_abiertos,
        "historial_reprobacion": historial_reprobacion,
        # Metadatos útiles para el reporte del benchmark (no forman parte del
        # esquema que consume FacultadJSONRepository)
        "_metadata": {
            "num_estudiantes": num_estudiantes,
            "num_materias": num_materias,
            "num_profesores": num_profesores,
            "num_grupos": len(grupos_abiertos),
            "num_vetos": len(historial_reprobacion),
        },
    }
