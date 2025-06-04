# Set the python version as a build-time argument
# with Python 3.11 as the default
ARG PYTHON_VERSION=3.11-slim
FROM python:${PYTHON_VERSION}

# Create a virtual environment
RUN python -m venv /opt/venv

# Set the virtual environment as the current location
ENV PATH=/opt/venv/bin:$PATH

# Upgrade pip
RUN pip install --upgrade pip

# Set Python-related environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install OS dependencies
RUN apt-get update && apt-get install -y \
    # for postgres
    libpq-dev \
    # for Pillow
    libjpeg-dev \
    # other
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create the code directory
RUN mkdir -p /code

# Set the working directory
WORKDIR /code

# Copy the requirements file into the container
COPY requirements.txt /tmp/requirements.txt

# Copy the project code into the container's working directory
COPY ./mystorelink /code

# Install the Python project requirements
RUN pip install -r /tmp/requirements.txt

# Set environment variables for the Django app (build-time and runtime)
ARG DJANGO_SECRET_KEY
ENV DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}

ARG DJANGO_DEBUG=False
ENV DJANGO_DEBUG=${DJANGO_DEBUG}

ARG DATABASE_URL
ENV DATABASE_URL=${DATABASE_URL}

ARG SUPABASE_URL
ENV SUPABASE_URL=${SUPABASE_URL}

ARG SUPABASE_KEY
ENV SUPABASE_KEY=${SUPABASE_KEY}

ARG SUPABASE_SERVICE_KEY
ENV SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}

ARG GOOGLE_OAUTH2_CLIENT_ID
ENV GOOGLE_OAUTH2_CLIENT_ID=${GOOGLE_OAUTH2_CLIENT_ID}

ARG GOOGLE_OAUTH2_CLIENT_SECRET
ENV GOOGLE_OAUTH2_CLIENT_SECRET=${GOOGLE_OAUTH2_CLIENT_SECRET}

ARG NUTRITION_API_KEY
ENV NUTRITION_API_KEY=${NUTRITION_API_KEY}

# Set Django settings module
ENV DJANGO_SETTINGS_MODULE=mystorelink.settings

# Database isn't available during build
# Run commands that do not need the database
RUN python manage.py collectstatic --noinput

# Set the Django default project name
ARG PROJ_NAME="mystorelink"

# Create a bash script to run the Django project
# This script will execute at runtime when
# the container starts and the database is available
RUN printf "#!/bin/bash\n" > ./mystorelink_runner.sh && \
    printf "RUN_PORT=\"\${PORT:-8000}\"\n\n" >> ./mystorelink_runner.sh && \
    printf "sync\n" >> ./mystorelink_runner.sh && \
    printf "sleep 2\n" >> ./mystorelink_runner.sh && \
    printf "python manage.py migrate --no-input\n" >> ./mystorelink_runner.sh && \
    printf "gunicorn ${PROJ_NAME}.wsgi:application --bind \"0.0.0.0:\$RUN_PORT\"\n" >> ./mystorelink_runner.sh

# Make the bash script executable
RUN chmod +x mystorelink_runner.sh

# Clean up apt cache to reduce image size
RUN apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Expose port
EXPOSE 8000

# Run the Django project via the runtime script
# when the container starts
CMD ./mystorelink_runner.sh