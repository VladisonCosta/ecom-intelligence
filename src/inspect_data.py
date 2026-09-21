from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"


def inspect_csv(csv_path):
    print("\n" + "=" * 70)
    print(f"FILE: {csv_path.name}")
    print("=" * 70)

    df = pd.read_csv(csv_path)

    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    print("\nColumn names:")
    for column in df.columns:
        print(f"  - {column}")

    nulls = df.isna().sum()
    nulls = nulls[nulls > 0]

    print("\nColumns with null values:")

    if nulls.empty:
        print("  None")
    else:
        for column, count in nulls.items():
            print(f"  - {column}: {count:,}")

    print(f"\nDuplicated rows: {df.duplicated().sum():,}")


def main():
    csv_files = sorted(RAW_DATA_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {RAW_DATA_DIR}"
        )

    print(f"Datasets found: {len(csv_files)}")

    for csv_path in csv_files:
        inspect_csv(csv_path)


if __name__ == "__main__":
    main()