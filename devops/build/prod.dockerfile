ARG PYTHON_VERSION="3.12-slim"
ARG VERSION="0.0.1"

FROM python:${PYTHON_VERSION}


LABEL author="Stephen Ling <lingfromsh@163.com>"
LABEL description="A general message notification service"
LABEL version=${VERSION}

WORKDIR /docker-entrypoint.d


EXPOSE 8000
EXPOSE 8443

WORKDIR /app
