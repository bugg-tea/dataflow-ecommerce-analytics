import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from app.analytics import Analytics
from app.schemas import HealthResponse, SummaryResponse, OrdersResponse, QualityReportResponse
from app.sql_database import connect

DB_PATH = os.environ.get("DATAFLOW_DB_PATH", "data/dataflow.sqlite")
MONGO_URI = os.environ.get("MONGO_URI")


def get_mongo_repo():
    if not MONGO_URI:
        return None
    from app.mongo_repository import MongoRepository

    return MongoRepository(MONGO_URI)


def create_app(db_path=None, mongo_repo=None):
    db_path = db_path or DB_PATH
    app = FastAPI(title="DataFlow E-Commerce Analytics", version="1.0.0")

    @app.exception_handler(Exception)
    async def unhandled(request, exc):
        return JSONResponse(status_code=500, content={"detail": "Internal service error"})

    @app.get("/health", response_model=HealthResponse)
    def health():
        try:
            conn = connect(db_path)
            conn.execute("SELECT 1 FROM orders LIMIT 1")
            conn.close()
            return {"status": "ok", "database": "ready"}
        except Exception:
            return {"status": "ok", "database": "empty_or_unavailable"}

    @app.get("/api/summary", response_model=SummaryResponse)
    def summary(
        date_from: str | None = None, date_to: str | None = None, status: str | None = None
    ):
        conn = connect(db_path)
        try:
            return Analytics(conn).summary(date_from, date_to, status)
        finally:
            conn.close()

    @app.get("/api/orders", response_model=OrdersResponse)
    def orders(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
    ):
        conn = connect(db_path)
        try:
            result = Analytics(conn).orders(page, page_size, date_from, date_to, status)
            if not result["items"] and page > 1:
                raise HTTPException(status_code=404, detail="No orders on this page")
            return result
        finally:
            conn.close()

    @app.get("/api/quality-report", response_model=QualityReportResponse)
    def quality_report():
        repo = mongo_repo or get_mongo_repo()
        if repo is None:
            raise HTTPException(status_code=503, detail="MongoDB reporting is not configured")
        try:
            report = repo.get_latest_quality_report()
        except Exception:
            raise HTTPException(status_code=503, detail="MongoDB reporting is unavailable")
        if report is None:
            raise HTTPException(status_code=404, detail="No quality report available")
        return report

    return app


app = create_app()
