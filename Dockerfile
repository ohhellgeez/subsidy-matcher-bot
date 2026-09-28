FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY certs/mincifry_ca.pem ./certs/mincifry_ca.pem
COPY alembic.ini .
COPY migrations/ ./migrations/
COPY database/ ./database/

# Платформа МАХ использует сертификаты Минцифры — добавляем их в CA-бандл
# certifi, чтобы requests доверял platform-api2.max.ru без доп. настроек.
RUN python -c "import certifi, pathlib; b = pathlib.Path(certifi.where()); b.write_text(b.read_text() + '\n' + pathlib.Path('/app/certs/mincifry_ca.pem').read_text())"

# Порт используется только в режиме BOT_MODE=webhook.
EXPOSE 8000

CMD ["python", "-m", "src.main"]
