from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from backend import mlops_pipeline
from backend import db
import sqlite3
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI(title="Dynamic Pricing Optimization API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')

@app.on_event("startup")
def startup_event():
    db.init_db()
    mlops_pipeline.generate_initial_data()
    mlops_pipeline.train_model()
    # Check if frontend exists
    if not os.path.exists(frontend_path):
        os.makedirs(frontend_path)

if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

class PredictionRequest(BaseModel):
    demand: int
    supply: int
    time: str

class FeedbackRequest(BaseModel):
    demand: int
    supply: int
    time: str
    recommended_price: float
    actual_sales: int

@app.post("/predict-price")
def predict_price(req: PredictionRequest):
    price = mlops_pipeline.get_optimal_price(req.demand, req.supply, req.time)
    
    return {"recommended_price": price}

@app.post("/feedback")
def submit_feedback(req: FeedbackRequest, background_tasks: BackgroundTasks):
    revenue = req.recommended_price * req.actual_sales
    conn = sqlite3.connect(db.DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO demand_data (demand, supply, time_of_day, price, actual_sales, revenue)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (req.demand, req.supply, req.time, req.recommended_price, req.actual_sales, revenue))
    conn.commit()
    
    # Check for retraining
    c.execute("SELECT COUNT(*) FROM demand_data")
    count = c.fetchone()[0]
    conn.close()
    
    if count % 10 == 0: # Retrain every 10 feedbacks for demonstration purposes
        background_tasks.add_task(mlops_pipeline.train_model, is_retrain=True)

    return {"status": "success", "message": f"Feedback received. Revenue: ₹{revenue:.2f}. Model learning continuously."}

@app.get("/dashboard-data")
def get_dashboard_data():
    conn = sqlite3.connect(db.DB_PATH)
    
    df_history = pd.read_sql("SELECT * FROM demand_data ORDER BY id ASC", conn)
    
    if df_history.empty:
        return {}
        
    revenue_trend = df_history['revenue'].tolist()
    price_trend = df_history['price'].tolist()
    demand_trend = df_history['demand'].tolist()
    
    df_metrics = pd.read_sql("SELECT * FROM model_metrics ORDER BY id DESC", conn)
    rmse = df_metrics['rmse'].iloc[0] if not df_metrics.empty else 0
    version = df_metrics['version'].iloc[0] if not df_metrics.empty else "v1.0"
    
    total_rev = sum(revenue_trend)
    avg_price = sum(price_trend)/len(price_trend)
    
    conn.close()
    
    return {
        "metrics": {
            "total_revenue": round(total_rev, 2),
            "avg_price": round(avg_price, 2),
            "model_version": version,
            "rmse": round(rmse, 2),
            "data_points": len(df_history)
        },
        "trends": {
            "revenue": revenue_trend[-30:],
            "price": price_trend[-30:],
            "demand": demand_trend[-30:]
        },
        "recent_activity": df_history.tail(5).to_dict(orient='records')
    }

@app.get("/")
def serve_dashboard():
    return FileResponse(os.path.join(frontend_path, "index.html"))
