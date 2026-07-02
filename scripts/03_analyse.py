"""
03_analyse.py — Phase 3 analysis of the clean LATAM finance dataset.

Produces the 6 required analyses, each printed as a Markdown table:
  1. Cost of living vs income, by country
  2. Savings patterns by age group
  3. Industry benchmarks
  4. Financial satisfaction & savings by AI-tool usage
  5. Debt analysis for indebted respondents, by country
  6. Pearson correlation matrix of key numeric variables

Usage:
    python scripts/03_analyse.py
    python scripts/03_analyse.py path/to/clean.csv
"""

import sys
from pathlib import Path

import pandas as pd

# Emit UTF-8 so accented values (México, Tecnología) render correctly when the
# Markdown output is piped to a file or a UTF-8 terminal.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_IN = ROOT / "data" / "latam_finanzas_clean.csv"

EXPENSE_COLS = [
    "gasto_vivienda_usd",
    "gasto_alimentacion_usd",
    "gasto_transporte_usd",
    "gasto_entretenimiento_usd",
    "gasto_educacion_usd",
    "gasto_salud_usd",
]


def df_to_markdown(df, index_label=None, floatfmt="{:,.2f}"):
    """Render a DataFrame as a GitHub-flavored Markdown table (no deps)."""
    df = df.copy()

    def fmt(v):
        if isinstance(v, float):
            return floatfmt.format(v)
        return str(v)

    cols = list(df.columns)
    header = ([index_label or (df.index.name or "")] if index_label is not None
              or df.index.name is not None or not df.index.equals(pd.RangeIndex(len(df)))
              else [])
    show_index = bool(header)
    header = header + [str(c) for c in cols]

    lines = ["| " + " | ".join(header) + " |",
             "| " + " | ".join("---" for _ in header) + " |"]
    for idx, row in df.iterrows():
        cells = ([str(idx)] if show_index else []) + [fmt(row[c]) for c in cols]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def section(title):
    print(f"\n## {title}\n")


def main():
    in_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_IN
    if not in_path.exists():
        sys.exit(f"ERROR: input file not found: {in_path}")

    df = pd.read_csv(in_path)
    # Per-row total monthly expenses (all expense columns are complete).
    df["gasto_total_usd"] = df[EXPENSE_COLS].sum(axis=1)

    # --- 1. Cost of living vs income ---------------------------------------
    section("1. Cost of Living vs Income (by country)")
    g = df.groupby("pais")
    cost = pd.DataFrame({
        "avg_income_usd": g["ingreso_mensual_usd"].mean(),
        "avg_total_expenses_usd": g["gasto_total_usd"].mean(),
        # Savings rate = mean savings / mean income * 100.
        "savings_rate_pct": g["ahorro_mensual_usd"].mean() / g["ingreso_mensual_usd"].mean() * 100,
    }).sort_values("avg_income_usd", ascending=False)
    print(df_to_markdown(cost, index_label="pais"))

    # --- 2. Savings patterns by age ----------------------------------------
    section("2. Savings Patterns by Age Group")
    age_bins = [20, 25, 30, 35, float("inf")]
    age_labels = ["20-24", "25-29", "30-34", "35+"]
    df["grupo_edad"] = pd.cut(df["edad"], bins=age_bins, labels=age_labels, right=False)
    ag = df.groupby("grupo_edad", observed=True)["ahorro_mensual_usd"]
    age_tbl = pd.DataFrame({
        "n": ag.size(),
        "mean_savings_usd": ag.mean(),
        "median_savings_usd": ag.median(),
    })
    print(df_to_markdown(age_tbl, index_label="grupo_edad"))

    # --- 3. Industry benchmarks --------------------------------------------
    section("3. Industry Benchmarks")
    ig = df.groupby("industria")
    ind_tbl = pd.DataFrame({
        "n": ig.size(),
        "mean_income_usd": ig["ingreso_mensual_usd"].mean(),
        "mean_savings_usd": ig["ahorro_mensual_usd"].mean(),
        "pct_positive_savings": ig["ahorro_mensual_usd"].apply(lambda s: (s > 0).mean() * 100),
    }).sort_values("mean_income_usd", ascending=False)
    print(df_to_markdown(ind_tbl, index_label="industria"))

    # --- 4. Financial literacy & digital tools -----------------------------
    section("4. Satisfaction & Savings by AI-Tool Usage")
    ia_bins = [-1, 0, 3, 8, float("inf")]
    ia_labels = ["None (0)", "Low (1-3)", "Medium (4-8)", "High (9+)"]
    df["grupo_ia"] = pd.cut(df["horas_herramientas_ia_semana"], bins=ia_bins, labels=ia_labels)
    ia_g = df.groupby("grupo_ia", observed=True)
    ia_tbl = pd.DataFrame({
        "n": ia_g.size(),
        "avg_satisfaccion_financiera": ia_g["satisfaccion_financiera"].mean(),
        "avg_ahorro_mensual_usd": ia_g["ahorro_mensual_usd"].mean(),
    })
    print(df_to_markdown(ia_tbl, index_label="grupo_ia"))

    # --- 5. Debt analysis --------------------------------------------------
    section("5. Debt Analysis (respondents with tiene_deuda == 'Sí')")
    indebted = df[df["tiene_deuda"] == "Sí"]
    dg = indebted.groupby("pais")
    debt_tbl = pd.DataFrame({
        "n": dg.size(),
        "mean_debt_usd": dg["deuda_total_usd"].mean(),
        "mean_monthly_income_usd": dg["ingreso_mensual_usd"].mean(),
        # Debt-to-income = total debt / monthly income (times covered).
        "debt_to_income_ratio": dg["deuda_total_usd"].mean() / dg["ingreso_mensual_usd"].mean(),
    }).sort_values("debt_to_income_ratio", ascending=False)
    print(df_to_markdown(debt_tbl, index_label="pais"))
    print(f"\n> Note: `deuda_total_usd` was ~45% missing and left un-imputed in cleaning; "
          f"means above are over non-missing values only.")

    # --- 6. Correlation matrix ---------------------------------------------
    section("6. Pearson Correlation Matrix")
    corr_cols = {
        "Age": "edad",
        "Income": "ingreso_mensual_usd",
        "Total_Expenses": "gasto_total_usd",
        "IA_Hours": "horas_herramientas_ia_semana",
        "Fin_Satisfaction": "satisfaccion_financiera",
    }
    corr = df[list(corr_cols.values())].rename(columns={v: k for k, v in corr_cols.items()})
    corr_matrix = corr.corr(method="pearson")
    print(df_to_markdown(corr_matrix, index_label="", floatfmt="{:.3f}"))


if __name__ == "__main__":
    main()
