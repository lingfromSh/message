FROM python:3.11.4

WORKDIR /app

COPY . /app

RUN pip3 install poetry && poetry install
