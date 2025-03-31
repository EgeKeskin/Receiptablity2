# Use official Python image
FROM python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /receiptablity

# Copy project files
COPY . /receiptablity/

# Create the static directory
RUN mkdir -p /static

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install -r requirements.txt

# Expose port
EXPOSE 8000

# Start Django app with Gunicorn and collect static files
CMD ["sh", "-c", "python manage.py collectstatic --noinput && gunicorn --bind 0.0.0.0:8000 receiptablity.wsgi:application"]
