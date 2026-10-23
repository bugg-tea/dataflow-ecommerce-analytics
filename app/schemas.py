from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class HealthResponse(BaseModel):
    status: str
    database: str


class SummaryResponse(BaseModel):
    total_orders: int
    delivered_orders: int
    cancelled_orders: int
    merchandise_sales: float
    average_order_value: Optional[float]
    average_review_score: Optional[float]


class OrderResponse(BaseModel):
    order_id: str
    customer_id: str
    order_status: str
    order_purchase_timestamp: str
    item_count: int
    merchandise_sales: float


class OrdersResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: List[OrderResponse]


class QualityReportResponse(BaseModel):
    run_id: str
    created_at: datetime
    total_rows: int
    accepted_rows: int
    rejected_rows: int
    missing_values: dict
    duplicate_counts: dict
    validation_findings: list
