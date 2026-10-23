import re

from playwright.sync_api import expect
import os
import subprocess
import sys
import time
import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="module")
def streamlit_server():
    env = os.environ.copy()
    env["DATAFLOW_DB_PATH"] = "data/ui-test.sqlite"
    # env["DATAFLOW_DB_PATH"] = "data/dataflow.sqlite"
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app/dashboard.py",
            "--server.port",
            "8599",
            "--server.headless",
            "true",
        ],
        env=env,
    )
    time.sleep(8)
    yield "http://localhost:8599"
    proc.terminate()


@pytest.fixture
def page(streamlit_server):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        current_page = context.new_page()
        current_page.set_default_timeout(30000)

        try:
            current_page.goto(
                streamlit_server,
                wait_until="domcontentloaded",
            )

            expect(
                current_page.get_by_text(
                    "Total orders",
                    exact=True,
                )
            ).to_be_visible(timeout=30000)

            yield current_page
        finally:
            context.close()
            browser.close()


def total_orders_value(page):
    metric = page.get_by_test_id("stMetric").filter(
        has=page.get_by_text("Total orders", exact=True)
    )
    return metric.get_by_test_id("stMetricValue")


def select_order_status(page, status):
    page.get_by_role(
        "combobox",
        name=re.compile("Order status"),
    ).click()

    page.get_by_role(
        "option",
        name=status,
        exact=True,
    ).click()


def test_dashboard_title(page):
    expect(page).to_have_title(
        re.compile("DataFlow"),
        timeout=30000,
    )
    expect(
        page.get_by_role(
            "heading",
            name="DataFlow E-Commerce Analytics Dashboard",
            exact=True,
        )
    ).to_be_visible(timeout=30000)


def test_kpi_section_visible(page):
    expect(page.get_by_text("Total orders", exact=True)).to_be_visible(timeout=30000)

    # Deterministic sample database contains five orders.
    expect(total_orders_value(page)).to_have_text(
        "5",
        timeout=30000,
    )


def test_charts_render(page):
    # Verify actual Plotly chart containers, not only headings.
    expect(page.get_by_test_id("stPlotlyChart")).to_have_count(
        4,
        timeout=30000,
    )


def test_status_filter_updates(page):
    select_order_status(page, "delivered")

    # Sample data contains three delivered orders.
    expect(total_orders_value(page)).to_have_text(
        "3",
        timeout=30000,
    )


def test_empty_state(page):
    select_order_status(page, "unavailable")

    expect(
        page.get_by_text(
            "No orders match the selected filters.",
            exact=True,
        )
    ).to_be_visible(timeout=30000)

    expect(page.get_by_test_id("stMetric")).to_have_count(
        0,
        timeout=30000,
    )
