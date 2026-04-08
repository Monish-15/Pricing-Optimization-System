import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import sqlite3
import mlflow
import os

from backend.db import DB_PATH

MODEL_PATH = os.path.join(os.path.dirname(__file__), "pricing_model.pkl")

def generate_initial_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM demand_data")
    if cursor.fetchone()[0] == 0:
        np.random.seed(42)
        n_samples = 500
        demand = np.random.randint(50, 300, n_samples)
        supply = np.random.randint(20, 150, n_samples)
        times = np.random.choice(['morning', 'afternoon', 'evening', 'night'], n_samples)
        
        # Base price logic mimicking real world (higher demand -> higher price, higher supply -> lower price)
        price = 50 + (demand * 0.4) - (supply * 0.2)
        
        # Adjust price based on time
        time_multipliers = {'morning': 1.1, 'afternoon': 1.0, 'evening': 1.3, 'night': 0.8}
        price = price * np.array([time_multipliers[t] for t in times])
        
        price += np.random.normal(0, 5, n_samples)
        price = np.clip(price, 10, 500)
        price = np.round(price, 2)
        
        # Sales elasticity
        actual_sales = np.maximum(0, demand - (price * 0.3) + np.random.normal(0, 5, n_samples)).astype(int)
        revenue = price * actual_sales

        df = pd.DataFrame({
            'demand': demand,
            'supply': supply,
            'time_of_day': times,
            'price': price,
            'actual_sales': actual_sales,
            'revenue': revenue
        })
        df.to_sql('demand_data', conn, if_exists='append', index=False)
    conn.close()

def train_model(is_retrain=False):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM demand_data", conn)
    conn.close()

    if df.empty:
        return

    # One-hot encode time_of_day
    df_encoded = pd.get_dummies(df, columns=['time_of_day'])
    
    # Expected columns to ensure consistency
    expected_cols = ['demand', 'supply', 'price', 'time_of_day_morning', 'time_of_day_afternoon', 'time_of_day_evening', 'time_of_day_night']
    for col in expected_cols:
        if col not in df_encoded.columns:
            df_encoded[col] = False
            
    X = df_encoded[expected_cols]
    y = df_encoded['actual_sales']

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    preds = model.predict(X)
    rmse = np.sqrt(mean_squared_error(y, preds))
    rscore = r2_score(y, preds)

    joblib.dump(model, MODEL_PATH)

    # Log to MLflow
    mlflow_db_path = os.path.join(os.path.dirname(__file__), "mlflow.db")
    mlflow.set_tracking_uri(f"sqlite:///{mlflow_db_path}")
    try:
        mlflow.set_experiment("pricing_optimization")
        with mlflow.start_run():
            mlflow.log_metric("rmse", rmse)
            mlflow.log_metric("r2", rscore)
            mlflow.log_param("retrain", is_retrain)
            mlflow.log_param("data_size", len(df))
    except Exception as e:
        print(f"MLflow error: {e}")

    # Log to DB
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    version = "v1." + str(len(df)) if is_retrain else "v1.0"
    c.execute("INSERT INTO model_metrics (version, rmse, r2) VALUES (?, ?, ?)", 
              (version, float(rmse), float(rscore)))
    conn.commit()
    conn.close()

def get_optimal_price(demand, supply, time_of_day):
    if not os.path.exists(MODEL_PATH):
        generate_initial_data()
        train_model()
    
    model = joblib.load(MODEL_PATH)
    
    candidate_prices = np.arange(50, 500, 10)
    best_revenue = 0
    optimal_price = 50
    
    for test_price in candidate_prices:
        input_data = {
            'demand': [demand],
            'supply': [supply],
            'price': [test_price],
            'time_of_day_morning': [time_of_day == 'morning'],
            'time_of_day_afternoon': [time_of_day == 'afternoon'],
            'time_of_day_evening': [time_of_day == 'evening'],
            'time_of_day_night': [time_of_day == 'night']
        }
        
        expected_cols = ['demand', 'supply', 'price', 'time_of_day_morning', 'time_of_day_afternoon', 'time_of_day_evening', 'time_of_day_night']
        X = pd.DataFrame(input_data)[expected_cols]
        
        expected_sales = model.predict(X)[0]
        expected_revenue = expected_sales * test_price
        
        if expected_revenue > best_revenue:
            best_revenue = expected_revenue
            optimal_price = test_price

    return float(round(optimal_price, 2))
