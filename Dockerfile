FROM python:3.12-slim

WORKDIR /app

# Системные зависимости для psycopg2 и Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements и frontend-пакет отдельно для кэширования слоёв
COPY requirements.txt .
COPY diploma-frontend/dist/ diploma-frontend/dist/

RUN pip install --no-cache-dir -r requirements.txt

# Копируем backend
COPY diploma_backend/ diploma_backend/

WORKDIR /app/diploma_backend

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
