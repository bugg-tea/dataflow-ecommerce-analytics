import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

from app.sql_database import connect, insert_dataframe

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {
    "orders": ["order_id", "customer_id", "order_status", "order_purchase_timestamp"],
    "order_items": ["order_id", "order_item_id", "product_id", "price", "freight_value"],
    "products": ["product_id", "product_category_name"],
    "customers": ["customer_id", "customer_city", "customer_state"],
    "reviews": ["review_id", "order_id", "review_score"],
}

PRIMARY_KEYS = {
    "orders": ["order_id"],
    "order_items": ["order_id", "order_item_id"],
    "products": ["product_id"],
    "customers": ["customer_id"],
    "reviews": ["review_id"],
}

DB_COLUMNS = {
    "customers": ["customer_id", "customer_city", "customer_state"],
    "products": ["product_id", "product_category_name"],
    "orders": ["order_id", "customer_id", "order_status", "order_purchase_timestamp"],
    "order_items": ["order_id", "order_item_id", "product_id", "price", "freight_value"],
    "reviews": ["review_id", "order_id", "review_score"],
}


def _utc_now():
    return datetime.now(timezone.utc).isoformat()


def load_csv(path, dataset):
    if not Path(path).exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    df = pd.read_csv(path, dtype=str)
    missing = [c for c in REQUIRED_COLUMNS[dataset] if c not in df.columns]
    if missing:
        raise ValueError(f"{dataset}: missing required columns: {missing}")
    return df


def clean_dataset(name, df, report):
    df = df.copy()
    key = PRIMARY_KEYS[name]
    before = len(df)
    duplicate_mask = df.duplicated(subset=key, keep="first")
    duplicates = int(duplicate_mask.sum())
    df = df[~duplicate_mask]
    findings = []

    if name == "orders":
        missing_id = df["order_id"].isna() | (df["order_id"].astype(str).str.strip() == "")
        invalid_date = pd.to_datetime(df["order_purchase_timestamp"], errors="coerce").isna()
        reject = missing_id | invalid_date
        if missing_id.any():
            findings.append(f"{int(missing_id.sum())} orders missing order_id")
        if invalid_date.any():
            findings.append(f"{int(invalid_date.sum())} orders with invalid purchase timestamp")
        df = df[~reject]
        df["order_purchase_timestamp"] = pd.to_datetime(
            df["order_purchase_timestamp"], errors="coerce"
        ).dt.strftime("%Y-%m-%d %H:%M:%S")
    elif name == "order_items":
        missing_id = df["order_id"].isna() | (df["order_id"].astype(str).str.strip() == "")
        price = pd.to_numeric(df["price"], errors="coerce")
        invalid_price = price.isna() | (price < 0)
        reject = missing_id | invalid_price
        if invalid_price.any():
            findings.append(
                f"{int(invalid_price.sum())} order items with missing or negative price"
            )
        df = df[~reject]
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df["freight_value"] = pd.to_numeric(df["freight_value"], errors="coerce").fillna(0)
        df["order_item_id"] = (
            pd.to_numeric(df["order_item_id"], errors="coerce").fillna(0).astype(int)
        )
    elif name == "reviews":
        score = pd.to_numeric(df["review_score"], errors="coerce")
        invalid = score.isna() | (score < 1) | (score > 5)
        if invalid.any():
            findings.append(f"{int(invalid.sum())} reviews with missing or out-of-range score")
        df = df[~invalid]
        df["review_score"] = score[~invalid]
    else:
        df = df.fillna(
            {
                "product_category_name": "unknown",
                "customer_city": "unknown",
                "customer_state": "unknown",
            }
        )

    rejected = before - len(df)
    report["total_rows"] += before
    report["accepted_rows"] += len(df)
    report["rejected_rows"] += rejected
    report["duplicate_counts"][name] = duplicates
    report["missing_values"][name] = int(df.isna().sum().sum())
    report["validation_findings"].extend(findings)
    return df


def run_pipeline(data_dir):
    data_dir = Path(data_dir)
    report = {
        "run_id": str(uuid.uuid4()),
        "started_at": _utc_now(),
        "total_rows": 0,
        "accepted_rows": 0,
        "rejected_rows": 0,
        "missing_values": {},
        "duplicate_counts": {},
        "validation_findings": [],
    }
    datasets = {}
    for name in ["customers", "products", "orders", "order_items", "reviews"]:
        path = data_dir / f"{name}.csv"
        if not path.exists():
            if name == "orders":
                raise FileNotFoundError(f"Required input file not found: {path}")
            logger.info("Optional %s.csv not found; related analytics will be limited", name)
            continue
        raw = load_csv(path, name)
        datasets[name] = clean_dataset(name, raw, report)
    report["completed_at"] = _utc_now()
    report["status"] = "completed"
    return datasets, report


def save_to_sqlite(datasets, db_path):
    conn = connect(db_path)
    try:
        counts = {}
        for name in ["customers", "products", "orders", "order_items", "reviews"]:
            if name in datasets:
                insert_dataframe(conn, name, datasets[name], DB_COLUMNS[name])
                counts[name] = len(datasets[name])
        return counts
    finally:
        conn.close()
