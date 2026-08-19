FROM python:3.12-slim AS base

WORKDIR /app
ENV PYTHONPATH=/app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      gcc libpq-dev curl \
      libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 \
      fonts-dejavu-core fonts-liberation && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=180 -r requirements.txt

COPY . .

RUN mkdir -p /app/media/audio

EXPOSE 8000

CMD ["sh", "entrypoint.sh"]
