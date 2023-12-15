#!/bin/bash

cd /app

uvicorn --host 0.0.0.0 --port 8000 --reload main:app
