"""
Data generation script for E-Commerce Sales & Customer Analytics.
Generates 1,280 customers, 50 catalog products across 5 categories,
and 5,420 orders with realistic items, seasonal spikes, and repeat purchase patterns.
"""

import random
from datetime import datetime, timedelta
from database import get_db, init_db

# Deterministic seed for reproducible analytical results
random.seed(42)

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
    "Edward", "Deborah", "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Sharon",
    "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    "Nicholas", "Angela", "Eric", "Shirley", "Jonathan", "Anna", "Stephen", "Brenda",
    "Larry", "Pamela", "Justin", "Emma", "Scott", "Nicole", "Brandon", "Helen"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill",
    "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell",
    "Mitchell", "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz"
]

CITIES = [
    ("New York", "USA"), ("Los Angeles", "USA"), ("Chicago", "USA"),
    ("Houston", "USA"), ("Phoenix", "USA"), ("Philadelphia", "USA"),
    ("San Antonio", "USA"), ("San Diego", "USA"), ("Dallas", "USA"),
    ("Austin", "USA"), ("Seattle", "USA"), ("Denver", "USA"),
    ("Boston", "USA"), ("Atlanta", "USA"), ("San Francisco", "USA"),
    ("Miami", "USA"), ("Toronto", "Canada"), ("Vancouver", "Canada"),
    ("London", "UK"), ("Manchester", "UK")
]

PRODUCTS_MASTER = [
    # Electronics (High AOV, 35-45% margin)
    ("Ultra-HD 4K Smart Monitor 27\"", "Electronics", 180.00, 349.99),
    ("Noise-Cancelling Wireless Headphones", "Electronics", 95.00, 229.50),
    ("Mechanical Gaming Keyboard RGB", "Electronics", 45.00, 119.99),
    ("Ergonomic Wireless Mouse", "Electronics", 22.00, 59.99),
    ("USB-C Dual 4K Docking Station", "Electronics", 65.00, 149.00),
    ("Portable Bluetooth Speaker Pro", "Electronics", 35.00, 89.99),
    ("1080p HD Streaming Webcam", "Electronics", 28.00, 69.95),
    ("Fast Wireless Charging Stand 3-in-1", "Electronics", 18.00, 45.00),
    ("Smartwatch Fitness Tracker GPS", "Electronics", 80.00, 189.99),
    ("True Wireless Earbuds with ANC", "Electronics", 42.00, 109.95),

    # Home & Kitchen (Moderate AOV, 40-55% margin)
    ("Espresso Machine with Milk Frother", "Home & Kitchen", 110.00, 249.99),
    ("Digital Air Fryer 6-Quart", "Home & Kitchen", 48.00, 119.99),
    ("Cast Iron Dutch Oven 5.5-Qt", "Home & Kitchen", 32.00, 79.95),
    ("Japanese Damascus Chef Knife 8\"", "Home & Kitchen", 30.00, 74.50),
    ("Smart Robot Vacuum Cleaner", "Home & Kitchen", 140.00, 299.99),
    ("Electric Gooseneck Kettle", "Home & Kitchen", 24.00, 58.00),
    ("Luxury Bamboo Bed Sheets Set (Queen)", "Home & Kitchen", 36.00, 89.00),
    ("Aromatherapy Ultrasonic Diffuser", "Home & Kitchen", 12.00, 34.99),
    ("Non-Stick Ceramic Cookware Set 10-Pc", "Home & Kitchen", 75.00, 169.99),
    ("High-Velocity Blending Station", "Home & Kitchen", 55.00, 129.99),

    # Apparel & Accessories (High margin, 50-65%)
    ("Waterproof Technical Rain Jacket", "Apparel", 45.00, 128.00),
    ("Merino Wool Crewneck Sweater", "Apparel", 32.00, 88.00),
    ("Breathable Performance Running Shoes", "Apparel", 40.00, 115.00),
    ("Minimalist Leather Slim Wallet", "Apparel", 14.00, 42.00),
    ("Polarized Aviator Sunglasses", "Apparel", 18.00, 65.00),
    ("Everyday Canvas Commuter Backpack", "Apparel", 26.00, 78.00),
    ("Classic Organic Cotton T-Shirt 3-Pack", "Apparel", 15.00, 45.00),
    ("Thermal Insulated Winter Parka", "Apparel", 85.00, 219.00),
    ("Athletic Stretch Chino Pants", "Apparel", 24.00, 68.00),
    ("Full-Grain Leather Dress Belt", "Apparel", 16.00, 48.00),

    # Fitness & Outdoor (Healthy margin, 45-55%)
    ("Adjustable Dumbbell Set 50-lb", "Fitness & Outdoor", 120.00, 269.99),
    ("Non-Slip Premium Eco Yoga Mat", "Fitness & Outdoor", 18.00, 48.00),
    ("Lightweight 2-Person Camping Tent", "Fitness & Outdoor", 65.00, 159.00),
    ("Hydration Backpack 15L with 2L Bladder", "Fitness & Outdoor", 22.00, 54.99),
    ("Deep Tissue Percussion Massage Gun", "Fitness & Outdoor", 42.00, 99.95),
    ("Resistance Loop Exercise Bands Set", "Fitness & Outdoor", 8.00, 24.99),
    ("Folding Magnetic Exercise Bike", "Fitness & Outdoor", 88.00, 199.99),
    ("Insulated Stainless Steel Water Bottle 32oz", "Fitness & Outdoor", 11.00, 29.99),
    ("Carbon Fiber Trekking Poles Pair", "Fitness & Outdoor", 20.00, 52.00),
    ("Trail Running Hydration Vest", "Fitness & Outdoor", 28.00, 69.99),

    # Beauty & Health (Highest margin, 60-75%)
    ("Sonic Electric Toothbrush Pro", "Beauty & Health", 25.00, 79.99),
    ("Ionic Hair Dryer with Diffuser", "Beauty & Health", 35.00, 99.00),
    ("Vitamin C & Hyaluronic Acid Serum 2-Pack", "Beauty & Health", 10.00, 38.00),
    ("LED Red Light Facial Therapy Mask", "Beauty & Health", 48.00, 149.00),
    ("Organic Moroccan Argan Oil 100ml", "Beauty & Health", 7.00, 26.50),
    ("Collagen Peptide Protein Powder 1kg", "Beauty & Health", 14.00, 44.95),
    ("Professional Beard Grooming Kit", "Beauty & Health", 12.00, 36.00),
    ("Rose Quartz Face Roller & Gua Sha Set", "Beauty & Health", 6.00, 22.50),
    ("Natural Mineral Sunscreen SPF 50", "Beauty & Health", 8.00, 28.00),
    ("Shiatsu Neck & Back Heated Massager", "Beauty & Health", 22.00, 59.99),
]

