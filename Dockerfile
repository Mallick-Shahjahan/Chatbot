FROM python:3.11-slim

# Install system packages needed for PyAV, FFmpeg, and soundfile
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

COPY requirements.txt .

# Upgrade pip/wheel and install Cython before building PyAV
RUN pip install --upgrade pip setuptools wheel
RUN pip install "Cython==0.29.36"

# Install Python dependencies (PyAV will use the preinstalled Cython)
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "chatbot.py", "--server.port=8501", "--server.headless=true"]
