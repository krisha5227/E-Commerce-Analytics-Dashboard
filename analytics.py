"""
Analytical engine for E-Commerce Dashboard.
Combines optimized SQL queries with Pandas for:
- Executive KPIs (Revenue, Profit, Margin, AOV, Returning Customer Revenue)
- Sales Trends & Seasonality
- Category & Product Profitability
- RFM Customer Segmentation
- Customer Contribution / Pareto 80-20 Analysis
- Monthly Cohort Retention Matrix
"""

import pandas as pd
import numpy as np
from datetime import datetime
from database import get_db

def _build_date_filter(start_date=None, end_date=None, date_col="order_date"):
    """Helper to build SQL date filter clauses and parameters."""
    clauses = []
    params = []
    if start_date:
        clauses.append(f"{date_col} >= ?")
        params.append(f"{start_date} 00:00:00")
    if end_date:
        clauses.append(f"{date_col} <= ?")
        params.append(f"{end_date} 23:59:59")
    
    where_sql = (" AND " + " AND ".join(clauses)) if clauses else ""
    return where_sql, params

def get_kpis(start_date=None, end_date=None):
    """
    Computes primary executive KPIs:
    - Total Revenue, Profit, Margin %
    - Average Order Value (AOV)
    - Total Orders & Unique Customers
    - Returning Customer Share of Revenue
    """
    with get_db() as conn:
        date_clause, params = _build_date_filter(start_date, end_date)
        
        # Pull completed orders for KPI calculations
        sql = f"""
            SELECT id, customer_id, order_date, total_amount, total_profit
            FROM orders
            WHERE status = 'Completed' {date_clause}
            ORDER BY customer_id, order_date ASC
        """
        df = pd.read_sql_query(sql, conn, params=params)

    if df.empty:
        return {
            "total_revenue": 0.0,
            "total_profit": 0.0,
            "profit_margin": 0.0,
            "aov": 0.0,
            "total_orders": 0,
            "unique_customers": 0,
            "returning_orders": 0,
            "returning_revenue": 0.0,
            "returning_rev_pct": 0.0,
            "repeat_customers_count": 0,
            "repeat_customers_pct": 0.0,
        }

    total_revenue = float(df["total_amount"].sum())
    total_profit = float(df["total_profit"].sum())
    total_orders = int(len(df))
    unique_customers = int(df["customer_id"].nunique())
    profit_margin = round((total_profit / total_revenue * 100), 2) if total_revenue > 0 else 0.0
    aov = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0

    # Returning-customer analysis
    # Order sequence number per customer
    df["order_seq"] = df.groupby("customer_id").cumcount() + 1
    returning_df = df[df["order_seq"] > 1]
    returning_orders = int(len(returning_df))
    returning_revenue = float(returning_df["total_amount"].sum())
    returning_rev_pct = round((returning_revenue / total_revenue * 100), 2) if total_revenue > 0 else 0.0

    # Customers with more than 1 order
    order_counts_by_cust = df.groupby("customer_id").size()
    repeat_customers_count = int((order_counts_by_cust > 1).sum())
    repeat_customers_pct = round((repeat_customers_count / unique_customers * 100), 2) if unique_customers > 0 else 0.0

    return {
        "total_revenue": round(total_revenue, 2),
        "total_profit": round(total_profit, 2),
        "profit_margin": profit_margin,
        "aov": aov,
        "total_orders": total_orders,
        "unique_customers": unique_customers,
        "returning_orders": returning_orders,
        "returning_revenue": round(returning_revenue, 2),
        "returning_rev_pct": returning_rev_pct,
        "repeat_customers_count": repeat_customers_count,
        "repeat_customers_pct": repeat_customers_pct,
    }