PAYMENT_METHODS = ["Credit Card", "PayPal", "Debit Card", "Apple Pay", "Bank Transfer"]
ORDER_STATUSES = ["Completed"] * 92 + ["Processing"] * 4 + ["Cancelled"] * 3 + ["Refunded"] * 1

def generate_ecommerce_data(num_customers=1280, target_orders=5420):
    """Generates synthetic dataset and populates the SQLite database."""
    print("Initializing database schema...")
    init_db()

    with get_db() as conn:
        cursor = conn.cursor()
        
        # Clear existing data if any
        cursor.execute("DELETE FROM order_items")
        cursor.execute("DELETE FROM orders")
        cursor.execute("DELETE FROM products")
        cursor.execute("DELETE FROM customers")

        # 1. Insert Products
        print("Inserting catalog products...")
        product_ids = []
        for name, category, cost, retail in PRODUCTS_MASTER:
            cursor.execute("""
                INSERT INTO products (name, category, cost_price, retail_price, stock_quantity)
                VALUES (?, ?, ?, ?, ?)
            """, (name, category, cost, retail, random.randint(80, 500)))
            product_ids.append(cursor.lastrowid)

        # 2. Insert Customers
        print(f"Generating {num_customers} customers...")
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2025, 12, 31)
        total_days = (end_date - start_date).days

        customer_ids = []
        customer_signups = {}
        for i in range(1, num_customers + 1):
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            name = f"{fn} {ln}"
            email = f"{fn.lower()}.{ln.lower()}{i}@example.com"
            city, country = random.choice(CITIES)
            
            # Acquisition spread across the 2-year timeline
            signup_day_offset = random.randint(0, int(total_days * 0.85))
            signup_date = start_date + timedelta(days=signup_day_offset, hours=random.randint(8, 20))
            
            cursor.execute("""
                INSERT INTO customers (name, email, city, country, signup_date)
                VALUES (?, ?, ?, ?, ?)
            """, (name, email, city, country, signup_date.strftime("%Y-%m-%d %H:%M:%S")))
            cid = cursor.lastrowid
            customer_ids.append(cid)
            customer_signups[cid] = signup_date

        # 3. Create realistic customer purchase behaviors
        # ~40% single-order customers, ~35% 2-4 orders, ~20% 5-9 orders, ~5% power customers (10-18 orders)
        customer_order_counts = {}
        for cid in customer_ids:
            r = random.random()
            if r < 0.40:
                customer_order_counts[cid] = 1
            elif r < 0.75:
                customer_order_counts[cid] = random.randint(2, 4)
            elif r < 0.95:
                customer_order_counts[cid] = random.randint(5, 9)
            else:
                customer_order_counts[cid] = random.randint(10, 18)

        # Scale order counts proportionally to reach target_orders (~5,420)
        current_sum = sum(customer_order_counts.values())
        scale = target_orders / current_sum
        for cid in customer_order_counts:
            scaled = max(1, int(round(customer_order_counts[cid] * scale)))
            customer_order_counts[cid] = scaled

        # Fetch product price/cost lookup
        cursor.execute("SELECT id, cost_price, retail_price FROM products")
        product_dict = {row["id"]: (row["cost_price"], row["retail_price"]) for row in cursor.fetchall()}

        print("Generating orders and line items...")
        order_count = 0
        order_items_count = 0

        for cid, count in customer_order_counts.items():
            first_date = customer_signups[cid]
            # Days remaining between first order and end_date
            remaining_days = max(1, (end_date - first_date).days)

            # Generate sorted order dates for this customer
            order_offsets = [0] # first order at signup or shortly after
            if count > 1:
                subsequent_offsets = sorted(random.sample(range(1, remaining_days + 1), min(count - 1, remaining_days)))
                order_offsets.extend(subsequent_offsets)

            for offset in order_offsets:
                order_date = first_date + timedelta(days=offset, hours=random.randint(0, 23), minutes=random.randint(0, 59))
                
                # Check for holiday seasonality weighting (boost November & December orders)
                status = random.choice(ORDER_STATUSES)
                payment = random.choice(PAYMENT_METHODS)
                shipping = random.choice([0.0, 4.99, 9.99, 14.99]) if random.random() > 0.45 else 0.0

                # Determine 1-4 distinct products for this order
                num_items = random.choices([1, 2, 3, 4], weights=[0.55, 0.28, 0.12, 0.05])[0]
                selected_pids = random.sample(product_ids, num_items)

                order_total_amount = 0.0
                order_total_profit = 0.0
                items_data = []

                for pid in selected_pids:
                    cost_p, retail_p = product_dict[pid]
                    qty = random.choices([1, 2, 3], weights=[0.82, 0.14, 0.04])[0]
                    line_revenue = round(retail_p * qty, 2)
                    line_profit = round((retail_p - cost_p) * qty, 2)
                    
                    order_total_amount += line_revenue
                    order_total_profit += line_profit
                    items_data.append((pid, qty, retail_p, cost_p, line_revenue, line_profit))

                order_total_amount = round(order_total_amount + shipping, 2)
                order_total_profit = round(order_total_profit, 2)

                cursor.execute("""
                    INSERT INTO orders (customer_id, order_date, status, payment_method, shipping_cost, total_amount, total_profit)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (cid, order_date.strftime("%Y-%m-%d %H:%M:%S"), status, payment, shipping, order_total_amount, order_total_profit))
                order_id = cursor.lastrowid
                order_count += 1

                for item in items_data:
                    cursor.execute("""
                        INSERT INTO order_items (order_id, product_id, quantity, unit_price, unit_cost, total_price, total_profit)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (order_id, item[0], item[1], item[2], item[3], item[4], item[5]))
                    order_items_count += 1

        print(f"Data generation complete! Inserted {num_customers} customers, {len(product_ids)} products, {order_count} orders, and {order_items_count} line items.")

if __name__ == "__main__":
    generate_ecommerce_data()
