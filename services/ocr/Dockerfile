FROM python:3.9-slim

WORKDIR /app

COPY ../../requirements.txt .
COPY . .

RUN apt-get update && apt-get install -y tesseract-ocr && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "celery", "-A", "services.ocr.ocr_worker", "worker", "-n", "ocr@%%h", "--without-gossip", "--without-mingle", "-Q", "ocr_queue", "--loglevel=info", "--pool=solo" ]