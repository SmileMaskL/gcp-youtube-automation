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

# Copy all source code into /app
COPY . /app/

# Ensure default image exists (필요시 default_image.jpg를 src 혹은 최상위에 위치)
COPY default_image.jpg /app/default_image.jpg

# Set environment variable for port
ENV PORT=8080

# Command to run the app with Gunicorn
CMD ["gunicorn", "src.app:app", "--bind", "0.0.0.0:8080"]
