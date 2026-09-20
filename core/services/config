"""
Configuración central del modelo de franjas horarias.

Antes, "6 franjas por día" y "36 franjas totales" estaban hardcodeados por
separado en schedule_generator.py y en optimizacion_traslados.py. Si cambiabas
uno sin el otro, la detección de traslados entre sedes (que depende de saber
cuántas franjas hay por día para calcular divmod(color, franjas_por_dia))
quedaba desincronizada con el límite físico real. Este módulo es la única
fuente de verdad para ambos.

Los valores por defecto reproducen el demo original (100 estudiantes):
6 días x 6 franjas/día = 36. Para una simulación a escala real, usa
franjas_por_dia y dias_habiles calculados a partir del horario real de la
universidad (ver experimentos/run_benchmark.py).
"""

DIAS_HABILES_POR_SEMANA_DEFECTO = 6   # Lunes a Sábado
FRANJAS_POR_DIA_DEFECTO = 6           # valor del demo original (banco de pruebas de 100 estudiantes)
MAX_FRANJAS_FISICAS_DEFECTO = DIAS_HABILES_POR_SEMANA_DEFECTO * FRANJAS_POR_DIA_DEFECTO  # 36
