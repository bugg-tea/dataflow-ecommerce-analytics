import pytest
from fastapi.testclient import TestClient
from app.main import create_app


@pytest.fixture
def api_client(sample_db):
    db, _ = sample_db
    return TestClient(create_app(db_path=db, mongo_repo=None))


def test_health(api_client):
    assert api_client.get("/health").status_code == 200


def test_summary_schema_and_values(api_client):
    body = api_client.get("/api/summary").json()
    assert body["total_orders"] == 5
    assert body["merchandise_sales"] == 550.0


def test_orders_returns_records(api_client):
    assert len(api_client.get("/api/orders").json()["items"]) == 5


def test_orders_pagination(api_client):
    body = api_client.get("/api/orders?page=1&page_size=2").json()
    assert len(body["items"]) == 2


def test_invalid_page(api_client):
    assert api_client.get("/api/orders?page=0").status_code == 422


def test_invalid_page_size(api_client):
    assert api_client.get("/api/orders?page_size=1000").status_code == 422


def test_page_beyond_available(api_client):
    assert api_client.get("/api/orders?page=99").status_code == 404


def test_quality_report_not_configured(api_client):
    assert api_client.get("/api/quality-report").status_code == 503


def test_quality_report_no_report(sample_db):
    db, _ = sample_db

    class EmptyRepo:
        def get_latest_quality_report(self):
            return None

    assert (
        TestClient(create_app(db_path=db, mongo_repo=EmptyRepo()))
        .get("/api/quality-report")
        .status_code
        == 404
    )


def test_quality_report_success(sample_db):
    db, _ = sample_db

    class FakeRepo:
        def get_latest_quality_report(self):
            return {
                "run_id": "r1",
                "created_at": "2024-01-01T00:00:00Z",
                "total_rows": 10,
                "accepted_rows": 8,
                "rejected_rows": 2,
                "missing_values": {},
                "duplicate_counts": {},
                "validation_findings": [],
            }

    r = TestClient(create_app(db_path=db, mongo_repo=FakeRepo())).get("/api/quality-report")
    assert r.status_code == 200 and r.json()["run_id"] == "r1"


def test_empty_database_summary(tmp_path):
    client = TestClient(create_app(db_path=str(tmp_path / "empty.sqlite")))
    assert client.get("/api/summary").json()["total_orders"] == 0


def test_invalid_date_filter(api_client):
    assert api_client.get("/api/summary", params={"date_from": "not-a-date"}).status_code in (
        200,
        422,
    )


def test_internal_error_no_stack_trace(api_client):
    assert "Traceback" not in api_client.get("/api/orders?page=1&page_size=1").text
