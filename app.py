"""
Flask Web Application for E-Commerce Sales & Customer Analytics Dashboard.
Serves interactive dashboard views and REST API endpoints.
"""

import io
import csv
from flask import Flask, render_template, request, jsonify, Response
from database import init_db, check_db_seeded
from generate_data import generate_ecommerce_data
import analytics

app = Flask(__name__)

# Ensure database is initialized and seeded on startup
with app.app_context():
    init_db()
    if not check_db_seeded():
        print("Database not seeded or incomplete. Seeding synthetic data...")
        generate_ecommerce_data()

# -------------------------------------------------------------
# HTML Page Routes
# -------------------------------------------------------------

@app.route("/")
def index():
    """Executive Sales & Revenue Overview Dashboard."""
    return render_template("overview.html", active_page="overview")

@app.route("/customers")
def customers():
    """Customer Analytics: RFM Segmentation & Cohort Retention."""
    return render_template("customers.html", active_page="customers")

@app.route("/products")
def products():
    """Product Performance & Profitability Catalog."""
    return render_template("products.html", active_page="products")

@app.route("/orders")
def orders():
    """Interactive Orders Ledger and Customer Explorer."""
    return render_template("orders.html", active_page="orders")

# -------------------------------------------------------------
# REST API Endpoints (JSON)
# -------------------------------------------------------------

@app.route("/api/overview")
def api_overview():
    """Returns all KPI metrics, sales trends, and category distribution for overview."""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    kpis = analytics.get_kpis(start_date, end_date)
    trend = analytics.get_sales_trend(start_date, end_date)
    categories = analytics.get_category_breakdown(start_date, end_date)
    top_products = analytics.get_top_products(start_date, end_date, limit=8)

    return jsonify({
        "kpis": kpis,
        "trend": trend,
        "categories": categories,
        "top_products": top_products
    })

@app.route("/api/customer-analytics")
def api_customer_analytics():
    """Returns RFM segmentation, Pareto distribution, and Cohort retention matrix."""
    rfm = analytics.get_rfm_segmentation()
    pareto = analytics.get_customer_pareto()
    cohorts = analytics.get_cohort_retention()

    return jsonify({
        "rfm": rfm,
        "pareto": pareto,
        "cohorts": cohorts
    })

@app.route("/api/products")
def api_products():
    """Returns product catalog performance data."""
    category = request.args.get("category", "All")
    sort_by = request.args.get("sort_by", "revenue")
    direction = request.args.get("direction", "desc")

    data = analytics.get_product_catalog(category, sort_by, direction)
    return jsonify({"products": data})

@app.route("/api/orders")
def api_orders():
    """Returns paginated, searchable, and filtered orders ledger."""
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 15))
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "All")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    data = analytics.get_orders_ledger(
        page=page,
        per_page=per_page,
        search=search,
        status=status,
        start_date=start_date,
        end_date=end_date
    )
    return jsonify(data)

@app.route("/api/order/<int:order_id>")
def api_order_detail(order_id):
    """Returns single order line items and customer info."""
    data = analytics.get_order_detail(order_id)
    if not data:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(data)

@app.route("/api/customer/<int:customer_id>")
def api_customer_profile(customer_id):
    """Returns customer profile, lifetime metrics, and order history."""
    data = analytics.get_customer_profile(customer_id)
    if not data:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify(data)

@app.route("/api/export-csv")
def export_csv():
    """Exports orders or products report to downloadable CSV."""
    export_type = request.args.get("type", "orders")

    output = io.StringIO()
    writer = csv.writer(output)

    if export_type == "products":
        writer.writerow(["Product ID", "Name", "Category", "Retail Price", "Cost Price", "Stock", "Units Sold", "Revenue", "Profit", "Margin %"])
        products_data = analytics.get_product_catalog()
        for p in products_data:
            writer.writerow([
                p["id"], p["name"], p["category"], p["retail_price"],
                p["cost_price"], p["stock_quantity"], p["units_sold"],
                p["revenue"], p["profit"], p["margin_pct"]
            ])
        filename = "ecommerce_products_analytics.csv"
    else:
        # Default: Export orders
        writer.writerow(["Order ID", "Date", "Customer Name", "Customer Email", "Status", "Payment Method", "Items Count", "Revenue ($)", "Profit ($)"])
        orders_data = analytics.get_orders_ledger(page=1, per_page=10000)
        for o in orders_data["orders"]:
            writer.writerow([
                o["order_id"], o["order_date"], o["customer_name"],
                o["customer_email"], o["status"], o["payment_method"],
                o["items_count"], o["total_amount"], o["total_profit"]
            ])
        filename = "ecommerce_orders_export.csv"

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
