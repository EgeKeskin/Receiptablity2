# Use a slim Python base
FROM python:3.11-slim

# don’t write .pyc, and force stdout/err
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# system deps for pytesseract
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      tesseract-ocr \
      libtesseract-dev \
      libleptonica-dev \
 && rm -rf /var/lib/apt/lists/*

# grab and install Python deps
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# copy your code
COPY . .

# collect static (so staticfiles/ is baked in)
RUN python manage.py collectstatic --noinput

# run via shell so that $PORT expands
CMD sh -c "\
    gunicorn receiptablity.wsgi:application \
      --bind 0.0.0.0:${PORT:-8000} \
      --workers 2\
"
