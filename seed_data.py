import json
import random
import os

def generar_dataset_masivo():
    print("Iniciando generación de datos de prueba...")

    # 1. Catálogo de Materias
    materias = [
        { "id": "25941", "nombre": "Cálculo Diferencial", "nivel": 1, "creditos": 3, "sesiones_semanales": 2, "area_conocimiento": "Ciencias Básicas" },
        { "id": "7", "nombre": "Cálculo Integral", "nivel": 2, "creditos": 3, "sesiones_semanales": 2, "area_conocimiento": "Ciencias Básicas" },
        { "id": "16", "nombre": "Cálculo Multivariado", "nivel": 3, "creditos": 3, "sesiones_semanales": 2, "area_conocimiento": "Ciencias Básicas" },
        { "id": "88", "nombre": "Ecuaciones Diferenciales", "nivel": 4, "creditos": 3, "sesiones_semanales": 2, "area_conocimiento": "Ciencias Básicas" },
        { "id": "MN1", "nombre": "Métodos Numéricos", "nivel": 4, "creditos": 3, "sesiones_semanales": 2, "area_conocimiento": "Ciencias Básicas" },
        { "id": "415", "nombre": "Matemáticas Especiales", "nivel": 5, "creditos": 3, "sesiones_semanales": 2, "area_conocimiento": "Ciencias Básicas" },
        
        { "id": "FIS1", "nombre": "Física Mecánica", "nivel": 2, "creditos": 2, "sesiones_semanales": 1, "area_conocimiento": "Física" },
        
        { "id": "POO1", "nombre": "Programación Orientada a Objetos", "nivel": 2, "creditos": 4, "sesiones_semanales": 3, "area_conocimiento": "Programación" },
        { "id": "ED1", "nombre": "Estructuras de Datos", "nivel": 3, "creditos": 4, "sesiones_semanales": 3, "area_conocimiento": "Programación" },
        
        { "id": "ARQ1", "nombre": "Arquitectura de Computadores", "nivel": 5, "creditos": 3, "sesiones_semanales": 2, "area_conocimiento": "Ingeniería de Computadores" }
    ]

    # 2. Catálogo de Profesores 
    profesores = [
        # Expertos en Matemáticas
        { "id": "P_001", "nombre": "Augusto Peña", "tipo_contrato": "Planta", "max_creditos_docencia": 12, "areas_habilitadas": ["Ciencias Básicas"] },
        { "id": "P_002", "nombre": "Martha López", "tipo_contrato": "Planta", "max_creditos_docencia": 12, "areas_habilitadas": ["Ciencias Básicas"] },
        { "id": "P_003", "nombre": "Javier Ramírez", "tipo_contrato": "Catedratico", "max_creditos_docencia": 6, "areas_habilitadas": ["Ciencias Básicas", "Física"] },
        
        # Expertos en Programación
        { "id": "P_004", "nombre": "Carlos Medina", "tipo_contrato": "Ocasional", "max_creditos_docencia": 8, "areas_habilitadas": ["Programación"] },
        { "id": "P_005", "nombre": "Lucía Castro", "tipo_contrato": "Planta", "max_creditos_docencia": 12, "areas_habilitadas": ["Programación"] },
        { "id": "P_006", "nombre": "Roberto Sánchez", "tipo_contrato": "Catedratico", "max_creditos_docencia": 6, "areas_habilitadas": ["Programación", "Ingeniería de Computadores"] },
        
        # Expertos en Hardware y Arquitectura
        { "id": "P_007", "nombre": "Elena Torres", "tipo_contrato": "Ocasional", "max_creditos_docencia": 8, "areas_habilitadas": ["Ingeniería de Computadores"] },
        
        # Profesores Comodín (Saben varias cosas)
        { "id": "P_008", "nombre": "Diego Vargas", "tipo_contrato": "Planta", "max_creditos_docencia": 12, "areas_habilitadas": ["Ciencias Básicas", "Programación"] },
        { "id": "P_009", "nombre": "Patricia Gómez", "tipo_contrato": "Catedratico", "max_creditos_docencia": 6, "areas_habilitadas": ["Física", "Ingeniería de Computadores"] },
        { "id": "P_010", "nombre": "Andrés Silva", "tipo_contrato": "Planta", "max_creditos_docencia": 12, "areas_habilitadas": ["Ciencias Básicas", "Ingeniería de Computadores"] }
    ]

    # 3. Catálogo de 100 Estudiantes
    estudiantes = [
        { "id": "EST_001", "nombre": "Sergio Osorio" },
        { "id": "EST_002", "nombre": "Vanessa Becerra" },
        { "id": "EST_003", "nombre": "Sebas Osorio" }
    ]
    for i in range(4, 101):
        estudiantes.append({ "id": f"EST_{i:03d}", "nombre": f"Estudiante Prueba {i}" })

    # 4. Creación de Grupos
    grupos_abiertos = []
    for materia in materias:
        # Abrimos 2 grupos por cada materia para dar opciones al algoritmo
        for num_grupo in (1, 2):
            grupos_abiertos.append({
                "id_grupo": f"G0{num_grupo}_{materia['id']}",
                "id_materia": materia['id'],
                "cupo": 35,
                "estudiantes_inscritos": [],
                "_creditos": materia['creditos'] # Temporal para calcular el límite
            })

    # 5. Inscripción Aleatoria (Respetando máximo 18 créditos)
    creditos_por_estudiante = {est['id']: 0 for est in estudiantes}

    for estudiante in estudiantes:
        # Intentamos inscribir al estudiante en 4-5 grupos aleatorios
        grupos_random = random.sample(grupos_abiertos, k=5)
        
        for grupo in grupos_random:
            # Validamos no exceder los 18 créditos
            if creditos_por_estudiante[estudiante['id']] + grupo['_creditos'] <= 18:
                # Validamos que no esté inscrito en el otro grupo de la misma materia
                materia_id = grupo['id_materia']
                inscrito_en_materia = any(
                    estudiante['id'] in g['estudiantes_inscritos'] 
                    for g in grupos_abiertos if g['id_materia'] == materia_id
                )
                
                if not inscrito_en_materia:
                    grupo['estudiantes_inscritos'].append(estudiante['id'])
                    creditos_por_estudiante[estudiante['id']] += grupo['_creditos']

    # Limpiamos el campo temporal de créditos en los grupos
    for grupo in grupos_abiertos:
        del grupo['_creditos']

    # 6. Historial de Reprobación (Vetos aleatorios para estresar el Matching)
    historial_reprobacion = []
    # Creamos unos 40 vetos aleatorios
    for _ in range(40):
        est_random = random.choice(estudiantes)['id']
        mat_random = random.choice(materias)['id']
        profe_random = random.choice(profesores)['id']
        
        # Evitar duplicados exactos
        veto = {
            "id_estudiante": est_random,
            "id_materia": mat_random,
            "id_profesor_vetado": profe_random
        }
        if veto not in historial_reprobacion:
            historial_reprobacion.append(veto)

    # Añadimos un veto seguro para probar que funciona
    historial_reprobacion.append({
        "id_estudiante": "EST_001", # Sergio
        "id_materia": "88",         # Ecuaciones
        "id_profesor_vetado": "P_001" # Augusto Peña
    })

    # 7. Ensamblar y guardar JSON
    dataset_final = {
        "materias": materias,
        "profesores": profesores,
        "estudiantes": estudiantes,
        "grupos_abiertos": grupos_abiertos,
        "historial_reprobacion": historial_reprobacion
    }

    ruta_salida = "infrastructure/dataset/facultad_data.json"
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        json.dump(dataset_final, f, indent=2, ensure_ascii=False)

    print(f"¡Éxito! Dataset masivo generado en {ruta_salida}")
    print(f"Total Grupos: {len(grupos_abiertos)}")
    print(f"Total Vetos: {len(historial_reprobacion)}")

if __name__ == "__main__":
    generar_dataset_masivo()