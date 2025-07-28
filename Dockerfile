# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY crosswalk.py .

# Create directory for uploaded files
RUN mkdir -p /app/uploads

# Expose Streamlit port
EXPOSE 8501

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_PORT=8502
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8502/_stcore/health

# Run the Streamlit application
CMD ["streamlit", "run", "app.py", "--server.port=8502", "--server.address=0.0.0.0"]