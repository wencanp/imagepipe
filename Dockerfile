# Use Python base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . . 

# Install dependencies
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y tesseract-ocr

# Command to run Celery Worker
CMD ["python", "gateway/app.py"]