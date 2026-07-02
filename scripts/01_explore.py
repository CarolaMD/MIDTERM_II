"""
01_explore.py — Initial exploration of the LATAM finance survey dataset.

Prints:
  1. Number of rows and columns
  2. Every column with its name and data type
  3. Missing values per column, sorted from most to least
  4. Basic statistics for all numeric columns (min, max, mean, median, std)
  5. Value counts for each categorical column

Usage:
    python scripts/01_explore.py
    python scripts/01_explore.py path/to/other.csv
"""

import sys
from pathlib import Path

import pandas as pd

# Default path is relative to the project root (parent of this script's folder).
DEFAULT_CSV = Path(__file__).resolve().parent.parent / "data" / "latam_finanzas_2025.csv"

CATEGORICAL_COLUMNS = [
    "pais",
    "industria",
    "ocupacion",
    "meta_financiera",
    "tiene_tarjeta_credito",
    "tiene_cuenta_ahorro",
    "tiene_deuda",
]


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main():
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV

    if not csv_path.exists():
        sys.exit(f"ERROR: file not found: {csv_path}")

    df = pd.read_csv(csv_path)

    # 1. Rows and columns
    section("1. SHAPE")
    print(f"Rows:    {df.shape[0]}")
    print(f"Columns: {df.shape[1]}")

    # 2. Columns and data types
    section("2. COLUMNS AND DATA TYPES")
    for name, dtype in df.dtypes.items():
        print(f"  {name:<30} {dtype}")

    # 3. Missing values, most to least
    section("3. MISSING VALUES (most to least)")
    missing = df.isna().sum().sort_values(ascending=False)
    for name, count in missing.items():
        pct = count / len(df) * 100 if len(df) else 0
        print(f"  {name:<30} {count:>6}  ({pct:5.1f}%)")

    # 4. Numeric statistics
    section("4. NUMERIC STATISTICS")
    numeric = df.select_dtypes(include="number")
    if numeric.empty:
        print("  (no numeric columns detected)")
    else:
        stats = numeric.agg(["min", "max", "mean", "median", "std"]).transpose()
        print(stats.to_string(float_format=lambda x: f"{x:,.2f}"))

    # 5. Categorical value counts
    section("5. CATEGORICAL VALUE COUNTS")
    for col in CATEGORICAL_COLUMNS:
        print(f"\n-- {col} --")
        if col not in df.columns:
            print("  (column not found in dataset)")
            continue
        counts = df[col].value_counts(dropna=False)
        for value, count in counts.items():
            print(f"  {str(value):<30} {count}")


if __name__ == "__main__":
    main()
