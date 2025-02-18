FROM python:3.11-slim

# 필수 라이브러리 설치
RUN apt-get update && apt-get install -y libgl1-mesa-glx && apt-get clean

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install -r requirements.txt

# 소스 복사
COPY . .

# Gunicorn 실행
CMD ["gunicorn", "--worker-class", "gevent", "--bind", "0.0.0.0:10000", "backend:app", "--timeout", "180", "--log-level", "debug"]
