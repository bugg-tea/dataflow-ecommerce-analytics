class Analytics:
    def __init__(self, conn):
        self.conn = conn

    def _filters(self, date_from=None, date_to=None, status=None):
        where, params = [], []
        if date_from:
            where.append("o.order_purchase_timestamp >= ?")
            params.append(f"{date_from} 00:00:00")
        if date_to:
            where.append("o.order_purchase_timestamp <= ?")
            params.append(f"{date_to} 23:59:59")
        if status:
            where.append("o.order_status = ?")
            params.append(status)
        return ("WHERE " + " AND ".join(where)) if where else "", params

    def summary(self, date_from=None, date_to=None, status=None):
        where, params = self._filters(date_from, date_to, status)
        row = self.conn.execute(
            f"""
            SELECT COUNT(*) AS total_orders,
                   SUM(CASE WHEN o.order_status='delivered' THEN 1 ELSE 0 END) AS delivered_orders,
                   SUM(CASE WHEN o.order_status='canceled' THEN 1 ELSE 0 END) AS cancelled_orders
            FROM orders o {where}
        """,
            params,
        ).fetchone()
        total = row["total_orders"] or 0
        delivered = row["delivered_orders"] or 0
        cancelled = row["cancelled_orders"] or 0
        sales_row = self.conn.execute(
            f"""
            SELECT SUM(oi.price) AS sales, COUNT(DISTINCT o.order_id) AS orders
            FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
            {where + (" AND " if where else "WHERE ") + "o.order_status != 'canceled'"}
        """,
            params,
        ).fetchone()
        sales = sales_row["sales"] or 0.0
        paid_orders = sales_row["orders"] or 0
        aov = round(sales / paid_orders, 2) if paid_orders else None
        review = self.conn.execute(
            f"""
            SELECT AVG(r.review_score) AS avg_score
            FROM orders o JOIN reviews r ON r.order_id = o.order_id {where}
        """,
            params,
        ).fetchone()
        avg_review = round(review["avg_score"], 2) if review["avg_score"] is not None else None
        return {
            "total_orders": total,
            "delivered_orders": delivered,
            "cancelled_orders": cancelled,
            "merchandise_sales": round(sales, 2),
            "average_order_value": aov,
            "average_review_score": avg_review,
        }

    def orders(self, page=1, page_size=10, date_from=None, date_to=None, status=None):
        where, params = self._filters(date_from, date_to, status)
        total = self.conn.execute(f"SELECT COUNT(*) c FROM orders o {where}", params).fetchone()[
            "c"
        ]
        rows = self.conn.execute(
            f"""
            SELECT o.order_id, o.customer_id, o.order_status, o.order_purchase_timestamp,
                   COALESCE(agg.item_count,0) item_count, COALESCE(agg.merchandise_sales,0) merchandise_sales
            FROM orders o
            LEFT JOIN (SELECT order_id, COUNT(*) item_count, SUM(price) merchandise_sales
                       FROM order_items GROUP BY order_id) agg ON agg.order_id=o.order_id
            {where} ORDER BY o.order_purchase_timestamp, o.order_id LIMIT ? OFFSET ?
        """,
            params + [page_size, (page - 1) * page_size],
        ).fetchall()
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "items": [dict(r) for r in rows],
        }

    def orders_over_time(self, date_from=None, date_to=None, status=None):
        where, params = self._filters(date_from, date_to, status)
        rows = self.conn.execute(
            f"""
            SELECT substr(o.order_purchase_timestamp,1,10) AS day, COUNT(*) AS orders
            FROM orders o {where} GROUP BY day ORDER BY day
        """,
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def category_sales(self, date_from=None, date_to=None, status=None):
        where, params = self._filters(date_from, date_to, status)
        clause = where + (" AND " if where else "WHERE ") + "o.order_status != 'canceled'"
        rows = self.conn.execute(
            f"""
            SELECT COALESCE(p.product_category_name,'unknown') AS category, SUM(oi.price) AS sales
            FROM orders o
            JOIN order_items oi ON oi.order_id=o.order_id
            LEFT JOIN products p ON p.product_id=oi.product_id
            {clause} GROUP BY category ORDER BY sales DESC
        """,
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def top_categories(self, limit=10, date_from=None, date_to=None, status=None):
        return self.category_sales(date_from, date_to, status)[:limit]

    def status_distribution(self, date_from=None, date_to=None):
        where, params = self._filters(date_from, date_to)
        rows = self.conn.execute(
            f"""
            SELECT order_status, COUNT(*) AS orders FROM orders o {where}
            GROUP BY order_status ORDER BY orders DESC
        """,
            params,
        ).fetchall()
        return [dict(r) for r in rows]
