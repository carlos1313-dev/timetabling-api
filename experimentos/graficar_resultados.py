"""
Genera las gráficas de escalabilidad a partir de experimentos/resultados_benchmark.csv.

Si el CSV tiene varias semillas por escala, cada punto de las gráficas es el
PROMEDIO entre semillas, con barras de error mostrando la desviación estándar
-- así una sola corrida con datos "raros" no distorsiona la curva.

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
    fallidas = df[df["estado"] != "ok"]
    if not fallidas.empty:
        print("Filas con errores (excluidas de las gráficas):")
        print(fallidas[["num_estudiantes", "semilla", "modo", "estado"]].to_string(index=False))
    return df[df["estado"] == "ok"].copy()


def _agregar(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    """Promedio y desviación estándar de `columna`, agrupado por (num_estudiantes, modo)."""
    agregado = df.groupby(["num_estudiantes", "modo"])[columna].agg(["mean", "std"]).reset_index()
    agregado["std"] = agregado["std"].fillna(0.0)  # una sola semilla -> std=0, no NaN
    return agregado


def graficar_tiempo_total(df: pd.DataFrame, carpeta_salida: str) -> None:
    agregado = _agregar(df, "tiempo_total_s")
    fig, ax = plt.subplots(figsize=(8, 5))
    for modo, grupo in agregado.groupby("modo"):
        grupo = grupo.sort_values("num_estudiantes")
        ax.errorbar(grupo["num_estudiantes"], grupo["mean"], yerr=grupo["std"], marker="o", capsize=3, label=modo)
    ax.set_xlabel("Número de estudiantes")
    ax.set_ylabel("Tiempo total de ejecución (s)")
    ax.set_title("Escalabilidad: tiempo total vs. tamaño del problema")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(carpeta_salida, "01_tiempo_total_vs_escala.png"), dpi=150)
    plt.close(fig)


def graficar_tiempo_por_etapa(df: pd.DataFrame, carpeta_salida: str) -> None:
    propuesta = df[df["modo"] == "propuesta"]
    fig, ax = plt.subplots(figsize=(8, 5))
    for columna, etiqueta in [
        ("tiempo_matching_s", "Matching (Fase 1)"),
        ("tiempo_coloreo_s", "Coloreo DSatur (Fase 2)"),
        ("tiempo_refinamiento_s", "Refinamiento de sede"),
    ]:
        agregado = propuesta.groupby("num_estudiantes")[columna].agg(["mean", "std"]).reset_index()
        agregado["std"] = agregado["std"].fillna(0.0)
        agregado = agregado.sort_values("num_estudiantes")
        ax.errorbar(agregado["num_estudiantes"], agregado["mean"], yerr=agregado["std"], marker="o", capsize=3, label=etiqueta)
    ax.set_xlabel("Número de estudiantes")
    ax.set_ylabel("Tiempo (s)")
    ax.set_title("Modo propuesta: tiempo por etapa del pipeline")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(carpeta_salida, "02_tiempo_por_etapa.png"), dpi=150)
    plt.close(fig)


def graficar_reduccion_traslados(df: pd.DataFrame, carpeta_salida: str) -> None:
    propuesta = df[df["modo"] == "propuesta"]
    antes = propuesta.groupby("num_estudiantes")["traslados_antes"].agg(["mean", "std"]).reset_index().sort_values("num_estudiantes")
    despues = propuesta.groupby("num_estudiantes")["traslados_despues"].agg(["mean", "std"]).reset_index().sort_values("num_estudiantes")
    pct = propuesta.groupby("num_estudiantes")["reduccion_traslados_pct"].agg(["mean", "std"]).reset_index().sort_values("num_estudiantes")

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.errorbar(antes["num_estudiantes"], antes["mean"], yerr=antes["std"].fillna(0), marker="o", capsize=3, label="Traslados antes (sin refinar)")
    ax1.errorbar(despues["num_estudiantes"], despues["mean"], yerr=despues["std"].fillna(0), marker="o", capsize=3, label="Traslados después (refinado)")
    ax1.set_xlabel("Número de estudiantes")
    ax1.set_ylabel("Traslados entre sedes (conteo)")
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.errorbar(pct["num_estudiantes"], pct["mean"], yerr=pct["std"].fillna(0), marker="s", color="green", linestyle="--", capsize=3, label="% de reducción")
    ax2.set_ylabel("% de reducción")
    ax2.legend(loc="upper right")

    ax1.set_title("Efecto del refinamiento de sede vs. tamaño del problema")
    fig.tight_layout()
    fig.savefig(os.path.join(carpeta_salida, "03_reduccion_traslados_vs_escala.png"), dpi=150)
    plt.close(fig)


def graficar_violaciones_veto(df: pd.DataFrame, carpeta_salida: str) -> None:
    agregado = _agregar(df, "violaciones_veto")
    tabla_media = agregado.pivot(index="num_estudiantes", columns="modo", values="mean")
    fig, ax = plt.subplots(figsize=(8, 5))
    tabla_media.plot(kind="bar", ax=ax)
    ax.set_xlabel("Número de estudiantes")
    ax.set_ylabel("Estudiantes que ven con un profesor vetado (promedio)")
    ax.set_title("Violaciones de veto: DSatur sin restricciones vs. Welsh-Powell vs. propuesta")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(carpeta_salida, "04_violaciones_veto_comparativo.png"), dpi=150)
    plt.close(fig)


def graficar_franjas_requeridas(df: pd.DataFrame, carpeta_salida: str) -> None:
    agregado = _agregar(df, "franjas_requeridas")
    fig, ax = plt.subplots(figsize=(8, 5))
    for modo, grupo in agregado.groupby("modo"):
        grupo = grupo.sort_values("num_estudiantes")
        ax.errorbar(grupo["num_estudiantes"], grupo["mean"], yerr=grupo["std"], marker="o", capsize=3, label=modo)

    if "hmax_utilizado" in df.columns and not df["hmax_utilizado"].isna().all():
        hmax = df["hmax_utilizado"].dropna().iloc[0]
        ax.axhline(hmax, color="red", linestyle="--", label=f"Hmax utilizado ({int(hmax)})")

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
