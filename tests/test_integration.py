import sqlite3
from app.data_pipeline import run_pipeline, save_to_sqlite
from app.main import create_app
from fastapi.testclient import TestClient


def test_full_data_flow(sample_db):
    db, report = sample_db
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 5
    assert conn.execute("SELECT COUNT(*) FROM order_items").fetchone()[0] == 6


def test_api_kpis_match_known_dataset(sample_db):
    db, _ = sample_db
    body = TestClient(create_app(db_path=db)).get("/api/summary").json()
    assert body["total_orders"] == 5
    assert body["merchandise_sales"] == 550.0


def test_quality_report_matches_pipeline(sample_db):
    _, report = sample_db
    assert report["accepted_rows"] > 0


def test_double_ingestion_idempotent(tmp_path):
    d1, _ = run_pipeline("data/sample")
    db = tmp_path / "db.sqlite"
    save_to_sqlite(d1, str(db))
    d2, _ = run_pipeline("data/sample")
    save_to_sqlite(d2, str(db))
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 5


def test_mongo_failure_does_not_corrupt_sqlite(sample_db):
    db, _ = sample_db

    class FailingRepo:
        def get_latest_quality_report(self):
            raise RuntimeError("mongo down")

    client = TestClient(create_app(db_path=db, mongo_repo=FailingRepo()))
    assert client.get("/api/quality-report").status_code == 503
    assert client.get("/api/summary").json()["total_orders"] == 5
