"""
02_clean.py — Clean the LATAM finance survey dataset.

Steps:
  1. Standardize the 'industria' column (spelling / casing / abbreviation variants).
     Prints unique values BEFORE and AFTER.
  2. Report % missing for each numeric column, apply a per-column recommendation
     (median-fill / drop / leave).
  3. Flag negative 'ahorro_mensual_usd' values in a new boolean column
     'ahorro_negativo' (does NOT remove them).
  4. Save the clean dataset to data/latam_finanzas_clean.csv
  5. Print a summary of changes.

Usage:
    python scripts/02_clean.py
    python scripts/02_clean.py path/to/input.csv path/to/output.csv
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_IN = ROOT / "data" / "latam_finanzas_2025.csv"
DEFAULT_OUT = ROOT / "data" / "latam_finanzas_clean.csv"

# ---------------------------------------------------------------------------
# Industry standardization.
#
# NOTE: this mapping MUST be verified against the real unique values in the
# file (run 01_explore.py first). The keys are the *normalized* form of a raw
# value (lowercased, stripped, internal whitespace collapsed); the values are
# the canonical label to use. Anything not in the map keeps its normalized,
# title-cased form. Extend this dict as new variants show up in the data.
# ---------------------------------------------------------------------------
INDUSTRY_CANONICAL = {
    "tecnologia": "Tecnología",
    "tec": "Tecnología",
    "ti": "Tecnología",
    "it": "Tecnología",
    "tech": "Tecnología",
    "tecnologia de la informacion": "Tecnología",
    "finanzas": "Finanzas",
    "financiero": "Finanzas",
    "banca": "Finanzas",
    "salud": "Salud",
    "sanidad": "Salud",
    "educacion": "Educación",
    "edu": "Educación",
    "manufactura": "Manufactura",
    "manufacturing": "Manufactura",
    "comercio": "Comercio",
    "retail": "Comercio",
    "ventas": "Comercio",
    "gobierno": "Gobierno",
    "sector publico": "Gobierno",
    "construccion": "Construcción",
    "agricultura": "Agricultura",
    "agro": "Agricultura",
}


def normalize_key(value):
    """Lowercase, strip, collapse internal whitespace — for matching only."""
    if pd.isna(value):
        return value
    return " ".join(str(value).strip().lower().split())


def canonical_industry(value):
    if pd.isna(value):
        return value
    key = normalize_key(value)
    if key in INDUSTRY_CANONICAL:
        return INDUSTRY_CANONICAL[key]
    # Unknown variant: keep a cleaned, title-cased version so at least casing
    # and whitespace are consistent.
    return key.title()


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main():
    in_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_IN
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT

    if not in_path.exists():
        sys.exit(f"ERROR: input file not found: {in_path}")

    df = pd.read_csv(in_path)
    rows_before = len(df)
    changes = []

    # --- 1. Standardize industria ------------------------------------------
    section("1. STANDARDIZE 'industria'")
    if "industria" not in df.columns:
        print("  (column 'industria' not found — skipping)")
    else:
        before = sorted(df["industria"].dropna().unique().tolist())
        print(f"BEFORE ({len(before)} unique values):")
        for v in before:
            print(f"  - {v!r}")

        df["industria"] = df["industria"].map(canonical_industry)

        after = sorted(df["industria"].dropna().unique().tolist())
        print(f"\nAFTER ({len(after)} unique values):")
        for v in after:
            print(f"  - {v!r}")
        changes.append(
            f"industria: collapsed {len(before)} -> {len(after)} unique values"
        )

    # --- 2. Missing values in numeric columns ------------------------------
    section("2. MISSING VALUES IN NUMERIC COLUMNS")
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    # Threshold policy:
    #   0%              -> leave (nothing missing)
    #   0 < pct <= 40%  -> median-fill (preserve rows; median is robust to outliers)
    #   pct > 40%       -> leave + warn (too much to impute reliably; decide manually)
    # Rows are only dropped if a column is missing a tiny fraction (<= 5%) AND
    # you would rather not impute — here we prefer median-fill over dropping to
    # keep the full 500 responses, so dropping is not applied automatically.
    if not numeric_cols:
        print("  (no numeric columns detected)")
    else:
        for col in numeric_cols:
            n_missing = int(df[col].isna().sum())
            pct = n_missing / rows_before * 100 if rows_before else 0
            if n_missing == 0:
                print(f"  {col:<28} {pct:5.1f}%  -> leave (no missing)")
            elif pct <= 40:
                median = df[col].median()
                df[col] = df[col].fillna(median)
                print(
                    f"  {col:<28} {pct:5.1f}%  -> fill with median ({median:,.2f})"
                )
                changes.append(
                    f"{col}: filled {n_missing} missing with median {median:,.2f}"
                )
            else:
                print(
                    f"  {col:<28} {pct:5.1f}%  -> LEAVE (>40% missing; impute manually)"
                )
                changes.append(
                    f"{col}: left {n_missing} missing ({pct:.1f}%, too high to impute)"
                )

    # --- 3. Flag negative ahorro_mensual_usd -------------------------------
    section("3. FLAG NEGATIVE 'ahorro_mensual_usd'")
    if "ahorro_mensual_usd" not in df.columns:
        print("  (column 'ahorro_mensual_usd' not found — skipping)")
    else:
        neg_mask = df["ahorro_mensual_usd"] < 0
        n_neg = int(neg_mask.sum())
        df["ahorro_negativo"] = neg_mask
        print(f"  Negative values found: {n_neg}")
        print(f"  Added boolean column 'ahorro_negativo' (True where value < 0).")
        print(f"  Negative rows were KEPT (valid: spending exceeds earnings).")
        changes.append(
            f"ahorro_negativo: flagged {n_neg} negative rows (kept, not removed)"
        )

    # --- 4. Save -----------------------------------------------------------
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    rows_after = len(df)

    # --- 5. Summary --------------------------------------------------------
    section("5. SUMMARY")
    print(f"  Input:  {in_path}")
    print(f"  Output: {out_path}")
    print(f"  Rows before: {rows_before}")
    print(f"  Rows after:  {rows_after}")
    print(f"  Columns: {df.shape[1]}")
    print("  Changes:")
    for c in changes:
        print(f"    - {c}")


if __name__ == "__main__":
    main()
