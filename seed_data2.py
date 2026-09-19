import json

def generar_escenario_ideal():
    materias = [
        {"id": "M1", "nombre": "Cálculo Diferencial", "nivel": 1, "creditos": 3, "sesiones_semanales": 2, "area_conocimiento": "Ciencias Básicas"},
        {"id": "M2", "nombre": "Programación Básica", "nivel": 1, "creditos": 3, "sesiones_semanales": 2, "area_conocimiento": "Programación"},
        {"id": "M3", "nombre": "Cálculo Integral", "nivel": 2, "creditos": 3, "sesiones_semanales": 2, "area_conocimiento": "Ciencias Básicas"},
        {"id": "M4", "nombre": "Física Mecánica", "nivel": 2, "creditos": 3, "sesiones_semanales": 2, "area_conocimiento": "Física"},
        {"id": "M5", "nombre": "Estructuras de Datos", "nivel": 3, "creditos": 4, "sesiones_semanales": 3, "area_conocimiento": "Programación"}
    ]

    profesores = [
        {"id": "P1", "nombre": "Augusto Peña", "tipo_contrato": "Planta", "max_creditos_docencia": 60, "areas_habilitadas": ["Ciencias Básicas"]},
        {"id": "P2", "nombre": "Lucía Castro", "tipo_contrato": "Planta", "max_creditos_docencia": 60, "areas_habilitadas": ["Programación"]},
        {"id": "P3", "nombre": "Javier Ramírez", "tipo_contrato": "Planta", "max_creditos_docencia": 60, "areas_habilitadas": ["Física", "Ciencias Básicas"]}
    ]

    # Para 5 materias, la aproximación entera de la distribución es:
    # 2 materias en Calle 40, 2 en Universidad y 1 en Calle 34.
    sedes_por_materia = {
        "M1": "CALLE 40 (SABIO CALDAS / ADMINISTRATIVO)",
        "M2": "CALLE 40 (SABIO CALDAS / ADMINISTRATIVO)",
        "M3": "UNIVERSIDAD (ECCI S)",
        "M4": "UNIVERSIDAD (ECCI S)",
        "M5": "CALLE 34"
    }

    grupos_abiertos = [
        {"id_grupo": "GR_M1", "id_materia": "M1", "sede": sedes_por_materia["M1"], "cupo": 30, "estudiantes_inscritos": []},
        {"id_grupo": "GR_M2", "id_materia": "M2", "sede": sedes_por_materia["M2"], "cupo": 30, "estudiantes_inscritos": []},
        {"id_grupo": "GR_M3", "id_materia": "M3", "sede": sedes_por_materia["M3"], "cupo": 30, "estudiantes_inscritos": []},
        {"id_grupo": "GR_M4", "id_materia": "M4", "sede": sedes_por_materia["M4"], "cupo": 30, "estudiantes_inscritos": []},
        {"id_grupo": "GR_M5", "id_materia": "M5", "sede": sedes_por_materia["M5"], "cupo": 30, "estudiantes_inscritos": []}
    ]

    for i in range(1, 31):
        est_id = f"EST_{i:03d}"
        if i <= 10:
            grupos_abiertos[0]["estudiantes_inscritos"].append(est_id)
            grupos_abiertos[1]["estudiantes_inscritos"].append(est_id)
        elif i <= 20:
            grupos_abiertos[2]["estudiantes_inscritos"].append(est_id)
            grupos_abiertos[3]["estudiantes_inscritos"].append(est_id)
        else:
            grupos_abiertos[4]["estudiantes_inscritos"].append(est_id)

    datos = {
        "materias": materias,
        "profesores": profesores,
        "historial_reprobacion": [],
        "grupos_abiertos": grupos_abiertos
    }

    with open("infrastructure/dataset/facultad_data.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)
    print("✅ Escenario 1 (Flujo Ideal) generado exitosamente.")

if __name__ == "__main__":
    generar_escenario_ideal()
