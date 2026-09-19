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
NIVEL_MAXIMO = 10


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


def _generar_grupos(materias: List[Dict[str, Any]], grupos_por_materia: int = 2) -> List[Dict[str, Any]]:
    grupos = []
    for materia in materias:
        for num_grupo in range(1, grupos_por_materia + 1):
            grupos.append({
                "id_grupo": f"G{num_grupo:02d}_{materia['id']}",
                "id_materia": materia["id"],
                "sede": materia["sede"],
                "cupo": 35,
                "estudiantes_inscritos": [],
                "_creditos": materia["creditos"],  # temporal, se limpia después
            })
    return grupos


def _inscribir_estudiantes(
    estudiantes: List[Dict[str, Any]],
    grupos: List[Dict[str, Any]],
    rng: random.Random,
    limite_creditos: int = 18,
    intentos_por_estudiante: int = 5,
) -> None:
    """
    Mismo algoritmo de seed_data.py: cada estudiante intenta inscribirse en
    `intentos_por_estudiante` grupos aleatorios, respetando el límite de
    créditos y sin repetir materia.
    """
    creditos_por_estudiante = {est["id"]: 0 for est in estudiantes}

    for estudiante in estudiantes:
        k = min(intentos_por_estudiante, len(grupos))
        grupos_candidatos = rng.sample(grupos, k=k)

        for grupo in grupos_candidatos:
            if creditos_por_estudiante[estudiante["id"]] + grupo["_creditos"] <= limite_creditos:
                materia_id = grupo["id_materia"]
                ya_inscrito_en_materia = any(
                    estudiante["id"] in g["estudiantes_inscritos"]
                    for g in grupos if g["id_materia"] == materia_id
                )
                if not ya_inscrito_en_materia:
                    grupo["estudiantes_inscritos"].append(estudiante["id"])
                    creditos_por_estudiante[estudiante["id"]] += grupo["_creditos"]


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

    num_materias = max(4, round(num_estudiantes * PROPORCION_MATERIAS_POR_ESTUDIANTE))
    num_profesores = max(3, round(num_estudiantes * PROPORCION_PROFESORES_POR_ESTUDIANTE))
    num_vetos = max(1, round(num_estudiantes * VETOS_POR_ESTUDIANTE))

    materias = _generar_materias(num_materias)
    profesores = _generar_profesores(num_profesores, rng)
    estudiantes = _generar_estudiantes(num_estudiantes)
    grupos_abiertos = _generar_grupos(materias)

    _inscribir_estudiantes(estudiantes, grupos_abiertos, rng)

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
