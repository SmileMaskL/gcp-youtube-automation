# Dockerfile

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ /app/

# Expose port
ENV PORT 8080

# Run Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]
