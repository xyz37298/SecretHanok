FROM python:3.11-slim

# 필수 패키지 설치 (pip 포함)
RUN apt-get update && apt-get install -y \
    python3-pip \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "--worker-class", "gevent", "--bind", "0.0.0.0:${PORT}", "backend:app"]
