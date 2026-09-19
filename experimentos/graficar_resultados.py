"""
Genera las gráficas de escalabilidad a partir de experimentos/resultados_benchmark.csv.

Uso:
    python experimentos/graficar_resultados.py
    python experimentos/graficar_resultados.py --csv otra_ruta.csv --salida otra_carpeta/
"""

from __future__ import annotations
import argparse
import os

import pandas as pd
import matplotlib.pyplot as plt


def _cargar(ruta_csv: str) -> pd.DataFrame:
    df = pd.read_csv(ruta_csv)
    # Filas que fallaron no tienen métricas numéricas; las dejamos fuera de las gráficas
    # pero se reportan aparte para que no se pierdan silenciosamente.
    fallidas = df[df["estado"] != "ok"]
    if not fallidas.empty:
        print("Filas con errores (excluidas de las gráficas):")
        print(fallidas[["num_estudiantes", "modo", "estado"]].to_string(index=False))
    return df[df["estado"] == "ok"].copy()


def graficar_tiempo_total(df: pd.DataFrame, carpeta_salida: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    for modo, grupo in df.groupby("modo"):
        grupo = grupo.sort_values("num_estudiantes")
        ax.plot(grupo["num_estudiantes"], grupo["tiempo_total_s"], marker="o", label=modo)
    ax.set_xlabel("Número de estudiantes")
    ax.set_ylabel("Tiempo total de ejecución (s)")
    ax.set_title("Escalabilidad: tiempo total vs. tamaño del problema")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(carpeta_salida, "01_tiempo_total_vs_escala.png"), dpi=150)
    plt.close(fig)


def graficar_tiempo_por_etapa(df: pd.DataFrame, carpeta_salida: str) -> None:
    propuesta = df[df["modo"] == "propuesta"].sort_values("num_estudiantes")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(propuesta["num_estudiantes"], propuesta["tiempo_matching_s"], marker="o", label="Matching (Fase 1)")
    ax.plot(propuesta["num_estudiantes"], propuesta["tiempo_coloreo_s"], marker="o", label="Coloreo DSatur (Fase 2)")
    ax.plot(propuesta["num_estudiantes"], propuesta["tiempo_refinamiento_s"], marker="o", label="Refinamiento de sede")
    ax.set_xlabel("Número de estudiantes")
    ax.set_ylabel("Tiempo (s)")
    ax.set_title("Modo propuesta: tiempo por etapa del pipeline")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(carpeta_salida, "02_tiempo_por_etapa.png"), dpi=150)
    plt.close(fig)


def graficar_reduccion_traslados(df: pd.DataFrame, carpeta_salida: str) -> None:
    propuesta = df[df["modo"] == "propuesta"].sort_values("num_estudiantes")
    fig, ax1 = plt.subplots(figsize=(8, 5))

    ax1.plot(propuesta["num_estudiantes"], propuesta["traslados_antes"], marker="o", label="Traslados antes (sin refinar)")
    ax1.plot(propuesta["num_estudiantes"], propuesta["traslados_despues"], marker="o", label="Traslados después (refinado)")
    ax1.set_xlabel("Número de estudiantes")
    ax1.set_ylabel("Traslados entre sedes (conteo)")
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(propuesta["num_estudiantes"], propuesta["reduccion_traslados_pct"], marker="s", color="green", linestyle="--", label="% de reducción")
    ax2.set_ylabel("% de reducción")
    ax2.legend(loc="upper right")

    ax1.set_title("Efecto del refinamiento de sede vs. tamaño del problema")
    fig.tight_layout()
    fig.savefig(os.path.join(carpeta_salida, "03_reduccion_traslados_vs_escala.png"), dpi=150)
    plt.close(fig)


def graficar_violaciones_veto(df: pd.DataFrame, carpeta_salida: str) -> None:
    tabla = df.pivot_table(index="num_estudiantes", columns="modo", values="violaciones_veto")
    fig, ax = plt.subplots(figsize=(8, 5))
    tabla.plot(kind="bar", ax=ax)
    ax.set_xlabel("Número de estudiantes")
    ax.set_ylabel("Estudiantes que ven con un profesor vetado")
    ax.set_title("Violaciones de veto: baseline vs. propuesta")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(carpeta_salida, "04_violaciones_veto_baseline_vs_propuesta.png"), dpi=150)
    plt.close(fig)


def graficar_franjas_requeridas(df: pd.DataFrame, carpeta_salida: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    for modo, grupo in df.groupby("modo"):
        grupo = grupo.sort_values("num_estudiantes")
        ax.plot(grupo["num_estudiantes"], grupo["franjas_requeridas"], marker="o", label=modo)
    ax.axhline(36, color="red", linestyle="--", label="Límite físico (36 franjas)")
    ax.set_xlabel("Número de estudiantes")
    ax.set_ylabel("Franjas horarias requeridas (χ(G₂))")
    ax.set_title("Franjas requeridas vs. tamaño del problema")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(carpeta_salida, "05_franjas_requeridas_vs_escala.png"), dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Genera las gráficas de escalabilidad del benchmark UCTP.")
    parser.add_argument("--csv", type=str,
                         default=os.path.join(os.path.dirname(__file__), "resultados_benchmark.csv"))
    parser.add_argument("--salida", type=str,
                         default=os.path.join(os.path.dirname(__file__), "graficas"))
    args = parser.parse_args()

    os.makedirs(args.salida, exist_ok=True)
    df = _cargar(args.csv)

    if df.empty:
        print("No hay filas exitosas para graficar.")
        return

    graficar_tiempo_total(df, args.salida)
    graficar_tiempo_por_etapa(df, args.salida)
    graficar_reduccion_traslados(df, args.salida)
    graficar_violaciones_veto(df, args.salida)
    graficar_franjas_requeridas(df, args.salida)

    print(f"Gráficas guardadas en: {args.salida}")


if __name__ == "__main__":
    main()
