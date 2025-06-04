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
ENV DJANGO_SECRET_KEY=django-insecure-nqr#xjux1+sp-e*ly06_br7_mx*13fg=-++i3!9+z30b27s10e
ENV DEBUG=False
ENV DATABASE_URL=sqlite:///temp.db
ENV SUPABASE_URL=https://txoozovxifmkyjubfuhg.supabase.co
ENV SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR4b296b3Z4aWZta3lqdWJmdWhnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkwMjQ0OTcsImV4cCI6MjA2NDYwMDQ5N30._6qFicR1sMM25EA90xkkW7KPLyasHFp21ys6WrDV9Ko
ENV SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR4b296b3Z4aWZta3lqdWJmdWhnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTAyNDQ5NywiZXhwIjoyMDY0NjAwNDk3fQ.UlCDCbSnc9dqR8OGTY8LJjJwfvphpU5BOkm7nvtmo_0

# Collect static files
RUN python manage.py collectstatic --noinput

# Create media directory
RUN mkdir -p /app/mystorelink/media

# Expose port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "mystorelink.wsgi:application"]