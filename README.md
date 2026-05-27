# 🎓 ERP Académico: Optimización de Horarios mediante Teoría de Grafos
**Universidad Distrital Francisco José de Caldas - Facultad de Ingeniería** **Proyecto Curricular de Ingeniería de Sistemas**

---

## 📝 Planteamiento del Problema
El problema de asignación de horarios universitarios (*University Timetabling Problem*) es un desafío clásico de optimización combinatoria (NP-Hard). En la Facultad de Ingeniería, este problema se agrava por el alto volumen de estudiantes, los cruces de mallas curriculares y las limitaciones de infraestructura física. 

Este proyecto modela y resuelve esta problemática construyendo un motor de asignación basado en grafos que garantiza horarios sin cruces, y además resuelve **tres restricciones críticas de la vida real**:
1. **Idoneidad Docente (Skill-Based Matching):** Un profesor de Programación no puede ser asignado a una clase de Ciencias Básicas.
2. **Restricción de Repitentes (Vetos):** Si un estudiante reprobó, el sistema debe evitar reasignarlo con el mismo docente para garantizar equidad académica.
3. **Limitación de Infraestructura:** La facultad solo cuenta con 36 franjas físicas disponibles a la semana (Lunes a Sábado).

## 🧠 Modelado Matemático y Algoritmos de Grafos
El núcleo de este sistema está construido sobre dos familias distintas de algoritmos de optimización de grafos, separados en dos fases de ejecución:

### Fase 1: Asignación Docente (Emparejamiento Máximo Bipartito)
El motor de asignación modela el problema como un grafo bipartito $G = (U, V, E)$, donde:
* **Conjunto $U$:** Nodos que representan a los Profesores.
* **Conjunto $V$:** Nodos que representan a los Grupos/Materias.
* **Aristas ($E$):** Una conexión existe si y solo si se cumplen dos validaciones:
  1. El área de conocimiento de la materia está dentro de las áreas habilitadas del profesor (*Hard Constraint*).
  2. La intersección de conjuntos $\mathcal{O}(1)$ entre el historial de vetos y los alumnos matriculados es vacía.

**Algoritmo implementado:** Se utiliza **Búsqueda en Profundidad (DFS)** para encontrar rutas aumentantes (*Augmenting Paths*) y lograr el Emparejamiento Máximo, reasignando dinámicamente a la planta docente sin violar las reglas.

### Fase 2: Construcción de Horarios (Coloración de Vértices)
Una vez emparejados los docentes, el sistema aplica el **Patrón de Expansión de Nodos**. Una materia de 3 créditos se divide dinámicamente en 3 nodos independientes (Clase 1, 2 y 3).
* **Nodos:** Sesiones de clase individuales.
* **Aristas (Conflictos):** Se dibuja una arista bajo el **Patrón Strategy** si dos sesiones: tienen el mismo profesor, pertenecen al mismo semestre (malla), tienen alumnos cruzados, o son sesiones del mismo grupo.

**Algoritmo implementado:** Se aplica el algoritmo heurístico **DSatur (Degree of Saturation)** para realizar el coloreo del grafo. El "color" representa una de las 36 franjas horarias disponibles. DSatur garantiza la minimización de franjas, asegurando que nodos adyacentes (con conflictos) jamás se programen a la misma hora. *(Se incluye Welsh-Powell como estrategia de comparación secundaria)*.

---

## 🚀 Características de Nivel Empresarial (ERP)
Más allá de los grafos, el sistema incluye validaciones de calidad de software:
* **Fail-Fast de Créditos:** El sistema suma la carga de cada estudiante e interrumpe la ejecución (HTTP 400) si alguien supera el límite reglamentario de 18 créditos.
* **Control de Carga Física:** Si DSatur determina que la densidad del grafo exige más de 36 franjas (colores), se rechaza la programación excedente y se levanta una *Alerta de Decanatura* por falta de infraestructura.
* **Alertas de Escasez Docente:** Relajación de restricciones (*Soft Constraints*) si matemáticamente no hay suficientes profesores idóneos, levantando alertas preventivas.
* **Vistas Filtradas (UI):** Interfaz desacoplada que permite buscar la matriz de horarios unificada por profesor o por estudiante, mostrando sus compañeros de clase inscritos.
* **Reporte de Anomalías:** Identificación de estudiantes matriculados en el catálogo que quedaron sin carga académica asignada.

