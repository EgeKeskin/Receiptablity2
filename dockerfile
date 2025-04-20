# Use official Python image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /receiptablity

# System deps
RUN apt-get update \
 && apt-get install -y tesseract-ocr libtesseract-dev libleptonica-dev \
 && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Code
COPY . .

# Make sure STATIC_ROOT exists & collect
RUN mkdir -p staticfiles
RUN python manage.py collectstatic --noinput

# Expose & run
EXPOSE 10000
CMD ["gunicorn", "receiptablity.wsgi:application", "--bind", "0.0.0.0:$PORT", "--workers", "2"]
