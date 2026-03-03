FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc

# Copy requirements first
COPY backend/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend ./backend

# Create DB directory
RUN mkdir -p /app/backend

EXPOSE 8000

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "backend.frontend_api.app:app", "--bind", "0.0.0.0:8000", "--workers", "4"]
