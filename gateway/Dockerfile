FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
COPY . .

RUN apt-get update && apt-get install -y tesseract-ocr && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

# Shell script to start the Flask app, avoid Railway's Flask CLI inference mechanism
RUN chmod +x start.sh
CMD ["./start.sh"]