---

## 🏗️ Arquitectura del Software (Clean Architecture)
Construido como un monolito modular bajo principios SOLID, garantizando el aislamiento puro de la lógica matemática.

```text
timetabling_api/
├── core/                        # Dominio Matemático y Reglas de Negocio
│   ├── entities.py              # Materia, Profesor, SesionGrupo, Estudiante
│   ├── algorithms/              # Núcleo de Teoría de Grafos (DFS Bipartito, DSatur)
│   ├── rules/                   # Estrategias de aristas de conflicto
│   └── services/                # Validadores, Expansores de nodos y Orquestadores
├── infrastructure/              # Persistencia
│   └── dataset/
│       └── facultad_data.json   # Data Seeder (100 estudiantes, 10 profesores)
├── api/                         # Presentación REST API (FastAPI)
└── frontend/                    # Single Page Application (Dashboard Interactivo)
└── README.md                    # Documentación del proyecto   
```

## Requisitos de Instalación

* **Python 3.8** o superior.
* Un navegador web moderno (Chrome, Edge, Firefox).

## Instrucciones de Ejecución Paso a Paso

### 1. Clonar el repositorio

Descargue o clone el repositorio en su máquina local. Abra una terminal en la carpeta raíz del proyecto (`timetabling`).

### 2. Instalar las dependencias

El backend utiliza FastAPI por su alto rendimiento y manejo asíncrono. Ejecute el siguiente comando para instalar las librerías necesarias:

```bash
pip install fastapi uvicorn pydantic

```
### OPCIONAL

Generar un nuevo escenario de estrés masivo aleatorio ejecutando el seeder:
```bash
python seed_data.py
```

### 3. Levantar el Servidor Backend

Inicie la API ejecutando Uvicorn. El servidor quedará escuchando en el puerto 8000.

```bash
uvicorn api.main:app --reload

```

*(Para verificar que el backend funciona correctamente, puede visitar la documentación interactiva Swagger en: `http://127.0.0.1:8000/docs`)*

### 4. Ejecutar la Interfaz de Usuario (Frontend)

Dado que el frontend está desacoplado, no requiere un servidor web adicional. Simplemente diríjase a la carpeta `frontend/` y abra el archivo `index.html` haciendo doble clic sobre él en su navegador.

Haga clic en el botón **"Generar Horarios Óptimos"** para ver la ejecución del algoritmo en tiempo real.

## 🧪 Cómo evaluar los escenarios de prueba

Los datos académicos (profesores, materias, estudiantes, historiales) no están quemados en el código. El sistema lee directamente el archivo de infraestructura.

Para evaluar los diferentes escenarios y la reacción del algoritmo DSatur, modifique el archivo:
`infrastructure/dataset/facultad_data.json`

* **Escenario 1 (Flujo Ideal):** Elimine los registros del bloque `historial_reprobacion` y verifique la asignación limpia.
* **Escenario 2 (Intersección de estudiantes):** Agregue el mismo ID de estudiante a grupos de diferentes semestres. El algoritmo los separará en colores (franjas) distintos.
* **Escenario 3 (Escasez Docente):** Elimine profesores del catálogo `profesores` dejando solo uno que esté vetado en el `historial_reprobacion`. El frontend mostrará una *Alerta Académica*.

## 👨‍💻 Autores

* **Sergio Nicolás Osorio Guevara Codigo 20241020073**
* **Silvana Martínez Pardo. Código: 20241020010**
* **Arley Santiago Alvarez Ortiz. Código: 20241020008**
* **Laura Sofia Cuadros Niño. 20222020160**
* **Emmanuel Guerrero Piza: 20202020039**

---