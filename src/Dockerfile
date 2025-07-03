# Use official Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project into /app
COPY . /app/

# Ensure default image exists (이미 루트에 있으므로 COPY 생략 가능. /app/default_image.jpg 경로 유지)
# If your image is in another folder, adjust accordingly.

# Set environment variable for port
ENV PORT=8080

# Command to run the app with Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]
