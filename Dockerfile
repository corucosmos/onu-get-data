FROM python:3.11-slim

# Instalar Chromium y su Driver
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY onu_get_data.py .

# Instalamos selenium
RUN pip install --no-cache-dir \
    selenium \
    urllib3==1.26.15 \
    pytz\
    requests

RUN mkdir -p /app/data

CMD ["python", "-u","onu_get_data.py"]