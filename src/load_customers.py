from pathlib import Path

import pandas as pd
from sqlalchemy import text

from database import get_engine


# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "raw" / "olist_customers_dataset.csv"


EXPECTED_COLUMNS = [
    "customer_id",
    "customer_unique_id",
    "customer_zip_code_prefix",
    "customer_city",
    "customer_state",
]


def extract():
    """Read the raw Olist customers dataset."""

    print("Extracting customers data...")

    df = pd.read_csv(CSV_PATH)

    print(f"Rows extracted: {len(df):,}")

    return df


def validate(df):
    """Validate the structure and basic quality of the dataset."""

    print("Validating customers data...")

    missing_columns = [
        column
        for column in EXPECTED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing expected columns: {missing_columns}"
        )

    if df["customer_id"].isna().any():
        raise ValueError("customer_id contains null values.")

    if df["customer_id"].duplicated().any():
        raise ValueError("customer_id contains duplicates.")

    print("Validation successful.")


def transform(df):
    """Transform raw data into the structure used by PostgreSQL."""

    print("Transforming customers data...")

    df = df[
        [
            "customer_id",
            "customer_unique_id",
            "customer_city",
            "customer_state",
        ]
    ].copy()

    df["customer_city"] = df["customer_city"].str.strip()
    df["customer_state"] = df["customer_state"].str.strip().str.upper()

    print(f"Rows after transformation: {len(df):,}")

    return df


def load(df):
    """Load customers into PostgreSQL."""

    print("Loading customers into PostgreSQL...")

    engine = get_engine()

    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE customers CASCADE;"))

        df.to_sql(
            "customers",
            connection,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )

    print("Load successful.")


def verify():
    """Verify the number of records loaded."""

    engine = get_engine()

    with engine.connect() as connection:
        count = connection.execute(
            text("SELECT COUNT(*) FROM customers;")
        ).scalar_one()

    print(f"Rows in PostgreSQL: {count:,}")


def main():
    print("\n=== OLIST CUSTOMERS ETL ===\n")

    df = extract()
    validate(df)
    df = transform(df)
    load(df)
    verify()

    print("\nETL completed successfully.")


if __name__ == "__main__":
    main()