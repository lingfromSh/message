FROM python:3.11.6

LABEL author="shiyun.ling"

EXPOSE 8000
EXPOSE 8443

WORKDIR /app

VOLUME [ "/app" ]

ADD . /app

# keep image latest to avoid some safety problems of lib

RUN apt update -y && apt upgrade -y

RUN pip install -U pip

RUN pip install poetry

RUN poetry install
