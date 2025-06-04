FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Change to the Django project directory
WORKDIR /app/mystorelink

# Set Django settings module
ENV DJANGO_SETTINGS_MODULE=mystorelink.settings

# Set temporary environment variables for collectstatic
ENV DJANGO_SECRET_KEY=temp-secret-key-for-build
ENV DEBUG=False
ENV DATABASE_URL=sqlite:///temp.db

# Collect static files
RUN python manage.py collectstatic --noinput

# Create media directory
RUN mkdir -p /app/mystorelink/media

# Expose port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "mystorelink.wsgi:application"]