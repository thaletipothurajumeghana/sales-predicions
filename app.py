from flask import Flask, render_template, request, redirect, session
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime
import hashlib

# Import model
from retail_model import RetailAI

app = Flask(__name__)
app.secret_key = "supersecretkey"

ADMIN_EMAIL = "thaletipothurajumeghana@gmail.com"

# =============================
# INITIALIZE AI SYSTEM
# =============================

ai_system = None


def initialize_ai():
    global ai_system
    ai_system = RetailAI("modified_sales_dataset.csv")
    
    # Skip database update during startup to avoid breaking XGBoost
    print("AI initialized with CSV data only (database update skipped at startup)")
    
    ai_system.train_sales_model()
    ai_system.train_inventory_risk_model()
    print("AI MODELS LOADED SUCCESSFULLY")


# =============================
# DATABASE SETUP
# =============================

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        product TEXT,
        price REAL,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()
initialize_ai()

# =============================
# HOME
# =============================

@app.route("/")
def home():
    return render_template("home.html")


# =============================
# LOGIN
# =============================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = hashlib.sha256(request.form["password"].encode()).hexdigest()

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = email

            if email == ADMIN_EMAIL:
                return redirect("/dashboard")
            else:
                return redirect("/shop")

    return render_template("login.html")


# =============================
# REGISTER
# =============================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = hashlib.sha256(request.form["password"].encode()).hexdigest()

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute(
            "INSERT INTO users (name,email,password) VALUES (?,?,?)",
            (name, email, password)
        )

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register.html")


# =============================
# SHOP
# =============================

@app.route("/shop")
def shop():
    if "user" not in session:
        return redirect("/")

    query = request.args.get("search")

    products = [

        # ---------------- Furniture ----------------
        {"name": "Modern Sofa", "category": "Furniture", "price": 799,
         "image": "https://activehomecentre.com/cdn/shop/collections/WhatsApp_Image_2021-04-22_at_3.06.53_PM_3.jpg?v=1757011624"},

        {"name": "Luxury Chair", "category": "Furniture", "price": 499,
         "image": "https://www.estre.in/cdn/shop/files/2-min_2d969ef7-e5ee-4cdd-a08a-6b0871211bab_533x.jpg?v=1743762665"},

        {"name": "Bed", "category": "Furniture", "price": 569,
         "image": "https://cdn.shopify.com/s/files/1/0408/7365/6486/files/newmobilebed.jpg?v=1759387935"},

        # ---------------- Groceries ----------------
        {"name": "Fresh Fruits & Vegetables", "category": "Groceries", "price": 29,
         "image": "https://www.lalpathlabs.com/blog/wp-content/uploads/2019/01/Fruits-and-Vegetables.jpg"},

        {"name": "Premium Pulses", "category": "Groceries", "price": 15,
         "image": "https://food.fnr.sndimg.com/content/dam/images/food/fullset/2016/2/15/0/HE_dried-legumes-istock-2_s4x3.jpg.rend.hgtvcom.1280.1280.85.suffix/1455572939649.webp"},

        {"name": "Milk & Bread Combo", "category": "Groceries", "price": 8,
         "image": "https://thumbs.dreamstime.com/b/rural-still-life-bread-milk-eggs-board-55729613.jpg"},

        # ---------------- Electronics ----------------
        {"name": "iPhone 15", "category": "Electronics", "price": 999,
         "image": "https://darlingretail.com/cdn/shop/files/iPhone_15_Blue_Pure_Back_iPhone_15_Blue_Pure_Front_2up_Screen__WWEN_600x.jpg?v=1695103868"},

        {"name": "Wireless Earphones", "category": "Electronics", "price": 79,
         "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRYFQNmvWCZGW8HJxuuTmQ4ZpaI1_t9fzrkOg&s"},

        {"name": "Hair Straightener", "category": "Electronics", "price": 45,
         "image": "https://image.cdn.shpy.in/365412/ikonic-pro-titanium-shine-hair-straightener-black-1738425778893_SKU-11136_0.jpg?width=600&format=webp"},

        # ---------------- Fashion ----------------
        {"name": "Casual Outfit", "category": "Fashion", "price": 59,
         "image": "https://img.freepik.com/premium-photo/cool-fashion-casual-men-outfit-wooden-table_93675-18917.jpg"},

        {"name": "Running Shoes", "category": "Fashion", "price": 120,
         "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQQJP7_k1r1jtYZNcUe9IYFHla6SjyMTT-TuQ&s"},

        {"name": "Classic Watch", "category": "Fashion", "price": 199,
         "image": "https://www.fossil.com/on/demandware.static/-/Library-Sites-FossilSharedLibrary/default/dw294e3664/2025/HO25/set_10272025_global_holiday_lp/watches/Watches_LP_carousel_Style_Mens_classic.jpg"},

        # ---------------- Sports ----------------
        {"name": "Dumbbells", "category": "Sports", "price": 50,
         "image": "data:image/jpeg;base64,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"},

        {"name": "Protein Powder", "category": "Sports", "price": 35,
         "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTNKUcM7ZyvdjfRXh1T0p1CkeiG4Tj1AA_sjw&s"},

        {"name": "Cricket Bat & Ball", "category": "Sports", "price": 75,
         "image": "https://media.istockphoto.com/id/177491473/photo/cricket-bat-and-ball.jpg?s=612x612&w=0&k=20&c=QqX5lbsHBUi7VZc4yLyeW52LVttKtZQ5e-LXEG-uKMI="},
    ]

    # Search
    if query:
        products = [p for p in products if query.lower() in p["name"].lower()]

    return render_template("shop.html", products=products, search=query)

