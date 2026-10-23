from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.mongo_repository import MongoRepository, MongoUnavailableError


@pytest.fixture
def repo():
    client = MagicMock(name="mongo_client")
    database = MagicMock(name="dataflow_test_database")

    runs_collection = MagicMock(name="ingestion_runs")
    reports_collection = MagicMock(name="quality_reports")

    # Return a separate mock for each named database/collection.
    client.__getitem__.side_effect = {
        "dataflow_test": database,
    }.__getitem__

    database.__getitem__.side_effect = {
        "ingestion_runs": runs_collection,
        "quality_reports": reports_collection,
    }.__getitem__

    with patch("pymongo.MongoClient", return_value=client):
        repository = MongoRepository(
            "mongodb://localhost:27017",
            database="dataflow_test",
        )

    return repository, client


@pytest.fixture
def report():
    return {
        "run_id": "test-run-1",
        "started_at": "2026-10-23T08:00:00+00:00",
        "completed_at": "2026-10-23T08:00:01+00:00",
        "total_rows": 10,
        "accepted_rows": 8,
        "rejected_rows": 2,
        "missing_values": {"orders": 1},
        "duplicate_counts": {"orders": 1},
        "validation_findings": ["One invalid purchase timestamp"],
    }


def test_constructor_pings_and_creates_unique_indexes(repo):
    repository, client = repo

    client.admin.command.assert_called_once_with("ping")
    repository.runs.create_index.assert_called_once_with([("run_id", 1)], unique=True)
    repository.reports.create_index.assert_called_once_with([("run_id", 1)], unique=True)


def test_ingestion_metadata_mapping(repo, report):
    repository, _ = repo

    document = repository.save_ingestion_run(report["run_id"], "completed", report)

    assert document["input_rows"] == 10
    assert document["accepted_rows"] == 8
    assert document["rejected_rows"] == 2
    assert document["started_at"] == report["started_at"]
    assert document["completed_at"] == report["completed_at"]
    assert document["error_summary"] is None

    repository.runs.update_one.assert_called_once_with(
        {"run_id": "test-run-1"},
        {"$set": document},
        upsert=True,
    )


def test_quality_document_mapping(repo, report):
    repository, _ = repo

    document = repository.save_quality_report(report)

    assert document["run_id"] == "test-run-1"
    assert isinstance(document["created_at"], datetime)
    assert document["total_rows"] == 10
    assert document["accepted_rows"] == 8
    assert document["rejected_rows"] == 2
    assert document["missing_values"] == {"orders": 1}
    assert document["duplicate_counts"] == {"orders": 1}
    assert document["validation_findings"] == ["One invalid purchase timestamp"]

    repository.reports.update_one.assert_called_once_with(
        {"run_id": "test-run-1"},
        {"$set": document},
        upsert=True,
    )


def test_repeated_report_uses_same_upsert_key(repo, report):
    repository, _ = repo

    repository.save_quality_report(report)
    repository.save_quality_report(report)

    calls = repository.reports.update_one.call_args_list
    assert len(calls) == 2
    for call in calls:
        assert call.args[0] == {"run_id": "test-run-1"}
        assert call.kwargs["upsert"] is True


def test_latest_report_removes_internal_id(repo):
    repository, _ = repo
    repository.reports.find_one.return_value = {
        "_id": "internal-id",
        "run_id": "test-run-1",
    }

    result = repository.get_latest_quality_report()

    assert result == {"run_id": "test-run-1"}
    repository.reports.find_one.assert_called_once_with(sort=[("created_at", -1)])


def test_latest_report_when_collection_is_empty(repo):
    repository, _ = repo
    repository.reports.find_one.return_value = None

    assert repository.get_latest_quality_report() is None


@pytest.mark.parametrize(
    "operation",
    ["ingestion_write", "quality_write", "quality_read"],
)
def test_database_failures_are_wrapped(repo, report, operation):
    repository, _ = repo

    if operation == "ingestion_write":
        repository.runs.update_one.side_effect = RuntimeError("write failed")

        with pytest.raises(MongoUnavailableError):
            repository.save_ingestion_run(
                "test-run-1",
                "completed",
                report,
            )

    elif operation == "quality_write":
        repository.reports.update_one.side_effect = RuntimeError("write failed")

        with pytest.raises(MongoUnavailableError):
            repository.save_quality_report(report)

    else:
        repository.reports.find_one.side_effect = RuntimeError("read failed")

        with pytest.raises(MongoUnavailableError):
            repository.get_latest_quality_report()


def test_connection_failure_is_wrapped():
    with patch("pymongo.MongoClient") as client_class:
        client_class.return_value.admin.command.side_effect = RuntimeError("connection failed")

        with pytest.raises(
            MongoUnavailableError,
            match="MongoDB connection failed",
        ):
            MongoRepository(
                "mongodb://localhost:27017",
                database="dataflow_test",
            )
