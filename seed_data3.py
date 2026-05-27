import json
import random

def generar_escenario_estres():
    materias = [
        {"id": "M1", "nombre": "Ecuaciones Diferenciales", "nivel": 4, "creditos": 3, "sesiones_semanales": 2, "area_conocimiento": "Ciencias Básicas"},
        {"id": "M2", "nombre": "Métodos Numéricos", "nivel": 4, "creditos": 3, "sesiones_semanales": 2, "area_conocimiento": "Ciencias Básicas"},
        {"id": "M3", "nombre": "Arquitectura de Computadores", "nivel": 4, "creditos": 3, "sesiones_semanales": 2, "area_conocimiento": "Ingeniería de Computadores"},
        {"id": "M4", "nombre": "Redes de Datos", "nivel": 5, "creditos": 3, "sesiones_semanales": 3, "area_conocimiento": "Ingeniería de Computadores"},
        {"id": "M5", "nombre": "Ingeniería de Software", "nivel": 5, "creditos": 4, "sesiones_semanales": 3, "area_conocimiento": "Programación"}
    ]
    
    profesores = [
        {"id": "P1", "nombre": "Augusto Peña", "tipo_contrato": "Planta", "max_creditos_docencia": 90, "areas_habilitadas": ["Ciencias Básicas"]},
        {"id": "P2", "nombre": "Lucía Castro", "tipo_contrato": "Planta", "max_creditos_docencia": 90, "areas_habilitadas": ["Programación"]},
        {"id": "P3", "nombre": "Javier Ramírez", "tipo_contrato": "Planta", "max_creditos_docencia": 90, "areas_habilitadas": ["Ingeniería de Computadores"]},
        {"id": "P4", "nombre": "Roberto Sánchez", "tipo_contrato": "Planta", "max_creditos_docencia": 90, "areas_habilitadas": ["Ciencias Básicas", "Programación"]},
        {"id": "P5", "nombre": "Patricia Gómez", "tipo_contrato": "Planta", "max_creditos_docencia": 90, "areas_habilitadas": ["Ingeniería de Computadores", "Programación"]}
    ]
    
    # Creamos 3 grupos por materia para elevar el volumen total de sesiones en la facultad
    grupos_abiertos = []
    for m in materias:
        for g_idx in range(1, 4):
            grupos_abiertos.append({"id_grupo": f"GR_{m['id']}_{g_idx}", "id_materia": m['id'], "cupo": 40, "estudiantes_inscritos": []})
    
    historial_reprobacion = []
    
    # 1. GENERACIÓN DEL CLIQUE: 40 estudiantes inscritos exactamente en los mismos grupos
    for i in range(1, 41):
        est_id = f"EST_CLIQUE_{i:03d}"
        for m in materias:
            g = next(grp for grp in grupos_abiertos if grp["id_grupo"] == f"GR_{m['id']}_1")
            g["estudiantes_inscritos"].append(est_id)
        
        if i % 5 == 0:
            historial_reprobacion.append({
                "id_estudiante": est_id,
                "id_materia": "M1",
                "id_profesor_vetado": "P1"
            })

    # 2. RUIDO MATRICULAR: 60 estudiantes dispersos en los grupos restantes
    for i in range(41, 101):
        est_id = f"EST_RUIDO_{i:03d}"
        materias_elegidas = random.sample(materias, k=3)
        for m in materias_elegidas:
            g = random.choice([grp for grp in grupos_abiertos if grp["id_materia"] == m["id"]])
            g["estudiantes_inscritos"].append(est_id)

    datos = {
        "materias": materias,
        "profesores": profesores,
        "historial_reprobacion": historial_reprobacion,
        "grupos_abiertos": grupos_abiertos
    }

    with open("infrastructure/dataset/facultad_data.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)
    print("✅ Escenario 3 (Estrés Crítico con Grupos) generado exitosamente.")

if __name__ == "__main__":
    generar_escenario_estres()