# =============================
# BUY PRODUCT
# =============================

@app.route("/buy/<product>/<price>")
def buy(product, price):

    if "user" not in session:
        return redirect("/")

    print("BUY ROUTE HIT")

    price = float(price)   # 🔥 ADD THIS LINE

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO orders (user_email,product,price,date) VALUES (?,?,?,?)",
        (session["user"], product, price, str(datetime.now()))
    )

    conn.commit()
    conn.close()

    return redirect("/shop")


# =============================
# DASHBOARD
# =============================

@app.route("/dashboard")
def dashboard():

    # =============================
    # DATABASE METRICS
    # =============================
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    today = datetime.now().date()

    c.execute("""
    SELECT SUM(price) 
    FROM orders 
    WHERE DATE(date) = ?
    """, (today,))
    today_revenue = c.fetchone()[0] or 0

    c.execute("""
    SELECT COUNT(*) 
    FROM orders 
    WHERE DATE(date) = ?
    """, (today,))
    today_orders = c.fetchone()[0]

    c.execute("""
    SELECT SUM(price) 
    FROM orders 
    WHERE date >= date('now','-30 day')
    """)
    revenue_30 = c.fetchone()[0] or 0

    c.execute("""
    SELECT COUNT(*) 
    FROM orders 
    WHERE date >= date('now','-30 day')
    """)
    orders_30 = c.fetchone()[0]

    conn.close()

    # =============================
    # LOAD LIVE ORDERS FROM DATABASE
    # =============================
    conn = sqlite3.connect("database.db")
    orders_df = pd.read_sql_query("SELECT * FROM orders", conn)
    conn.close()

    live_df = pd.DataFrame()
    if not orders_df.empty:
        orders_df["Date"] = pd.to_datetime(orders_df["date"])
        orders_df["Units Sold"] = 1
        orders_df["Price"] = orders_df["price"].astype(float)
        orders_df["Category"] = orders_df.get("product", "Unknown")
        live_df = orders_df[["Date", "Units Sold", "Price", "Category"]].copy()

    # =============================
    # DATAFRAME FROM MODEL + LIVE ORDERS MERGED
    # =============================
    df = ai_system.df.copy()
    df["Price"] = df["Price"].fillna(0)
    df["Units Sold"] = df["Units Sold"].fillna(0)
    df["Date"] = pd.to_datetime(df["Date"])

    if not live_df.empty:
        df = pd.concat([df, live_df], ignore_index=True)

    df["Date"] = pd.to_datetime(df["Date"])
    df["Revenue"] = df["Price"] * df["Units Sold"]
    df["Profit"] = df["Revenue"] * 0.2

    # =============================
    # AI PREDICTIONS (blended: dataset + live orders)
    # =============================
    if not live_df.empty:
        ai_system.update_from_database()
        ai_system.train_sales_model()

    prediction = int(round(ai_system.forecast_next_hour()))
    forecast = ai_system.prophet_forecast(30)
    forecast_30_day = int(round(forecast["yhat"].sum()))

    predicted_profit = ai_system.predict_profit(prediction)
    roi = ai_system.roi(50000, 30000)
    inventory_status = ai_system.inventory_alert()

    # =============================
    # MAX REVENUE POTENTIAL FOR THE YEAR
    # =============================
    daily_rev = df.groupby(df["Date"].dt.date)["Revenue"].sum()
    best_day_revenue = float(daily_rev.max()) if not daily_rev.empty else 0.0
    max_revenue = round(best_day_revenue * 365, 2)

    # =============================
    # CATEGORY PRICE RANGE — 5 main categories only
    # =============================
    MAIN_CATEGORIES = {
        "Toys":        "Toys",
        "Furniture":   "Furniture",
        "Groceries":   "Groceries",
        "Clothing":    "Clothing",
        "Fashion":     "Clothing",   # map Fashion → Clothing key
        "Electronics": "Electronics"
    }
    category_price_ranges = {}
    for raw_cat in df["Category"].dropna().unique():
        mapped = MAIN_CATEGORIES.get(str(raw_cat))
        if not mapped:
            continue
        cat_df = df[df["Category"] == raw_cat]
        min_price = round(float(cat_df["Price"].quantile(0.25)), 2)
        max_price = round(float(cat_df["Price"].quantile(0.75)), 2)
        # Don't overwrite if already set (e.g. Fashion already mapped to Clothing)
        if mapped not in category_price_ranges:
            category_price_ranges[mapped] = f"${min_price} - ${max_price}"

    # =============================
    # REVENUE TREND — full history up to today
    # =============================
    trend = df.groupby(df["Date"].dt.date)["Revenue"].sum().sort_index()
    trend_dates = [str(i) for i in trend.index]
    trend_values = [round(float(v), 2) for v in trend.values.tolist()]

    # =============================
    # SALES FORECAST GRAPH — Actual vs Predicted
    # =============================
    # Prophet output contains both historical fitted values (past) and future predictions
    # We split them: past dates → actual sales, future dates → predicted only

    # Daily actual sales from the dataset
    actual_daily = df.groupby(df["Date"].dt.date)["Units Sold"].sum().sort_index()
    actual_dates_set = set(str(d) for d in actual_daily.index)

    forecast_dates = forecast["ds"].astype(str).tolist()
    forecast_values = [int(round(float(v))) for v in forecast["yhat"].tolist()]

    # Actual line: real values where we have data, None for future dates
    actual_values = []
    for d in forecast_dates:
        day = pd.to_datetime(d).date()
        if str(day) in actual_dates_set:
            actual_values.append(int(actual_daily[day]))
        else:
            actual_values.append(None)  # null in JS = gap in line

    # =============================
    # CATEGORY SALES
    # =============================
    category_data = df.groupby("Category")["Units Sold"].sum()
    categories = [str(c) for c in category_data.index.tolist()]
    category_sales = [int(v) for v in category_data.values.tolist()]

    # =============================
    # PROFIT TREND — up to today
    # =============================
    profit_series = df.groupby(df["Date"].dt.date)["Profit"].sum().sort_index()
    profit_dates = [str(i) for i in profit_series.index]
    profits = [round(float(v), 2) for v in profit_series.values.tolist()]

    # =============================
    # TOP PRODUCTS
    # =============================
    if "product" in df.columns:
        top_products_data = df.groupby("product")["Units Sold"].sum() \
            .sort_values(ascending=False).head(5)
    elif "Product ID" in df.columns:
        top_products_data = df.groupby("Product ID")["Units Sold"].sum() \
            .sort_values(ascending=False).head(5)
    else:
        top_products_data = pd.Series(dtype=float)

    top_products = [str(p) for p in top_products_data.index.tolist()]
    product_sales = [int(v) for v in top_products_data.values.tolist()]

    # =============================
    # SHAP FEATURE IMPORTANCE
    # =============================
    features = ['Inventory', 'Units Ordered', 'Price', 'Discount', 'Demand', 'Seasonality', 'Competition']
    importance = [85.0, 78.0, 65.0, 52.0, 48.0, 35.0, 28.0]

    try:
        X, _ = ai_system.prepare_sales_data()
        shap_values = ai_system.explainer.shap_values(X.iloc[:100])
        all_importance = abs(shap_values).mean(axis=0)
        filtered_importance = []
        for feature in features:
            if feature in X.columns:
                idx = list(X.columns).index(feature)
                filtered_importance.append(float(all_importance[idx]))
            else:
                filtered_importance.append(30.0)
        importance = filtered_importance
    except Exception as e:
        print(f"SHAP safe fallback: {e}")

    # =============================
    # RENDER DASHBOARD
    # =============================
    return render_template(
        "dashboard.html",

        today_revenue=round(float(today_revenue), 2),
        today_orders=int(today_orders),
        profit=round(float(predicted_profit), 2),
        revenue_30=round(float(revenue_30), 2),
        orders_30=int(orders_30),
        roi=round(float(roi), 2),

        prediction=prediction,
        category_price_ranges=category_price_ranges,
        forecast_30_day=forecast_30_day,
        inventory_status=inventory_status,
        max_revenue=max_revenue,

        trend_dates=trend_dates,
        trend_values=trend_values,
        dates=trend_dates,
        revenues=trend_values,

        forecast_dates=forecast_dates,
        forecast_values=forecast_values,
        actual_values=actual_values,

        categories=categories,
        category_sales=category_sales,

        profit_dates=profit_dates,
        profits=profits,

        top_products=top_products,
        product_sales=product_sales,

        features=features,
        importance=importance
    )
  
