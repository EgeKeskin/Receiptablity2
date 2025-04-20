FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# system deps
RUN apt-get update \
 && apt-get install -y tesseract-ocr libtesseract-dev libleptonica-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY . .

# collect your static into STATIC_ROOT (staticfiles/)
RUN python manage.py collectstatic --noinput

# now STATIC_ROOT/staticfiles is baked into the image
CMD ["gunicorn", "receiptablity.wsgi:application", "--bind", "0.0.0.0:$PORT", "--workers", "2"]