def get_sales_trend(start_date=None, end_date=None):
    """
    Returns aggregated revenue, profit, and order volume trend over time.
    Uses monthly grouping by default.
    """
    date_clause, params = _build_date_filter(start_date, end_date)
    with get_db() as conn:
        sql = f"""
            SELECT 
                strftime('%Y-%m', order_date) as period,
                COUNT(id) as order_count,
                SUM(total_amount) as revenue,
                SUM(total_profit) as profit
            FROM orders
            WHERE status = 'Completed' {date_clause}
            GROUP BY period
            ORDER BY period ASC
        """
        df = pd.read_sql_query(sql, conn, params=params)

    if df.empty:
        return {"labels": [], "revenue": [], "profit": [], "orders": [], "aov": []}

    df["revenue"] = df["revenue"].round(2)
    df["profit"] = df["profit"].round(2)
    df["aov"] = (df["revenue"] / df["order_count"]).round(2)

    return {
        "labels": df["period"].tolist(),
        "revenue": df["revenue"].tolist(),
        "profit": df["profit"].tolist(),
        "orders": df["order_count"].tolist(),
        "aov": df["aov"].tolist(),
    }

def get_category_breakdown(start_date=None, end_date=None):
    """
    Returns sales, profit, margin %, and items sold aggregated by product category.
    """
    date_clause, params = _build_date_filter(start_date, end_date, date_col="o.order_date")
    with get_db() as conn:
        sql = f"""
            SELECT 
                p.category,
                SUM(oi.quantity) as units_sold,
                SUM(oi.total_price) as revenue,
                SUM(oi.total_profit) as profit
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            JOIN products p ON oi.product_id = p.id
            WHERE o.status = 'Completed' {date_clause}
            GROUP BY p.category
            ORDER BY revenue DESC
        """
        df = pd.read_sql_query(sql, conn, params=params)

    if df.empty:
        return []

    total_revenue = df["revenue"].sum()
    df["revenue"] = df["revenue"].round(2)
    df["profit"] = df["profit"].round(2)
    df["margin_pct"] = ((df["profit"] / df["revenue"]) * 100).round(2)
    df["rev_share_pct"] = ((df["revenue"] / total_revenue) * 100).round(2) if total_revenue > 0 else 0.0

    return df.to_dict(orient="records")

def get_top_products(start_date=None, end_date=None, limit=10):
    """
    Top best-selling products ranked by total revenue.
    """
    date_clause, params = _build_date_filter(start_date, end_date, date_col="o.order_date")
    params.append(limit)
    with get_db() as conn:
        sql = f"""
            SELECT 
                p.id,
                p.name,
                p.category,
                p.retail_price,
                SUM(oi.quantity) as units_sold,
                SUM(oi.total_price) as revenue,
                SUM(oi.total_profit) as profit
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            JOIN products p ON oi.product_id = p.id
            WHERE o.status = 'Completed' {date_clause}
            GROUP BY p.id, p.name, p.category, p.retail_price
            ORDER BY revenue DESC
            LIMIT ?
        """
        df = pd.read_sql_query(sql, conn, params=params)

    if df.empty:
        return []

    df["revenue"] = df["revenue"].round(2)
    df["profit"] = df["profit"].round(2)
    df["margin_pct"] = ((df["profit"] / df["revenue"]) * 100).round(2)
    return df.to_dict(orient="records")

