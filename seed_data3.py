import json
import random

def generar_escenario_malla():
    materias = [
        {"id": "M1", "nombre": "Cálculo Diferencial", "nivel": 1, "creditos": 3, "sesiones_semanales": 2, "area_conocimiento": "Ciencias Básicas"},
        {"id": "M2", "nombre": "Programación Básica", "nivel": 1, "creditos": 3, "sesiones_semanales": 2, "area_conocimiento": "Programación"},
        {"id": "M3", "nombre": "Cálculo Integral", "nivel": 2, "creditos": 3, "sesiones_semanales": 2, "area_conocimiento": "Ciencias Básicas"},
        {"id": "M4", "nombre": "Física Mecánica", "nivel": 2, "creditos": 3, "sesiones_semanales": 2, "area_conocimiento": "Física"},
        {"id": "M5", "nombre": "Estructuras de Datos", "nivel": 3, "creditos": 4, "sesiones_semanales": 3, "area_conocimiento": "Programación"}
    ]

    profesores = [
        {"id": "P1", "nombre": "Augusto Peña", "tipo_contrato": "Planta", "max_creditos_docencia": 60, "areas_habilitadas": ["Ciencias Básicas", "Física"]},
        {"id": "P2", "nombre": "Lucía Castro", "tipo_contrato": "Planta", "max_creditos_docencia": 60, "areas_habilitadas": ["Programación"]},
        {"id": "P3", "nombre": "Javier Ramírez", "tipo_contrato": "Planta", "max_creditos_docencia": 60, "areas_habilitadas": ["Física", "Ciencias Básicas"]},
        {"id": "P4", "nombre": "Elena Torres", "tipo_contrato": "Planta", "max_creditos_docencia": 60, "areas_habilitadas": ["Programación", "Ciencias Básicas"]}
    ]

    # Distribución aproximada para 5 materias:
    # 2 Calle 40, 2 Universidad, 1 Calle 34.
    sedes_por_materia = {
        "M1": "CALLE 40 (SABIO CALDAS / ADMINISTRATIVO)",
        "M2": "CALLE 40 (SABIO CALDAS / ADMINISTRATIVO)",
        "M3": "UNIVERSIDAD (ECCI S)",
        "M4": "UNIVERSIDAD (ECCI S)",
        "M5": "CALLE 34"
    }

    grupos_abiertos = []
    for m in materias:
        for num_grupo in (1, 2):
            grupos_abiertos.append({
                "id_grupo": f"GR_{m['id']}_{num_grupo}",
                "id_materia": m['id'],
                "sede": sedes_por_materia[m['id']],
                "cupo": 35,
                "estudiantes_inscritos": []
            })

    historial_reprobacion = []

    for i in range(1, 61):
        est_id = f"EST_{i:03d}"
        materias_elegidas = random.sample(materias, k=random.randint(3, 4))

        for m in materias_elegidas:
            grupo_elegido = random.choice([
                g for g in grupos_abiertos if g["id_materia"] == m["id"]
            ])
            grupo_elegido["estudiantes_inscritos"].append(est_id)

        if random.random() < 0.3:
            mat_vetada = random.choice(materias_elegidas)
            profe_vetado = (
                "P1"
                if mat_vetada["area_conocimiento"] in ["Ciencias Básicas", "Física"]
                else "P2"
            )
            historial_reprobacion.append({
                "id_estudiante": est_id,
                "id_materia": mat_vetada["id"],
                "id_profesor_vetado": profe_vetado
            })

    datos = {
        "materias": materias,
        "profesores": profesores,
        "historial_reprobacion": historial_reprobacion,
        "grupos_abiertos": grupos_abiertos
    }

    with open("infrastructure/dataset/facultad_data.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)
    print("✅ Escenario 2 (Triangulación de Mallas) generado exitosamente.")

if __name__ == "__main__":
    generar_escenario_malla()
