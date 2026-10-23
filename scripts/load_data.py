import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data_pipeline import run_pipeline, save_to_sqlite
from app.mongo_repository import MongoRepository, MongoUnavailableError

logging.basicConfig(level=logging.INFO)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/sample")
    parser.add_argument("--db", default=os.environ.get("DATAFLOW_DB_PATH", "data/dataflow.sqlite"))
    args = parser.parse_args()
    datasets, report = run_pipeline(args.data_dir)
    save_to_sqlite(datasets, args.db)
    print(f"Ingested {report['accepted_rows']} accepted rows into {args.db}")
    print(f"Quality: {report}")
    mongo_uri = os.environ.get("MONGO_URI")
    if mongo_uri:
        try:
            repo = MongoRepository(mongo_uri)
            repo.save_ingestion_run(report["run_id"], "completed", report)
            repo.save_quality_report(report)
            print("MongoDB ingestion metadata and quality report saved.")
        except MongoUnavailableError as exc:
            print(f"WARNING: MongoDB reporting unavailable: {exc}")
    else:
        print("WARNING: MONGO_URI not set; MongoDB reporting skipped.")


if __name__ == "__main__":
    main()
