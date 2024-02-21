ARG PYTHON_VERSION="3.11-slim"
ARG VERSION="0.0.1"

FROM python:${PYTHON_VERSION}


LABEL author="Stephen Ling <lingfromsh@163.com>"
LABEL application="message"
LABEL description="A general message notification service"
LABEL version=${VERSION}

WORKDIR /docker-entrypoint.d

EXPOSE 8000
EXPOSE 8443

WORKDIR /app

COPY poetry.lock /app/poetry.lock
COPY pyproject.toml /app/pyproject.toml

RUN apt update -y && apt upgrade -y && apt install -y gcc libpq-dev
RUN pip install --upgrade pip && pip install poetry
RUN poetry install
