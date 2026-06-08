#!/usr/bin/env python3
"""Gera os gráficos do experimento a partir de data/runs.csv e data/steps.csv.

Gráficos gerados em ``charts/``:
  1. tempo total do pipeline por execução      -> 01_pipeline_duration_por_run.png
  2. tempo por job / etapa                      -> 02_tempo_por_job.png
                                                   02b_tempo_por_step.png
  3. taxa de sucesso x falha                    -> 03_taxa_sucesso_falha.png
  4. nº de testes x duração do pipeline         -> 04_testes_x_duracao.png

Uso:
    python scripts/visualize.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CHARTS = ROOT / "charts"


def load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    runs = pd.read_csv(DATA / "runs.csv")
    steps = pd.read_csv(DATA / "steps.csv")
    metrics = pd.read_csv(DATA / "metrics.csv")
    runs = runs.sort_values("run_number").reset_index(drop=True)
    return runs, steps, metrics


def chart_pipeline_duration(runs: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(11, 5))
    labels = runs["run_number"].astype(str)
    colors = ["#2ca02c" if s == "success" else "#d62728" for s in runs["status"]]
    ax.bar(labels, runs["workflow_duration"], color=colors)
    ax.set_title("1) Tempo total do pipeline por execução")
    ax.set_xlabel("run_number")
    ax.set_ylabel("duração total (s)")
    for i, v in enumerate(runs["workflow_duration"]):
        ax.text(i, v + 0.5, f"{v:.0f}", ha="center", va="bottom", fontsize=8)
    legend = [
        plt.Rectangle((0, 0), 1, 1, color="#2ca02c"),
        plt.Rectangle((0, 0), 1, 1, color="#d62728"),
    ]
    ax.legend(legend, ["success", "failure"])
    fig.tight_layout()
    fig.savefig(CHARTS / "01_pipeline_duration_por_run.png", dpi=130)
    plt.close(fig)


def chart_time_per_job(steps: pd.DataFrame) -> None:
    # Recupera job_duration a partir do maior step? Usamos metrics.csv via steps agregando.
    job_dur = (
        steps.groupby("job_name")["step_duration"].sum().sort_values(ascending=False)
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    job_dur.plot(kind="bar", ax=ax, color="#1f77b4")
    ax.set_title("2) Tempo médio acumulado por job (soma dos steps)")
    ax.set_xlabel("job")
    ax.set_ylabel("soma das durações dos steps (s)")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(CHARTS / "02_tempo_por_job.png", dpi=130)
    plt.close(fig)

    # Detalhe por step (média entre runs).
    step_dur = (
        steps.groupby("step_name")["step_duration"]
        .mean()
        .sort_values(ascending=False)
        .head(12)
    )
    fig, ax = plt.subplots(figsize=(10, 6))
    step_dur.iloc[::-1].plot(kind="barh", ax=ax, color="#ff7f0e")
    ax.set_title("2b) Tempo médio por etapa (top 12 steps)")
    ax.set_xlabel("duração média (s)")
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(CHARTS / "02b_tempo_por_step.png", dpi=130)
    plt.close(fig)


def chart_success_failure(runs: pd.DataFrame) -> None:
    counts = runs["status"].value_counts()
    fig, ax = plt.subplots(figsize=(6, 6))
    colors = {"success": "#2ca02c", "failure": "#d62728"}
    ax.pie(
        counts.values,
        labels=[f"{k} ({v})" for k, v in counts.items()],
        autopct="%1.1f%%",
        colors=[colors.get(k, "#7f7f7f") for k in counts.index],
        startangle=90,
    )
    ax.set_title("3) Taxa de sucesso x falha das execuções")
    fig.tight_layout()
    fig.savefig(CHARTS / "03_taxa_sucesso_falha.png", dpi=130)
    plt.close(fig)


def chart_tests_vs_duration(runs: pd.DataFrame) -> None:
    df = runs.dropna(subset=["test_count", "workflow_duration"]).copy()
    fig, ax = plt.subplots(figsize=(9, 6))
    for status, color in [("success", "#2ca02c"), ("failure", "#d62728")]:
        sub = df[df["status"] == status]
        ax.scatter(
            sub["test_count"],
            sub["workflow_duration"],
            c=color,
            label=status,
            s=70,
            edgecolors="black",
        )
    # linha de tendência
    if len(df) >= 2:
        import numpy as np

        coef = np.polyfit(df["test_count"], df["workflow_duration"], 1)
        xs = np.linspace(df["test_count"].min(), df["test_count"].max(), 50)
        ax.plot(xs, coef[0] * xs + coef[1], "--", color="#1f77b4",
                label=f"tendência (slope={coef[0]:.3f}s/teste)")
    ax.set_title("4) Quantidade de testes x duração do pipeline")
    ax.set_xlabel("quantidade de testes")
    ax.set_ylabel("duração total do pipeline (s)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHARTS / "04_testes_x_duracao.png", dpi=130)
    plt.close(fig)


def main() -> None:
    CHARTS.mkdir(parents=True, exist_ok=True)
    runs, steps, metrics = load()
    chart_pipeline_duration(runs)
    chart_time_per_job(steps)
    chart_success_failure(runs)
    chart_tests_vs_duration(runs)
    print(f"Gráficos salvos em {CHARTS}")


if __name__ == "__main__":
    main()