# =============================
# LOGOUT
# =============================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# =============================
# LIVE STATS API (for auto-refresh)
# =============================

@app.route("/api/live-stats")
def live_stats():
    if "user" not in session or session["user"] != ADMIN_EMAIL:
        return {"error": "unauthorized"}, 403

    from flask import jsonify
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    today = datetime.now().date()

    c.execute("SELECT SUM(price) FROM orders WHERE DATE(date) = ?", (today,))
    today_revenue = round(c.fetchone()[0] or 0, 2)

    c.execute("SELECT COUNT(*) FROM orders WHERE DATE(date) = ?", (today,))
    today_orders = c.fetchone()[0]

    c.execute("SELECT SUM(price) FROM orders WHERE date >= date('now','-30 day')")
    revenue_30 = round(c.fetchone()[0] or 0, 2)

    c.execute("SELECT COUNT(*) FROM orders WHERE date >= date('now','-30 day')")
    orders_30 = c.fetchone()[0]

    # Today's revenue by hour (for live chart)
    c.execute("""
        SELECT strftime('%H:00', date) as hour, SUM(price)
        FROM orders WHERE DATE(date) = ?
        GROUP BY hour ORDER BY hour
    """, (today,))
    hourly = c.fetchall()
    hourly_labels = [r[0] for r in hourly]
    hourly_values = [round(r[1], 2) for r in hourly]

    conn.close()

    prediction = int(round(ai_system.forecast_next_hour())) if ai_system else 0

    return jsonify({
        "today_revenue": today_revenue,
        "today_orders": today_orders,
        "revenue_30": revenue_30,
        "orders_30": orders_30,
        "prediction": prediction,
        "hourly_labels": hourly_labels,
        "hourly_values": hourly_values
    })


# =============================
# ORDER HISTORY (customer view)
# =============================

@app.route("/orders")
def my_orders():
    if "user" not in session:
        return redirect("/")
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT product, price, date FROM orders WHERE user_email=? ORDER BY date DESC",
              (session["user"],))
    rows = c.fetchall()
    conn.close()
    orders = [{"product": r[0], "price": r[1], "date": r[2]} for r in rows]
    return render_template("orders.html", orders=orders)


# =============================
# RUN SERVER
# =============================

if __name__ == "__main__":

    print("Starting Flask Server...")

    app.run(host="127.0.0.1", port=5000, debug=True)