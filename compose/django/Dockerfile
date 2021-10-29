
FROM python:3.9-slim-bullseye

ARG DJANGO_UID
ARG DJANGO_GID
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
  # dependencies for building Python packages:
  && apt-get install -y build-essential \
  # psycopg2 dependencies:
  && apt-get install -y libpq-dev \
  # Translations dependencies:
  && apt-get install -y gettext \
  # silence a 'deferred' warning:
  && apt-get install -y apt-utils \
  # cleaning up unused files:
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

RUN addgroup --gid $DJANGO_GID django \
    && adduser --system --uid $DJANGO_UID --ingroup django django

# Requirements are installed here to ensure they will be cached.
COPY ./requirements.txt /requirements.txt
RUN pip --no-cache-dir install -r /requirements.txt

COPY --chown=django:django ./compose/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint  &&  chmod +x /entrypoint


COPY --chown=django:django ./compose/django/start /start
RUN sed -i 's/\r$//g' /start  &&  chmod +x /start
COPY --chown=django:django . /app

WORKDIR /app

ENTRYPOINT ["/entrypoint"]
