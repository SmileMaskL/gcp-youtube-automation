# Use official Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg

# Set working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code into /app
COPY . /app/

# Set environment variable for port
ENV PORT=8080

# Command to run the app with Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]
