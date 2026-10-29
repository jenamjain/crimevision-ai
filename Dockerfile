# CrimeVision AI - Production Container
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CRIMEVISION_HOST=0.0.0.0 \
    CRIMEVISION_PORT=8000

# Install essential system dependencies for OpenCV, multimedia, and PDF handling
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir python-multipart fpdf2 reportlab

# Copy application source code
COPY . .

# Create required storage directories
RUN mkdir -p uploads/images uploads/audio uploads/video reports

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# Launch application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
