"""
04_visualise.py — Phase 4 visualizations of the clean LATAM finance dataset.

Generates 5 charts and saves them as PNGs into charts/:
  1. Income distribution by country       (box plot)
  2. Mean monthly savings by age group     (bar chart)
  3. Financial satisfaction by AI-tool use (grouped bar chart)
  4. Savings rate by industry              (sorted horizontal bar)
  5. Debt-to-income ratio by country       (bar chart, debt holders only)

Usage:
    python scripts/04_visualise.py
    python scripts/04_visualise.py path/to/clean.csv
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless: render straight to file, no display needed
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_IN = ROOT / "data" / "latam_finanzas_clean.csv"
CHARTS_DIR = ROOT / "charts"

EXPENSE_COLS = [
    "gasto_vivienda_usd", "gasto_alimentacion_usd", "gasto_transporte_usd",
    "gasto_entretenimiento_usd", "gasto_educacion_usd", "gasto_salud_usd",
]

PALETTE = "muted"
sns.set_theme(style="whitegrid", palette=PALETTE)
plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "figure.autolayout": True,
})


def save(fig, name):
    path = CHARTS_DIR / name
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {path}")


def main():
    in_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_IN
    if not in_path.exists():
        sys.exit(f"ERROR: input file not found: {in_path}")
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(in_path)
    df["gasto_total_usd"] = df[EXPENSE_COLS].sum(axis=1)

    # ------------------------------------------------------------------ 1
    # Income distribution by country (box plot), ordered by median income.
    order = (df.groupby("pais")["ingreso_mensual_usd"].median()
             .sort_values(ascending=False).index)
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.boxplot(data=df, x="pais", y="ingreso_mensual_usd", order=order, ax=ax)
    ax.set_title("Income Distribution by Country")
    ax.set_xlabel("Country")
    ax.set_ylabel("Monthly income (USD)")
    ax.tick_params(axis="x", rotation=20)
    save(fig, "01_income_by_country.png")

    # ------------------------------------------------------------------ 2
    # Mean monthly savings by age group (bar chart).
    age_bins = [20, 25, 30, 35, float("inf")]
    age_labels = ["20-24", "25-29", "30-34", "35+"]
    df["grupo_edad"] = pd.cut(df["edad"], bins=age_bins, labels=age_labels, right=False)
    age_savings = df.groupby("grupo_edad", observed=True)["ahorro_mensual_usd"].mean()
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.barplot(x=age_savings.index, y=age_savings.values, ax=ax,
                hue=age_savings.index, legend=False)
    ax.set_title("Mean Monthly Savings by Age Group")
    ax.set_xlabel("Age group")
    ax.set_ylabel("Mean monthly savings (USD)")
    for i, v in enumerate(age_savings.values):
        ax.text(i, v, f"${v:,.0f}", ha="center", va="bottom", fontsize=9)
    save(fig, "02_savings_by_age.png")

    # ------------------------------------------------------------------ 3
    # Financial satisfaction by AI-tool usage (grouped bar chart).
    ia_bins = [-1, 0, 3, 8, float("inf")]
    ia_labels = ["None (0)", "Low (1-3)", "Medium (4-8)", "High (9+)"]
    df["grupo_ia"] = pd.cut(df["horas_herramientas_ia_semana"], bins=ia_bins, labels=ia_labels)
    ia_sat = df.groupby("grupo_ia", observed=True)["satisfaccion_financiera"].mean()
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.barplot(x=ia_sat.index, y=ia_sat.values, ax=ax,
                hue=ia_sat.index, legend=False)
    ax.set_title("Financial Satisfaction by AI-Tool Usage")
    ax.set_xlabel("Weekly hours using AI tools")
    ax.set_ylabel("Mean financial satisfaction (1-10)")
    ax.set_ylim(0, 10)
    for i, v in enumerate(ia_sat.values):
        ax.text(i, v, f"{v:.2f}", ha="center", va="bottom", fontsize=9)
    save(fig, "03_satisfaction_by_ai_usage.png")

    # ------------------------------------------------------------------ 4
    # Savings rate by industry (sorted horizontal bar).
    ig = df.groupby("industria")
    savings_rate = (ig["ahorro_mensual_usd"].mean() / ig["ingreso_mensual_usd"].mean() * 100)
    savings_rate = savings_rate.sort_values(ascending=True)  # ascending -> largest on top in barh
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.barplot(x=savings_rate.values, y=savings_rate.index, ax=ax,
                hue=savings_rate.index, legend=False, orient="h")
    ax.set_title("Savings Rate by Industry")
    ax.set_xlabel("Savings rate (% of income)")
    ax.set_ylabel("Industry")
    for i, v in enumerate(savings_rate.values):
        ax.text(v, i, f" {v:.1f}%", va="center", fontsize=9)
    save(fig, "04_savings_rate_by_industry.png")

    # ------------------------------------------------------------------ 5
    # Debt-to-income ratio by country, debt holders only (bar chart).
    indebted = df[df["tiene_deuda"] == "Sí"]
    dg = indebted.groupby("pais")
    dti = (dg["deuda_total_usd"].mean() / dg["ingreso_mensual_usd"].mean()).sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.barplot(x=dti.index, y=dti.values, ax=ax, hue=dti.index, legend=False)
    ax.set_title("Debt-to-Income Ratio by Country (Debt Holders)")
    ax.set_xlabel("Country")
    ax.set_ylabel("Total debt / monthly income (×)")
    ax.tick_params(axis="x", rotation=20)
    for i, v in enumerate(dti.values):
        ax.text(i, v, f"{v:.2f}×", ha="center", va="bottom", fontsize=9)
    save(fig, "05_debt_to_income_by_country.png")


if __name__ == "__main__":
    print("Generating charts...")
    main()
    print("Done.")
