# Use a lightweight Python image
FROM python:3.11-slim

# Install system dependencies required for PyAV & audio libraries
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      pkg-config \
      ffmpeg \
      libsndfile1 \
      build-essential \
      git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only requirements first (for caching layers)
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Copy the rest of your app
COPY . .

# Expose Streamlit's default port
EXPOSE 8501

# Run Streamlit app
CMD ["streamlit", "run", "chatbot.py", "--server.port=8501", "--server.headless=true"]
