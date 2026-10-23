def test_total_orders(analytics):
    assert analytics.summary()["total_orders"] == 5


def test_delivered_and_cancelled(analytics):
    s = analytics.summary()
    assert s["delivered_orders"] == 3
    assert s["cancelled_orders"] == 1


def test_merchandise_sales(analytics):
    assert analytics.summary()["merchandise_sales"] == 550.0


def test_average_order_value(analytics):
    assert analytics.summary()["average_order_value"] == 137.5


def test_average_review_score(analytics):
    assert analytics.summary()["average_review_score"] == 4.0


def test_empty_database(tmp_path):
    from app.sql_database import connect
    from app.analytics import Analytics

    conn = connect(str(tmp_path / "empty.sqlite"))
    s = Analytics(conn).summary()
    assert s["total_orders"] == 0
    assert s["average_order_value"] is None


def test_missing_review_data(tmp_path):
    from app.sql_database import connect
    from app.analytics import Analytics

    conn = connect(str(tmp_path / "noreviews.sqlite"))
    assert Analytics(conn).summary()["average_review_score"] is None


def test_date_filter(analytics):
    assert analytics.summary(date_from="2024-02-01", date_to="2024-02-28")["total_orders"] == 2


def test_status_filter(analytics):
    s = analytics.summary(status="delivered")
    assert s["total_orders"] == 3
    assert s["merchandise_sales"] == 430.0


def test_category_ranking(analytics):
    cats = analytics.top_categories()
    assert cats[0]["category"] == "books"
    assert cats[0]["sales"] == 250.0


def test_no_double_counting(analytics):
    assert analytics.summary()["merchandise_sales"] == 550.0


def test_orders_pagination(analytics):
    result = analytics.orders(page=1, page_size=2)
    assert result["total"] == 5
    assert len(result["items"]) == 2
