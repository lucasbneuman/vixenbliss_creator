FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY requirements.txt /tmp/s1-image-requirements.txt
RUN pip install --no-cache-dir -r /tmp/s1-image-requirements.txt

COPY runtime/app.py /app/app.py
COPY src /app/src

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
