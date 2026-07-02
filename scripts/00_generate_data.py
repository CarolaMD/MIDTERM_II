"""
00_generate_data.py — Generate a SYNTHETIC test dataset.

This is NOT real survey data. It produces 500 fake rows of "young professional"
finance responses with data-quality issues deliberately baked in, so the
exploration (01) and cleaning (02) scripts can be tested end to end:

  * 'industria' contains messy variants (casing, abbreviations, whitespace,
    accents) that map onto the canonical labels used in 02_clean.py.
  * Numeric columns have missing values at varied rates, including one column
    above the 40% "leave it" threshold.
  * 'ahorro_mensual_usd' contains valid negative values (spending > earning).

Deterministic: uses a fixed seed so re-runs produce the identical file.

Usage:
    python scripts/00_generate_data.py
    python scripts/00_generate_data.py path/to/output.csv
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "data" / "latam_finanzas_2025.csv"

N = 500
SEED = 42

PAISES = ["México", "Colombia", "Argentina", "Chile", "Perú", "Brasil"]
OCUPACIONES = [
    "Ingeniero/a", "Analista", "Diseñador/a", "Gerente",
    "Contador/a", "Docente", "Médico/a", "Emprendedor/a",
]
METAS = [
    "Comprar casa", "Ahorrar para retiro", "Pagar deudas",
    "Viajar", "Iniciar negocio", "Fondo de emergencia",
]
SI_NO = ["Sí", "No"]

# Messy industry variants -> the canonical labels 02_clean.py normalizes to.
# Each canonical bucket lists several raw spellings that appear in the file.
INDUSTRY_VARIANTS = {
    "Tecnología": ["Tecnología", "tecnologia", "TEC", "ti", "IT", "Tech", " tecnologia "],
    "Finanzas": ["Finanzas", "finanzas", "FINANZAS", "Banca", "financiero"],
    "Salud": ["Salud", "salud", "SALUD", "sanidad"],
    "Educación": ["Educación", "educacion", "EDU", "Educacion "],
    "Manufactura": ["Manufactura", "manufactura", "Manufacturing"],
    "Comercio": ["Comercio", "retail", "Ventas", "comercio"],
    "Gobierno": ["Gobierno", "sector publico"],
}


def main():
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    rng = np.random.default_rng(SEED)

    # Base numeric fields.
    edad = rng.integers(22, 41, size=N)
    ingreso = np.round(rng.normal(1800, 700, size=N).clip(300, 8000), 2)
    # Savings can be negative (spending > earning); centered low relative to income.
    ahorro = np.round(rng.normal(250, 400, size=N), 2)
    deuda = np.round(rng.gamma(2.0, 2500, size=N), 2)

    # Monthly expense breakdown (USD). Scaled loosely to income so totals are
    # plausible relative to earnings.
    gasto_vivienda = np.round((ingreso * 0.30 + rng.normal(0, 120, N)).clip(50), 2)
    gasto_alimentacion = np.round((ingreso * 0.15 + rng.normal(0, 60, N)).clip(30), 2)
    gasto_transporte = np.round((ingreso * 0.08 + rng.normal(0, 40, N)).clip(10), 2)
    gasto_entretenimiento = np.round((ingreso * 0.06 + rng.normal(0, 40, N)).clip(0), 2)
    gasto_educacion = np.round((ingreso * 0.05 + rng.normal(0, 60, N)).clip(0), 2)
    gasto_salud = np.round((ingreso * 0.05 + rng.normal(0, 40, N)).clip(0), 2)

    # Financial satisfaction: 1-10 Likert, loosely rising with savings.
    sat = 5.5 + (ahorro / 400) + rng.normal(0, 1.5, N)
    satisfaccion_financiera = np.clip(np.round(sat), 1, 10)

    # Weekly hours using AI tools: many zeros, a long low tail, few heavy users.
    horas_ia = rng.poisson(3, size=N).clip(0, 20)

    # Categorical fields.
    flat_variants = [v for group in INDUSTRY_VARIANTS.values() for v in group]
    industria = rng.choice(flat_variants, size=N)

    df = pd.DataFrame({
        "id": np.arange(1, N + 1),
        "edad": edad,
        "pais": rng.choice(PAISES, size=N),
        "industria": industria,
        "ocupacion": rng.choice(OCUPACIONES, size=N),
        "ingreso_mensual_usd": ingreso,
        "ahorro_mensual_usd": ahorro,
        "deuda_total_usd": deuda,
        "gasto_vivienda_usd": gasto_vivienda,
        "gasto_alimentacion_usd": gasto_alimentacion,
        "gasto_transporte_usd": gasto_transporte,
        "gasto_entretenimiento_usd": gasto_entretenimiento,
        "gasto_educacion_usd": gasto_educacion,
        "gasto_salud_usd": gasto_salud,
        "satisfaccion_financiera": satisfaccion_financiera,
        "horas_herramientas_ia_semana": horas_ia,
        "meta_financiera": rng.choice(METAS, size=N),
        "tiene_tarjeta_credito": rng.choice(SI_NO, size=N),
        "tiene_cuenta_ahorro": rng.choice(SI_NO, size=N),
        "tiene_deuda": rng.choice(SI_NO, size=N),
    })

    # Inject missing values at varied rates into numeric columns.
    #   edad ~5%, ingreso ~8%, ahorro ~15%, deuda ~45% (over the 40% threshold).
    def blank(col, frac):
        idx = rng.choice(N, size=int(N * frac), replace=False)
        df.loc[idx, col] = np.nan

    blank("edad", 0.05)
    blank("ingreso_mensual_usd", 0.08)
    blank("ahorro_mensual_usd", 0.15)
    blank("deuda_total_usd", 0.45)
    blank("satisfaccion_financiera", 0.06)
    blank("horas_herramientas_ia_semana", 0.04)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    n_neg = int((df["ahorro_mensual_usd"] < 0).sum())
    print(f"Wrote {len(df)} synthetic rows to {out_path}")
    print(f"  industria raw variants: {len(flat_variants)}")
    print(f"  negative ahorro_mensual_usd: {n_neg}")
    print(f"  missing per numeric col:")
    for c in ["edad", "ingreso_mensual_usd", "ahorro_mensual_usd", "deuda_total_usd"]:
        print(f"    {c:<22} {int(df[c].isna().sum())}")


if __name__ == "__main__":
    main()
