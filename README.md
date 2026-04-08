# 🚀 NexusPrice: Dynamic Pricing Optimization with MLOps

This is a complete, closed-loop MLOps system that predicts optimal prices, collects user feedback (sales/revenue), and automatically retrains itself over time. It's built for your Viva presentation to show advanced concepts like continuous learning and revenue optimization.

## 🌟 Features Highlight
- **Closed-Loop MLOps**: Unlike standard ML projects that predict once, this system captures actual sales and feeds them back into the database.
- **Continuous Learning**: The model automatically triggers a retraining cycle when new feedback is received (A/B testing simulation).
- **Revenue Optimization vs Price Prediction**: Focuses firmly on maximizing overall revenue, not just assigning a generic price.
- **Dynamic Demand Simulation**: A highly visual, state-of-the-art UI dashboard to interact with the model in real time.

## 🛠️ Tech Stack
- **Backend**: FastAPI, Uvicorn (for high-performance API serving)
- **ML Pipeline**: Scikit-Learn (Random Forest), Pandas
- **Experiment Tracking**: MLflow integration included
- **Frontend**: Vanilla JS/CSS with glassmorphism UI, Chart.js for visualization

---

## 🏃‍♂️ How to Run the Project Locally

### 1. Set Up Environment
It is highly recommended to use a virtual environment:
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 2. Install Dependencies
```powershell
pip install -r backend\requirements.txt
```

### 3. Start the Application
Run the FastAPI application. We use `uvicorn` and load the app from `backend/main.py`.
```powershell
# Make sure you run this from the root folder: D:\Pricing Optimization System
python -m uvicorn backend.main:app --reload
```

### 4. Open the Interface
Upon startup, the API will initialize an SQLite database and train an initial baseline model.
Once the server is running, simply go to your browser and open:
👉 **[http://localhost:8000/](http://localhost:8000/)**

## 💡 How to present this in your Viva

1. **Start at real-world use cases**: Talk about Uber surge pricing or airline tickets. Mention how your system dynamically balances Demand and Supply.
2. **Show the Dashboard**: Adjust the sliders. Tell the examiner: *"Here, I'm simulating market conditions. The model calculates the perfect price using a Random Forest."*
3. **Show the Feedback Loop (The "Wow" Factor)**: Once predicting a price, simulate actual sales and click **"Send Feedback & Retrain"**. Point out how the "Training Samples" count goes up and new rows appear in the logs. Explain: *"This is a closed-loop system. It deployed an endpoint, captured user response, logged the generated revenue, and will autonomously rebuild its intelligence as market conditions shift."*
4. **Conclusion**: Reinforce that it handles model drift automatically and maximizes long-term profit.
