FROM python:3.9-slim

WORKDIR /app

COPY ../../requirements.txt .
COPY . .
COPY ../../utils/ ./utils/

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

CMD [ "celery", "-A", "services.cleaner.cleaner_worker", "worker", "-B", "-n", "cleaner@%%h", "--without-gossip", "--without-mingle", "-Q", "cleaner_queue", "--loglevel=info", "--pool=solo" ]