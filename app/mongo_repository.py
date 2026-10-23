import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class MongoUnavailableError(Exception):
    pass


class MongoRepository:
    def __init__(self, uri, database="dataflow"):
        try:
            from pymongo import MongoClient, ASCENDING
        except ImportError as exc:
            raise MongoUnavailableError("PyMongo is not installed") from exc
        try:
            self.client = MongoClient(uri, serverSelectionTimeoutMS=3000)
            self.client.admin.command("ping")
        except Exception as exc:
            raise MongoUnavailableError(
                f"MongoDB connection failed: {exc.__class__.__name__}"
            ) from exc
        self.db = self.client[database]
        self.runs = self.db["ingestion_runs"]
        self.reports = self.db["quality_reports"]
        self.runs.create_index([("run_id", ASCENDING)], unique=True)
        self.reports.create_index([("run_id", ASCENDING)], unique=True)

    def save_ingestion_run(self, run_id, status, counts, error=None):
        doc = {
            "run_id": run_id,
            "status": status,
            "started_at": counts.get("started_at"),
            "completed_at": counts.get("completed_at"),
            "input_rows": counts.get("total_rows", 0),
            "accepted_rows": counts.get("accepted_rows", 0),
            "rejected_rows": counts.get("rejected_rows", 0),
            "error_summary": error,
        }
        try:
            self.runs.update_one({"run_id": run_id}, {"$set": doc}, upsert=True)
            return doc
        except Exception as exc:
            raise MongoUnavailableError(f"MongoDB write failed: {exc.__class__.__name__}") from exc

    def save_quality_report(self, report):
        doc = {
            "run_id": report["run_id"],
            "created_at": datetime.now(timezone.utc),
            "total_rows": report["total_rows"],
            "accepted_rows": report["accepted_rows"],
            "rejected_rows": report["rejected_rows"],
            "missing_values": report["missing_values"],
            "duplicate_counts": report["duplicate_counts"],
            "validation_findings": report["validation_findings"],
        }
        try:
            self.reports.update_one({"run_id": report["run_id"]}, {"$set": doc}, upsert=True)
            return doc
        except Exception as exc:
            raise MongoUnavailableError(f"MongoDB write failed: {exc.__class__.__name__}") from exc

    def get_latest_quality_report(self):
        try:
            doc = self.reports.find_one(sort=[("created_at", -1)])
        except Exception as exc:
            raise MongoUnavailableError(f"MongoDB read failed: {exc.__class__.__name__}") from exc
        if not doc:
            return None
        doc.pop("_id", None)
        return doc
