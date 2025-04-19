# Use official Python image
FROM python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_STATIC_ROOT=/static

# Set working directory
WORKDIR /receiptablity

# Install Tesseract and dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install -r requirements.txt

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port for Render
EXPOSE 8000

# Start app
CMD ["gunicorn", "receiptablity.wsgi:application", "--bind", "0.0.0.0:$PORT"]
