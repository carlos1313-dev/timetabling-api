from fastapi import APIRouter, HTTPException
from api.schemas import HorarioResponse

from infrastructure.data_sources.file_repository import FacultadJSONRepository
from core.services.validations import ValidadorInscripcionesService
from core.services.assign_professors import AsignadorProfesoresService
from core.services.schedule_generator import GeneradorHorariosService
from core.rules.default_rules import (
    ReglaMismoProfesor, 
    ReglaMismoSemestre, 
    ReglaEstudiantesCompartidos,
    ReglaSesionesMismoGrupo
)

router = APIRouter()

@router.post("/generar", response_model=HorarioResponse)
def generar_horarios():
    try:
        # 1. Infraestructura: Cargar los datos desde el archivo
        repo = FacultadJSONRepository(file_path="infrastructure/dataset/facultad_data.json")
        profesores, grupos, historial = repo.cargar_datos_completos()

        # Obtenemos TODOS los estudiantes inscritos en la base de datos cruda
        import json
        with open("infrastructure/dataset/facultad_data.json", 'r', encoding='utf-8') as f:
            datos_base = json.load(f)
            todos_estudiantes = {e['id']: e['nombre'] for e in datos_base.get('estudiantes', [])}
        # 2. Validaciones de Negocio (Fail-Fast)
        validador = ValidadorInscripcionesService(limite_creditos=18)
        validador.validar_limite_creditos(grupos)
        # 3. Etapa A: Asignar Profesores (Matching Bipartito)
        asignador = AsignadorProfesoresService(profesores, historial)
        grupos_asignados, alertas = asignador.ejecutar(grupos)

        reglas = [ReglaSesionesMismoGrupo(), ReglaMismoProfesor(), ReglaMismoSemestre(), ReglaEstudiantesCompartidos()]
        generador = GeneradorHorariosService(reglas)
        resultado = generador.ejecutar(grupos_asignados)

        # Identificar estudiantes sin carga
        estudiantes_con_carga = set()
        for g in grupos_asignados:
            estudiantes_con_carga.update(g.estudiantes_inscritos)
        
        sin_carga = [f"{nombre} ({id_est})" for id_est, nombre in todos_estudiantes.items() if id_est not in estudiantes_con_carga]

        # Mapear la lista de estudiantes para el Frontend
        for asig in resultado["asignaciones"]:
            grupo_obj = next(g for g in grupos_asignados if g.id_grupo == asig["id_grupo"])
            asig["estudiantes_inscritos"] = list(grupo_obj.estudiantes_inscritos)

        alertas_totales = alertas + resultado.get("alertas_generador", [])

        return {
            "estado": resultado["estado"],
            "total_franjas_requeridas": resultado["total_franjas_requeridas"],
            "alertas": alertas_totales, # AHORA MANDA AMBAS ALERTAS
            "estudiantes_sin_carga": sin_carga,
            "asignaciones": resultado["asignaciones"]
        }

    except ValueError as ve:
        # Aquí caerá el error si alguien se pasa de 18 créditos
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")