def get_rfm_segmentation():
    """
    Performs Recency, Frequency, Monetary (RFM) segmentation on the customer base.
    Calculates quintiles for R, F, M and assigns actionable marketing/sales segments.
    """
    with get_db() as conn:
        sql = """
            SELECT 
                c.id as customer_id,
                c.name,
                c.email,
                c.city,
                c.country,
                MAX(o.order_date) as last_order_date,
                COUNT(o.id) as frequency,
                SUM(o.total_amount) as monetary
            FROM customers c
            JOIN orders o ON c.id = o.customer_id
            WHERE o.status = 'Completed'
            GROUP BY c.id
        """
        df = pd.read_sql_query(sql, conn)

    if df.empty:
        return {"summary": [], "segments": {}}

    # Reference date is max order date + 1 day
    df["last_order_date"] = pd.to_datetime(df["last_order_date"])
    ref_date = df["last_order_date"].max() + pd.Timedelta(days=1)
    df["recency"] = (ref_date - df["last_order_date"]).dt.days

    # Scoring 1-5 (Higher is better for Frequency & Monetary, Lower is better for Recency)
    # Using rank(pct=True) to reliably handle ties
    df["r_score"] = pd.qcut(df["recency"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
    df["f_score"] = pd.qcut(df["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    df["m_score"] = pd.qcut(df["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    df["rfm_score"] = df["r_score"] * 100 + df["f_score"] * 10 + df["m_score"]

    def assign_segment(row):
        r, f, m = row["r_score"], row["f_score"], row["m_score"]
        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        elif r >= 3 and f >= 3 and m >= 3:
            return "Loyal Customers"
        elif r >= 4 and f <= 2:
            return "Promising / New"
        elif r >= 3 and f <= 3:
            return "Potential Loyalists"
        elif r <= 2 and f >= 3:
            return "At Risk"
        elif r <= 2 and f <= 2:
            return "Hibernating / Lost"
        else:
            return "Needs Attention"

    df["segment"] = df.apply(assign_segment, axis=1)

    # Segment Aggregations
    summary = df.groupby("segment").agg(
        customer_count=("customer_id", "count"),
        total_revenue=("monetary", "sum"),
        avg_monetary=("monetary", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_recency=("recency", "mean"),
    ).reset_index()

    total_cust = len(df)
    total_rev = df["monetary"].sum()

    summary["cust_share_pct"] = ((summary["customer_count"] / total_cust) * 100).round(2)
    summary["rev_share_pct"] = ((summary["total_revenue"] / total_rev) * 100).round(2)
    summary["total_revenue"] = summary["total_revenue"].round(2)
    summary["avg_monetary"] = summary["avg_monetary"].round(2)
    summary["avg_frequency"] = summary["avg_frequency"].round(1)
    summary["avg_recency"] = summary["avg_recency"].round(1)

    # Sort in order of strategic value
    segment_order = [
        "Champions", "Loyal Customers", "Potential Loyalists",
        "Promising / New", "Needs Attention", "At Risk", "Hibernating / Lost"
    ]
    summary["sort_order"] = summary["segment"].map(lambda x: segment_order.index(x) if x in segment_order else 99)
    summary = summary.sort_values("sort_order").drop(columns=["sort_order"])

    return {
        "summary": summary.to_dict(orient="records"),
        "total_analyzed_customers": total_cust,
        "total_revenue": round(total_rev, 2)
    }

def get_customer_pareto():
    """
    Calculates Pareto / 80-20 customer contribution:
    Cumulative % of customers vs Cumulative % of revenue.
    """
    with get_db() as conn:
        sql = """
            SELECT customer_id, SUM(total_amount) as total_spent
            FROM orders
            WHERE status = 'Completed'
            GROUP BY customer_id
            ORDER BY total_spent DESC
        """
        df = pd.read_sql_query(sql, conn)

    if df.empty:
        return {"deciles": [], "top_10_pct_rev": 0.0, "top_20_pct_rev": 0.0}

    total_rev = df["total_spent"].sum()
    total_cust = len(df)

    df["cum_rev"] = df["total_spent"].cumsum()
    df["cum_rev_pct"] = (df["cum_rev"] / total_rev * 100).round(2)
    df["cum_cust_pct"] = (np.arange(1, total_cust + 1) / total_cust * 100).round(2)

    top_10_idx = max(0, int(total_cust * 0.10) - 1)
    top_20_idx = max(0, int(total_cust * 0.20) - 1)

    top_10_pct_rev = float(df.iloc[top_10_idx]["cum_rev_pct"]) if top_10_idx < total_cust else 0.0
    top_20_pct_rev = float(df.iloc[top_20_idx]["cum_rev_pct"]) if top_20_idx < total_cust else 0.0

    # Decile points (10%, 20%, ... 100%)
    deciles = []
    for p in range(10, 101, 10):
        idx = min(int(round(total_cust * (p / 100))) - 1, total_cust - 1)
        deciles.append({
            "customer_pct": p,
            "revenue_pct": float(df.iloc[idx]["cum_rev_pct"])
        })

    return {
        "deciles": deciles,
        "top_10_pct_rev": top_10_pct_rev,
        "top_20_pct_rev": top_20_pct_rev,
        "total_customers": total_cust,
        "total_revenue": round(total_rev, 2)
    }

def get_cohort_retention():
    """
    Calculates monthly customer retention cohorts over 12 months.
    Cohort defined by customer's initial order month.
    """
    with get_db() as conn:
        sql = """
            SELECT customer_id, order_date
            FROM orders
            WHERE status = 'Completed'
            ORDER BY order_date ASC
        """
        df = pd.read_sql_query(sql, conn)

    if df.empty:
        return {"cohorts": [], "months": []}

    df["order_date"] = pd.to_datetime(df["order_date"])
    df["order_month"] = df["order_date"].dt.to_period("M")
    
    # First purchase month per customer
    df["cohort_month"] = df.groupby("customer_id")["order_month"].transform("min")

    # Calculate month index offset from cohort acquisition
    df["cohort_index"] = (df["order_month"].dt.year - df["cohort_month"].dt.year) * 12 + \
                         (df["order_month"].dt.month - df["cohort_month"].dt.month)

    # Filter to cohort index up to 11 months
    cohort_data = df.groupby(["cohort_month", "cohort_index"])["customer_id"].nunique().reset_index()
    cohort_pivot = cohort_data.pivot(index="cohort_month", columns="cohort_index", values="customer_id")

    # Cohort base size (Month 0)
    cohort_sizes = cohort_pivot.iloc[:, 0]
    retention_matrix = cohort_pivot.divide(cohort_sizes, axis=0) * 100

    cohorts_list = []
    # Format for JSON response
    # Take first 12 cohorts for clear display
    max_cohorts = retention_matrix.head(12)
    for cohort_period, row in max_cohorts.iterrows():
        size = int(cohort_sizes.loc[cohort_period])
        rates = []
        for col in range(12):
            if col in row and not pd.isna(row[col]):
                rates.append(round(float(row[col]), 1))
            else:
                rates.append(None)
        cohorts_list.append({
            "cohort": str(cohort_period),
            "size": size,
            "rates": rates
        })

    return {
        "cohorts": cohorts_list,
        "months": [f"M+{i}" for i in range(12)]
    }

def get_product_catalog(category=None, sort_by="revenue", direction="desc"):
    """
    Returns full product performance catalog.
    """
    where_sql = "WHERE p.category = ?" if category and category != "All" else ""
    params = [category] if category and category != "All" else []

    with get_db() as conn:
        sql = f"""
            SELECT 
                p.id,
                p.name,
                p.category,
                p.retail_price,
                p.cost_price,
                p.stock_quantity,
                COALESCE(SUM(oi.quantity), 0) as units_sold,
                COALESCE(SUM(oi.total_price), 0) as revenue,
                COALESCE(SUM(oi.total_profit), 0) as profit
            FROM products p
            LEFT JOIN order_items oi ON p.id = oi.product_id
            LEFT JOIN orders o ON oi.order_id = o.id AND o.status = 'Completed'
            {where_sql}
            GROUP BY p.id
        """
        df = pd.read_sql_query(sql, conn, params=params)

    if df.empty:
        return []

    df["revenue"] = df["revenue"].round(2)
    df["profit"] = df["profit"].round(2)
    df["margin_pct"] = np.where(df["revenue"] > 0, ((df["profit"] / df["revenue"]) * 100).round(2), 0.0)

    # Dynamic sorting
    valid_cols = ["revenue", "profit", "units_sold", "retail_price", "margin_pct", "stock_quantity", "name"]
    sort_col = sort_by if sort_by in valid_cols else "revenue"
    is_ascending = (direction.lower() == "asc")
    df = df.sort_values(by=sort_col, ascending=is_ascending)

    return df.to_dict(orient="records")

def get_orders_ledger(page=1, per_page=15, search="", status="", start_date=None, end_date=None):
    """
    Searchable, filterable, and paginated orders ledger.
    """
    offset = (page - 1) * per_page
    where_clauses = []
    params = []

    if search:
        where_clauses.append("(c.name LIKE ? OR c.email LIKE ? OR CAST(o.id AS TEXT) LIKE ?)")
        s_param = f"%{search}%"
        params.extend([s_param, s_param, s_param])
    
    if status and status != "All":
        where_clauses.append("o.status = ?")
        params.append(status)

    if start_date:
        where_clauses.append("o.order_date >= ?")
        params.append(f"{start_date} 00:00:00")
    if end_date:
        where_clauses.append("o.order_date <= ?")
        params.append(f"{end_date} 23:59:59")

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    with get_db() as conn:
        count_sql = f"""
            SELECT COUNT(o.id) as total_count
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            {where_sql}
        """
        total_records = pd.read_sql_query(count_sql, conn, params=params).iloc[0]["total_count"]

        # Ledger query with pagination
        query_params = list(params) + [per_page, offset]
        sql = f"""
            SELECT 
                o.id as order_id,
                o.order_date,
                o.status,
                o.payment_method,
                o.total_amount,
                o.total_profit,
                c.id as customer_id,
                c.name as customer_name,
                c.email as customer_email,
                (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) as items_count
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            {where_sql}
            ORDER BY o.order_date DESC
            LIMIT ? OFFSET ?
        """
        df = pd.read_sql_query(sql, conn, params=query_params)

    records = df.to_dict(orient="records") if not df.empty else []
    total_pages = max(1, int(np.ceil(total_records / per_page)))

    return {
        "orders": records,
        "total_records": int(total_records),
        "total_pages": total_pages,
        "current_page": page,
        "per_page": per_page
    }

def get_order_detail(order_id):
    """
    Returns full order details with individual line items.
    """
    with get_db() as conn:
        order_sql = """
            SELECT 
                o.id as order_id,
                o.order_date,
                o.status,
                o.payment_method,
                o.shipping_cost,
                o.total_amount,
                o.total_profit,
                c.id as customer_id,
                c.name as customer_name,
                c.email as customer_email,
                c.city as customer_city,
                c.country as customer_country
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            WHERE o.id = ?
        """
        order_row = conn.execute(order_sql, (order_id,)).fetchone()
        if not order_row:
            return None

        items_sql = """
            SELECT 
                oi.id,
                oi.quantity,
                oi.unit_price,
                oi.unit_cost,
                oi.total_price,
                oi.total_profit,
                p.id as product_id,
                p.name as product_name,
                p.category
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        """
        items_rows = conn.execute(items_sql, (order_id,)).fetchall()

    return {
        "order": dict(order_row),
        "items": [dict(r) for r in items_rows]
    }

def get_customer_profile(customer_id):
    """
    Returns single customer drill-down data: spend, order history, RFM profile.
    """
    with get_db() as conn:
        cust_row = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
        if not cust_row:
            return None

        orders_sql = """
            SELECT 
                id as order_id,
                order_date,
                status,
                payment_method,
                total_amount,
                total_profit
            FROM orders
            WHERE customer_id = ?
            ORDER BY order_date DESC
        """
        orders_rows = conn.execute(orders_sql, (customer_id,)).fetchall()

    orders_list = [dict(r) for r in orders_rows]
    completed_orders = [o for o in orders_list if o["status"] == "Completed"]
    
    total_spent = sum(o["total_amount"] for o in completed_orders)
    total_profit = sum(o["total_profit"] for o in completed_orders)
    order_count = len(completed_orders)
    aov = round(total_spent / order_count, 2) if order_count > 0 else 0.0

    return {
        "customer": dict(cust_row),
        "metrics": {
            "total_spent": round(total_spent, 2),
            "total_profit": round(total_profit, 2),
            "order_count": order_count,
            "aov": aov,
            "first_order": completed_orders[-1]["order_date"] if completed_orders else "N/A",
            "last_order": completed_orders[0]["order_date"] if completed_orders else "N/A",
        },
        "orders": orders_list
    }
