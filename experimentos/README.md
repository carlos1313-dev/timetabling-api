# Módulo `experimentos/` — Benchmark de escalabilidad UCTP

## ¿Para qué existe esto?

El resto del proyecto (`core/`, `api/`) resuelve UN horario a la vez, para UN
dataset fijo (`infrastructure/dataset/facultad_data.json`). Este módulo existe
para responder una pregunta distinta: **¿qué tan bien se comporta el sistema a
medida que crece el número de estudiantes, y cuánto aportan realmente las
restricciones propuestas (veto docente + minimización de traslados entre
sedes) frente a un UCTP genérico que no las considera?**

Es el soporte experimental del artículo de investigación del proyecto, no
código de producción — no lo importa `api/routes.py` ni el frontend.

## Piezas del módulo

| Archivo | Qué hace |
|---|---|
| `generador_dataset.py` | Genera un dataset sintético de CUALQUIER tamaño (`generar_dataset(num_estudiantes)`), manteniendo las proporciones reales aproximadas de la universidad (materias, profesores, vetos y reparto de sedes por estudiante). No escribe a disco. |
| `hidratar.py` | Convierte el dict que produce el generador en las entidades de dominio (`Profesor`, `Grupo`, `HistorialReprobacion`) directamente en memoria — es la misma lógica de `FacultadJSONRepository`, pero sin pasar por un archivo JSON. |
| `run_benchmark.py` | El runner: para cada escala, genera un dataset y corre el pipeline completo dos veces — modo `baseline` (sin veto, sin refinamiento de sede) y modo `propuesta` (comportamiento actual completo) — midiendo tiempos y violaciones. Escribe todo a `resultados_benchmark.csv`. |
| `graficar_resultados.py` | Lee ese CSV y genera 5 gráficas PNG en `graficas/`. |
| `resultados_benchmark.csv` | La salida más reciente del benchmark. Se sobrescribe cada vez que corres `run_benchmark.py` (o usa `--salida` para no perder una corrida anterior). |

## Cómo correrlo

```bash
# Desde la raíz del repo (importa módulos de core/, necesita estar ahí):
python experimentos/run_benchmark.py
python experimentos/graficar_resultados.py
```

### ¿El `--escalas` acepta cualquier número de valores y cualquier tamaño?

Sí a ambas. `--escalas` es una lista de longitud libre — puedes pasar 2 valores
o 20:

```bash
python experimentos/run_benchmark.py --escalas 30 60 90
python experimentos/run_benchmark.py --escalas 10 20 30 40 50 75 100 150 200 300 500 750 1000
```

Cada número es un tamaño de estudiantes independiente; el script genera un
dataset nuevo para cada uno. No hay límite superior impuesto por el código,
solo por cuánto tiempo estés dispuesto a esperar (los tiempos de cada
combinación se ven en consola mientras corre). El techo real de la
universidad (5000) no está en la lista por defecto porque tarda varios
minutos — se agrega explícitamente con `--incluir-techo`.

Si no pasas `--escalas`, usa la lista por defecto definida en
`ESCALAS_ESTUDIANTES_DEFECTO` dentro de `run_benchmark.py`.

## Dónde ver los resultados

- **El CSV** (`experimentos/resultados_benchmark.csv`) se abre con cualquier
  hoja de cálculo (Excel, Google Sheets, LibreOffice Calc) o con `pandas` en
  un notebook. Una fila por combinación (escala × modo). Las columnas clave:
  `traslados_antes`/`traslados_despues` (efecto del refinamiento de sede),
  `violaciones_veto` (comparar baseline vs. propuesta), `franjas_requeridas`
  y `excede_limite_36_franjas` (factibilidad de infraestructura), y las
  columnas `tiempo_*_s` (factibilidad computacional por etapa).
- **Las gráficas** (`experimentos/graficas/*.png`) son la versión visual de
  esas mismas columnas, listas para pegar en el artículo.

## Cosas a tener en cuenta antes de confiar ciegamente en los números

- Cada escala usa una **única semilla fija** (`SEMILLA_DATASET = 42` en
  `run_benchmark.py`). Eso hace las corridas reproducibles, pero significa
  que cada número del CSV viene de UN dataset sintético, no de un promedio de
  varios. Para resultados con significancia estadística real, habría que
  correr cada escala con varias semillas y reportar promedio ± desviación.
- El generador **no respeta la estructura curricular por niveles**: inscribe
  materias a cada estudiante sin preferencia por su semestre, lo que infla
  artificialmente los conflictos comparado con una universidad real.
  Esto afecta sobre todo la columna `franjas_requeridas`.
