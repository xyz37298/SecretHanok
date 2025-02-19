# Python 3.11 기반 이미지 사용
FROM python:3.11-slim

# 필수 패키지 설치 (OpenCV, WebSocket 관련)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# Gunicorn 실행 (WebSocket 지원을 위해 gevent 사용)
CMD ["gunicorn", "--worker-class", "gevent", "--bind", "0.0.0.0:10000", "backend:app", "--timeout", "180", "--log-level", "debug"]
