FROM python:3.9-slim

WORKDIR /app

COPY ../../requirements.txt .
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "celery", "-A", "services.convert.convert_worker", "worker", "-n", "convert@%%h", "--without-gossip", "--without-mingle", "-Q", "convert_queue", "--loglevel=info", "--pool=solo" ]