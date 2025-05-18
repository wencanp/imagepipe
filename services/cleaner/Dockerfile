FROM python:3.9-slim

WORKDIR /app

COPY ../../requirements.txt .
COPY . .
COPY ../../utils/ ./utils/

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

CMD [ "celery", "-A", "cleaner_worker", "worker", "-B", "-n", "cleaner@%h", "-Q", "cleaner_queue", "--loglevel=info", "--pool=solo" ]