FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# System dependencies for OpenCV with extra resilience
RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirement files from root context
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy necessary source code and model directory
# We MUST keep the folder structure so "from training.colorization_model import..." works
COPY training/ ./training/
COPY model/ ./model/
COPY webapp/backend/ ./webapp/backend/

# Expose the API port
EXPOSE 8000

# Start FastAPI using the PORT environment variable (Render compatibility)
CMD sh -c "uvicorn webapp.backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"
