import pandas as pd
import pytest
from app.data_pipeline import run_pipeline, save_to_sqlite
from app.sql_database import connect


def write_csv(path, df):
    df.to_csv(path, index=False)


def make_orders():
    return pd.DataFrame(
        {
            "order_id": ["O1", "O2"],
            "customer_id": ["C1", "C2"],
            "order_status": ["delivered", "shipped"],
            "order_purchase_timestamp": ["2024-01-01 10:00:00", "2024-01-02 11:00:00"],
        }
    )


def test_valid_data_loads_and_cleans(tmp_path):
    write_csv(tmp_path / "orders.csv", make_orders())
    datasets, report = run_pipeline(tmp_path)
    assert len(datasets["orders"]) == 2


def test_duplicates_detected(tmp_path):
    df = pd.concat([make_orders(), make_orders().iloc[[0]]], ignore_index=True)
    write_csv(tmp_path / "orders.csv", df)
    _, report = run_pipeline(tmp_path)
    assert report["duplicate_counts"]["orders"] == 1


def test_missing_required_column(tmp_path):
    write_csv(tmp_path / "orders.csv", make_orders().drop(columns=["order_status"]))
    with pytest.raises(ValueError, match="missing required columns"):
        run_pipeline(tmp_path)


def test_missing_order_id_rejected(tmp_path):
    df = make_orders()
    df.loc[0, "order_id"] = None
    write_csv(tmp_path / "orders.csv", df)
    _, report = run_pipeline(tmp_path)
    assert report["rejected_rows"] >= 1


def test_invalid_date_rejected(tmp_path):
    df = make_orders()
    df.loc[0, "order_purchase_timestamp"] = "not-a-date"
    write_csv(tmp_path / "orders.csv", df)
    _, report = run_pipeline(tmp_path)
    assert any("invalid purchase timestamp" in f for f in report["validation_findings"])


def test_negative_price_rejected(tmp_path):
    write_csv(tmp_path / "orders.csv", make_orders())
    items = pd.DataFrame(
        {
            "order_id": ["O1", "O2"],
            "order_item_id": [1, 1],
            "product_id": ["P1", "P2"],
            "price": [-5.0, 10.0],
            "freight_value": [1.0, 1.0],
        }
    )
    write_csv(tmp_path / "order_items.csv", items)
    _, report = run_pipeline(tmp_path)
    assert any("negative price" in f for f in report["validation_findings"])


def test_optional_missing_values(tmp_path):
    write_csv(tmp_path / "orders.csv", make_orders())
    write_csv(
        tmp_path / "products.csv",
        pd.DataFrame({"product_id": ["P1"], "product_category_name": [None]}),
    )
    datasets, _ = run_pipeline(tmp_path)
    assert datasets["products"].iloc[0]["product_category_name"] == "unknown"


def test_empty_input(tmp_path):
    write_csv(tmp_path / "orders.csv", make_orders().iloc[:0])
    datasets, report = run_pipeline(tmp_path)
    assert len(datasets["orders"]) == 0


def test_quality_counts_match(tmp_path):
    df = pd.concat([make_orders(), make_orders().iloc[[0]]], ignore_index=True)
    df.loc[1, "order_purchase_timestamp"] = "bad"
    write_csv(tmp_path / "orders.csv", df)
    _, report = run_pipeline(tmp_path)
    assert report["total_rows"] == 3
    assert report["accepted_rows"] + report["rejected_rows"] == 3


def test_repeated_ingestion_idempotent(tmp_path):
    write_csv(tmp_path / "orders.csv", make_orders())
    db = tmp_path / "db.sqlite"
    d1, _ = run_pipeline(tmp_path)
    save_to_sqlite(d1, str(db))
    d2, _ = run_pipeline(tmp_path)
    save_to_sqlite(d2, str(db))
    conn = connect(str(db))
    assert conn.execute("SELECT COUNT(*) c FROM orders").fetchone()["c"] == 2
