from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as horarios_router

app = FastAPI(
    title="API de Horarios - Facultad de Ingeniería",
    description="Motor de asignación de horarios basado en teoría de grafos.",
    version="1.0.0"
)

# --- NUEVO: Configuración de CORS ---
# Esto permite que tu archivo index.html (frontend) pueda pedirle datos al servidor
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción se pone el dominio real, aquí permitimos todos para desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ------------------------------------

app.include_router(horarios_router, prefix="/api/v1/horarios", tags=["Horarios"])

@app.get("/")
def health_check():
    return {"mensaje": "El motor de asignación de horarios está en línea y funcionando."}