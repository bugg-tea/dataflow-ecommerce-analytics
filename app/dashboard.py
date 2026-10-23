import os
import streamlit as st
import pandas as pd
import plotly.express as px

from app.analytics import Analytics
from app.sql_database import connect

st.set_page_config(page_title="DataFlow E-Commerce Analytics", page_icon=":bar_chart:")
st.title("DataFlow E-Commerce Analytics Dashboard")

DB_PATH = os.environ.get("DATAFLOW_DB_PATH", "data/dataflow.sqlite")
conn = connect(DB_PATH)
analytics = Analytics(conn)

col1, col2 = st.columns(2)
date_from = col1.date_input("Date from", value=None)
date_to = col2.date_input("Date to", value=None)
status = st.selectbox(
    "Order status", ["all", "delivered", "shipped", "canceled", "processing", "unavailable"]
)
status = None if status == "all" else status

summary = analytics.summary(date_from, date_to, status)
if summary["total_orders"] == 0:
    st.warning("No orders match the selected filters.")
    st.stop()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total orders", summary["total_orders"])
k2.metric("Delivered orders", summary["delivered_orders"])
k3.metric("Cancelled orders", summary["cancelled_orders"])
k4.metric("Merchandise sales", f"R$ {summary['merchandise_sales']:,.2f}")
k5.metric(
    "Avg order value",
    f"R$ {summary['average_order_value']:,.2f}"
    if summary["average_order_value"] is not None
    else "Unavailable",
)

if summary["average_review_score"] is not None:
    st.metric("Average review score", summary["average_review_score"])
else:
    st.info("Review data is unavailable.")

st.subheader("Orders over time")
time_df = pd.DataFrame(analytics.orders_over_time(date_from, date_to, status))
if not time_df.empty:
    st.plotly_chart(
        px.line(time_df, x="day", y="orders", title="Orders over time"), use_container_width=True
    )

st.subheader("Sales by product category")
cat_df = pd.DataFrame(analytics.category_sales(date_from, date_to, status))
if not cat_df.empty:
    st.plotly_chart(
        px.bar(cat_df, x="category", y="sales", title="Sales by category"), use_container_width=True
    )
    st.plotly_chart(
        px.bar(cat_df.head(10), x="category", y="sales", title="Top 10 categories by sales"),
        use_container_width=True,
    )

st.subheader("Order status distribution")
status_df = pd.DataFrame(analytics.status_distribution(date_from, date_to))
if not status_df.empty:
    st.plotly_chart(
        px.pie(status_df, names="order_status", values="orders", title="Order status distribution"),
        use_container_width=True,
    )

st.subheader("Latest data quality report")
mongo_uri = os.environ.get("MONGO_URI")
if not mongo_uri:
    st.info("MongoDB reporting is not configured.")
else:
    try:
        from app.mongo_repository import MongoRepository

        report = MongoRepository(mongo_uri).get_latest_quality_report()
        if report:
            st.json(report)
        else:
            st.warning("No quality report available.")
    except Exception:
        st.error("MongoDB reporting is unavailable.")
