FROM python:3.12-slim
LABEL Description="{{ cookiecutter.description }}" Maintainer="{{ cookiecutter.author_name }}"

# Basic setup
ENV POETRY_VERSION=1.8.2 \
    PYTHONUNBUFFERED=1 \
    DJANGO_STATIC_ROOT=/web/staticfiles \
    DJANGO_WORKDIR=/web/workdir

# Create workdir
RUN mkdir -p /web
WORKDIR /web

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl nodejs npm optipng jpegoptim \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

# Configure Poetry to not use virtualenvs (for Docker use)
RUN poetry config virtualenvs.create false

# Copy poetry project files
COPY pyproject.toml /web/
# Optional: copy poetry.lock if exists (ignore if not yet generated)
COPY poetry.lock /web/

# Install Python dependencies
RUN poetry install --no-interaction --no-ansi

# Copy app source files
{%- if cookiecutter.dockerize == "runserver" %}
COPY docker-files/entrypoint.sh /usr/local/bin/entrypoint.sh
{%- else %}
COPY {{ cookiecutter.app_name }} /web/{{ cookiecutter.app_name }}
COPY package.json /web/package.json
COPY wsgi.py /web/wsgi.py
COPY manage.py /web/manage.py
COPY worker.py /web/worker.py
COPY docker-files/uwsgi.ini /etc/uwsgi.ini
{%- endif %}

# Optional: install frontend dependencies
{%- if cookiecutter.dockerize != "runserver" %}
RUN npm install
{%- endif %}

# For nginx setup
{%- if cookiecutter.dockerize == "nginx" %}
VOLUME /web/nginx-conf
COPY docker-files/nginx-vhost.conf /web/nginx-conf/{{ cookiecutter.virtual_host }}
{%- endif %}

# Prepare static/media directories
RUN mkdir -p $DJANGO_STATIC_ROOT/CACHE

{%- if cookiecutter.dockerize != "runserver" %}
COPY workdir/fixtures/skeleton.json $DJANGO_WORKDIR/fixtures/skeleton.json
COPY workdir/media/filer_public $DJANGO_WORKDIR/media/filer_public
COPY workdir/.initialize $DJANGO_WORKDIR/.initialize
{%- endif %}

# Compile static assets if not in debug
{%- if cookiecutter.debug == "n" %}
RUN ./manage.py compilescss \
 && ./manage.py collectstatic --noinput --ignore='*.scss'
{%- endif %}

# Create django user
RUN useradd -M -d /web -s /bin/bash django

# Permissions and volume setup
{%- if cookiecutter.dockerize == "runserver" %}
USER django
{%- else %}
RUN chown -R django.django $DJANGO_STATIC_ROOT \
 && chown -R django.django $DJANGO_WORKDIR \
 && chown -R django.django /web/{{ cookiecutter.app_name }}/migrations

VOLUME $DJANGO_WORKDIR
{%- endif %}
