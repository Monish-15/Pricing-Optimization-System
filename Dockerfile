FROM python:3.10-slim

WORKDIR /app

# Install system dependencies required for data-science packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy all project files into the container
COPY . .

# Expose the API port
EXPOSE 8000

# Start the FastAPI application
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
