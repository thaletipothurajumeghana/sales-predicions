# =========================================================
# RETAIL AI SYSTEM (ALIGNED TO YOUR DATASET)
# =========================================================

import os
import pandas as pd
import numpy as np
from datetime import timedelta

# ML
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Forecasting
from prophet import Prophet

# Explainability
import shap
import matplotlib.pyplot as plt


class RetailAI:
    # =====================================================
    # INITIALIZATION
    # =====================================================
    def __init__(self, dataset_path):
        self.df = pd.read_csv(dataset_path)
        self.df["Date"] = pd.to_datetime(self.df["Date"])
        self.df = self.df.sort_values("Date")
        self.sales_model = None
        self.inventory_model = None
        self.feature_columns = None
        self.explainer = None

    # =====================================================
    # NEW: DATABASE UPDATE (ADD THIS)
    # =====================================================
    def update_from_database(self):
        """Load real orders from database.db and update training data"""
        import sqlite3
        db_path = os.getenv("DATABASE_PATH", "database.db")
        conn = sqlite3.connect(db_path)
    
        orders_df = pd.read_sql_query("""
            SELECT date as Date, price as Price, 1 as 'Units Sold'
            FROM orders
    """, conn)
        conn.close()
    
        if not orders_df.empty:
            orders_df['Date'] = pd.to_datetime(orders_df['Date'])
        
        # Match EXACTLY original CSV columns
            orders_df = orders_df[['Date', 'Units Sold', 'Price']]
        
        # Append to existing data
            self.df = pd.concat([self.df, orders_df], ignore_index=True)
            self.df = self.df.sort_values("Date").reset_index(drop=True)
        
            print(f"Added {len(orders_df)} real orders to dataset. Total: {len(self.df)} rows")

    # =====================================================
    # SALES FORECAST MODEL (XGBOOST)
    # =====================================================

    def prepare_sales_data(self):

        df = self.df.copy()

        # Time features
        df["Hour"] = df["Date"].dt.hour
        df["Day"] = df["Date"].dt.day
        df["Month"] = df["Date"].dt.month
        df["Weekday"] = df["Date"].dt.weekday

        # Lag features
        df["lag_1"] = df["Units Sold"].shift(1)
        df["lag_24"] = df["Units Sold"].shift(24)
        df["rolling_24"] = df["Units Sold"].rolling(24).mean()

        df = df.dropna()

        # Encode categorical columns
        categorical_cols = [
            "Store ID", "Product ID", "Category",
            "Region", "Weather Condition",
            "Promotion", "Seasonality",
            "Epidemic"
        ]

        df = pd.get_dummies(df, columns=categorical_cols, drop_first=True)

        X = df.drop(["Units Sold", "Date"], axis=1)
        y = df["Units Sold"]

        self.feature_columns = X.columns

        return X, y

    def train_sales_model(self):

        X, y = self.prepare_sales_data()

        split = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split], X.iloc[split:]
        y_train, y_test = y.iloc[:split], y.iloc[split:]

        self.sales_model = XGBRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=6
        )

        self.sales_model.fit(X_train, y_train)

        y_pred = self.sales_model.predict(X_test)

        print("\nSALES MODEL PERFORMANCE")
        print("MAE:", round(mean_absolute_error(y_test, y_pred), 2))
        print("RMSE:", round(np.sqrt(mean_squared_error(y_test, y_pred)), 2))
        print("R2:", round(r2_score(y_test, y_pred), 4))

        self.explainer = shap.TreeExplainer(self.sales_model)

    # =====================================================
    # FORECAST FUNCTION
    # =====================================================

    def forecast_next_hour(self):
        
        last_row = self.df.iloc[-1:].copy()

        # Time features
        last_row["Hour"] = last_row["Date"].dt.hour
        last_row["Day"] = last_row["Date"].dt.day
        last_row["Month"] = last_row["Date"].dt.month
        last_row["Weekday"] = last_row["Date"].dt.weekday

        # Lag features
        last_row["lag_1"] = self.df["Units Sold"].iloc[-1]
        last_row["lag_24"] = self.df["Units Sold"].iloc[-24]
        last_row["rolling_24"] = self.df["Units Sold"].iloc[-24:].mean()

    # Remove columns that are not model features
        drop_cols = ["Date", "Product"]
        for col in drop_cols:
            if col in last_row.columns:
                last_row = last_row.drop(columns=[col])

    # One-hot encoding
        last_row = pd.get_dummies(last_row)

    # Match training features
        last_row = last_row.reindex(columns=self.feature_columns, fill_value=0)

        prediction = self.sales_model.predict(last_row)[0]

        return prediction

    # =====================================================
    # INVENTORY RISK MODEL (ML)
    # =====================================================

    def train_inventory_risk_model(self):

        df = self.df.copy()

        df["Risk_Label"] = np.where(
            df["Inventory"] < df["Units Sold"], 1, 0
        )

        X = df[["Inventory", "Units Sold", "Units Ordered", "Price", "Discount"]]
        y = df["Risk_Label"]

        model = RandomForestClassifier()
        model.fit(X, y)

        self.inventory_model = model

        print("Inventory Risk Model Trained")

