from pathlib import Path

import pandas as pd
from sqlalchemy import text

from database import get_engine


BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"


DATASETS = {
    "customers": {
        "file": "olist_customers_dataset.csv",
        "columns": [
            "customer_id",
            "customer_unique_id",
            "customer_city",
            "customer_state",
        ],
        "primary_key": ["customer_id"],
    },
    "product_category_translation": {
        "file": "product_category_name_translation.csv",
        "columns": [
            "product_category_name",
            "product_category_name_english",
        ],
        "primary_key": ["product_category_name"],
    },
    "products": {
        "file": "olist_products_dataset.csv",
        "columns": [
            "product_id",
            "product_category_name",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
            "product_photos_qty",
        ],
        "primary_key": ["product_id"],
    },
    "sellers": {
        "file": "olist_sellers_dataset.csv",
        "columns": [
            "seller_id",
            "seller_city",
            "seller_state",
        ],
        "primary_key": ["seller_id"],
    },
    "orders": {
        "file": "olist_orders_dataset.csv",
        "columns": [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
        "primary_key": ["order_id"],
    },
    "order_items": {
        "file": "olist_order_items_dataset.csv",
        "columns": [
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ],
        "primary_key": ["order_id", "order_item_id"],
    },
    "order_payments": {
        "file": "olist_order_payments_dataset.csv",
        "columns": [
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value",
        ],
        "primary_key": ["order_id", "payment_sequential"],
    },
    "order_reviews": {
        "file": "olist_order_reviews_dataset.csv",
        "columns": [
            "review_id",
            "order_id",
            "review_score",
            "review_creation_date",
            "review_answer_timestamp",
        ],
        "primary_key": ["review_id", "order_id"],
    },
}


def extract(dataset):
    """Read a raw CSV file."""

    csv_path = RAW_DIR / dataset["file"]

    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    return pd.read_csv(csv_path)


def validate(df, table_name, config):
    """Validate required columns and primary-key quality."""

    required_columns = config["columns"]
    primary_key = config["primary_key"]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{table_name}: missing columns {missing_columns}"
        )

    if df[primary_key].isna().any().any():
        raise ValueError(
            f"{table_name}: primary key contains null values"
        )

    if df.duplicated(subset=primary_key).any():
        raise ValueError(
            f"{table_name}: duplicated primary key detected"
        )


def transform(df, config):
    """Select only columns used by the analytical model."""

    return df[config["columns"]].copy()


def clean_text_columns(df):
    """Normalize selected text fields."""

    text_columns = [
        "customer_city",
        "customer_state",
        "seller_city",
        "seller_state",
        "order_status",
        "payment_type",
    ]

    for column in text_columns:
        if column in df.columns:
            df[column] = df[column].astype("string").str.strip()

    for column in ["customer_state", "seller_state"]:
        if column in df.columns:
            df[column] = df[column].str.upper()

    return df


def load_table(connection, df, table_name):
    """Append a transformed dataframe to PostgreSQL."""

    df.to_sql(
        table_name,
        connection,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )


def truncate_tables(connection):
    """Clear target tables before a full reload."""

    connection.execute(
        text(
            """
            TRUNCATE TABLE
                order_reviews,
                order_payments,
                order_items,
                orders,
                sellers,
                products,
                product_category_translation,
                customers
            RESTART IDENTITY CASCADE;
            """
        )
    )


def verify_counts(connection, expected_counts):
    """Compare source row counts with PostgreSQL row counts."""

    print("\n=== DATA QUALITY: ROW COUNTS ===")

    for table_name, expected in expected_counts.items():
        actual = connection.execute(
            text(f'SELECT COUNT(*) FROM "{table_name}"')
        ).scalar_one()

        status = "OK" if actual == expected else "MISMATCH"

        print(
            f"{table_name:<30} "
            f"source={expected:>7,} "
            f"database={actual:>7,} "
            f"[{status}]"
        )

        if actual != expected:
            raise ValueError(
                f"{table_name}: source/database row count mismatch"
            )


def run_pipeline():
    print("\n=== ECOM INTELLIGENCE ETL PIPELINE ===\n")

    prepared_data = {}
    expected_counts = {}

    # Extract, validate and transform before changing the database.
    for table_name, config in DATASETS.items():
        print(f"[PREPARING] {table_name}")

        df = extract(config)

        print(f"  Extracted: {len(df):,} rows")

        validate(df, table_name, config)

        df = transform(df, config)
        df = clean_text_columns(df)

        prepared_data[table_name] = df
        expected_counts[table_name] = len(df)

        print("  Validation: OK")

    engine = get_engine()

    # One transaction: either the complete load succeeds or it rolls back.
    with engine.begin() as connection:
        print("\nClearing target tables...")
        truncate_tables(connection)

        print("\n=== LOADING POSTGRESQL ===")

        for table_name, df in prepared_data.items():
            print(f"[LOADING] {table_name}: {len(df):,} rows")
            load_table(connection, df, table_name)

        verify_counts(connection, expected_counts)

    print("\nETL pipeline completed successfully.")


if __name__ == "__main__":
    run_pipeline()