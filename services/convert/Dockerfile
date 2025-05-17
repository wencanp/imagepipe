FROM python:3.9-slim

WORKDIR /app

COPY ../../requirements.txt .
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "celery", "-A", "convert_worker", "worker", "-n", "convert@%h", "-Q", "convert_queue", "--loglevel=info", "--pool=solo" ]