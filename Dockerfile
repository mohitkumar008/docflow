FROM python:3.11-slim

# Install system dependencies required for parsing certain document types
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency configs
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source (Streamlit UI + FastAPI companion)
COPY app.py .
COPY api.py .

# Expose Streamlit default port (UI) and FastAPI port (API mode)
EXPOSE 8501
EXPOSE 8000

# Run the Streamlit web application by default
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]