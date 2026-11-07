FROM python:3.12-alpine

WORKDIR /app

COPY average.py .
COPY test_average.py .

CMD ["python", "-B", "-m", "unittest", "-v", "test_average"]
