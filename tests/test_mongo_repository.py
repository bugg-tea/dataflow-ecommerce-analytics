import pytest
from app.mongo_repository import MongoRepository, MongoUnavailableError


class FakeCollection:
    def __init__(self):
        self.docs = {}

    def update_one(self, query, update, upsert=False):
        self.docs[query["run_id"]] = update["$set"]
        return True

    def find_one(self, sort=None):
        return (
            sorted(self.docs.values(), key=lambda d: d.get("created_at"), reverse=True)[0]
            if self.docs
            else None
        )


class FakeRepo:
    def __init__(self):
        self.runs = FakeCollection()
        self.reports = FakeCollection()

    def save_ingestion_run(self, run_id, status, counts, error=None):
        doc = {"run_id": run_id, "status": status, "accepted_rows": counts["accepted_rows"]}
        self.runs.update_one({"run_id": run_id}, {"$set": doc}, True)
        return doc

    def save_quality_report(self, report):
        doc = {
            "run_id": report["run_id"],
            "accepted_rows": report["accepted_rows"],
            "created_at": "2024-01-01",
        }
        self.reports.update_one({"run_id": report["run_id"]}, {"$set": doc}, True)
        return doc

    def get_latest_quality_report(self):
        return self.reports.find_one()


def test_quality_report_fields():
    repo = FakeRepo()
    doc = repo.save_quality_report(
        {
            "run_id": "run-1",
            "total_rows": 10,
            "accepted_rows": 8,
            "rejected_rows": 2,
            "missing_values": {},
            "duplicate_counts": {},
            "validation_findings": [],
        }
    )
    assert doc["run_id"] == "run-1"


def test_ingestion_metadata_mapping():
    repo = FakeRepo()
    doc = repo.save_ingestion_run("run-2", "completed", {"accepted_rows": 5})
    assert doc["accepted_rows"] == 5


def test_duplicate_run_id_upsert():
    repo = FakeRepo()
    repo.save_ingestion_run("same", "completed", {"accepted_rows": 5})
    repo.save_ingestion_run("same", "completed", {"accepted_rows": 5})
    assert len(repo.runs.docs) == 1


def test_get_latest_report_empty():
    assert FakeRepo().get_latest_quality_report() is None


def test_mongo_connection_failure():
    with pytest.raises(MongoUnavailableError):
        MongoRepository("mongodb://invalid-host:27017", database="dataflow_test")
