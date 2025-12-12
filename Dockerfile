FROM python:3.11-slim

# Install system packages required for PyAV, FFmpeg and soundfile
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      pkg-config \
      ffmpeg \
      libsndfile1 \
      libavformat-dev \
      libavcodec-dev \
      libavdevice-dev \
      libavfilter-dev \
      libavutil-dev \
      libswscale-dev \
      libswresample-dev \
      build-essential \
      git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Copy app code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Start Streamlit
CMD ["streamlit", "run", "chatbot.py", "--server.port=8501", "--server.headless=true"]
