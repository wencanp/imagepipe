FROM python:3.9-slim

WORKDIR /app

COPY ../../requirements.txt .
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "celery", "-A", "services.filter.filter_worker", "worker", "-n", "filter@%%h", "--without-gossip", "--without-mingle", "-Q", "filter_queue", "--loglevel=info", "--pool=solo" ]