# =====================================================
# INVENTORY ALERT FUNCTION
# =====================================================

    def inventory_alert(self):
        
        df = self.df.copy()
        
        # Use latest row
        # 
        last_row = df.iloc[-1]
        
        X = [[
        last_row["Inventory"],
        last_row["Units Sold"],
        last_row["Units Ordered"],
        last_row["Price"],
        last_row["Discount"]
        ]]
        
        prediction = self.inventory_model.predict(X)[0]
        
        if prediction == 1:
            return "⚠ Low Stock Risk"
        else:
            return "✅ Inventory Healthy"

    # =====================================================
    # PRICE OPTIMIZATION
    # =====================================================

    # =====================================================
    # DYNAMIC PRICING BY CATEGORY
    # =====================================================

    def dynamic_price_ranges(self):

        df = self.df.copy()

        category_ranges = {}

        for category in df["Category"].dropna().unique():

            cat_df = df[df["Category"] == category]

            # skip empty category
            if len(cat_df) < 5:
                continue

            X = cat_df[["Price"]]
            y = cat_df["Units Sold"]

            model = GradientBoostingRegressor()
            model.fit(X, y)

            price_range = np.linspace(cat_df["Price"].min(),
                                      cat_df["Price"].max(), 50)

            best_price = 0
            max_revenue = 0

            for price in price_range:

                demand = model.predict([[price]])[0]
                revenue = demand * price

                if revenue > max_revenue:

                    max_revenue = revenue
                    best_price = price

            low = round(best_price * 0.9, 2)
            high = round(best_price * 1.1, 2)

            category_ranges[category] = f"${low} - ${high}"

        return category_ranges
    # =====================================================
# PROFIT PREDICTION
# =====================================================

    def predict_profit(self, predicted_units):
        avg_price = self.df["Price"].mean()
        # assume cost is 60% of price
        avg_cost = avg_price * 0.6
        
        revenue = predicted_units * avg_price
        
        cost = predicted_units * avg_cost
        
        profit = revenue - cost
        
        return profit

    # =====================================================
    # PROPHET 30-DAY FORECAST
    # =====================================================

    def prophet_forecast(self, periods=30):
        prophet_df = self.df[["Date", "Units Sold"]] \
            .rename(columns={"Date": "ds", "Units Sold": "y"})
        model = Prophet()
        model.fit(prophet_df)
        
        future = model.make_future_dataframe(periods=periods, freq="h")
        
        forecast = model.predict(future)
        
        return forecast[["ds", "yhat"]].tail(periods)
    # =====================================================
    # EOQ
    # =====================================================

    def eoq(self, annual_demand, ordering_cost, holding_cost):
        return np.sqrt((2 * annual_demand * ordering_cost) / holding_cost)

    # =====================================================
    # ROI
    # =====================================================

    def roi(self, revenue, investment):
        return ((revenue - investment) / investment) * 100

    # =====================================================
    # SHAP EXPLAINABILITY
    # =====================================================

    def get_shap_analysis(self):
        """SHAP analysis - ONLY desired features"""
        # Prepare features from current dataset
        X, _ = self.prepare_sales_data()

        # Select ONLY your 7 desired features
        desired_features = ['Inventory', 'Units Ordered', 'Price', 'Discount',
                            'Demand', 'Seasonality', 'Competition']

        # Filter to only available features
        available_features = [f for f in desired_features if f in X.columns]
        X_filtered = X[available_features]

        # Generate SHAP values
        shap_values = self.explainer.shap_values(X_filtered.iloc[:100])
        importance = abs(shap_values).mean(axis=0)

        return available_features, importance.tolist()



# =========================================================
# RUN SYSTEM
# =========================================================