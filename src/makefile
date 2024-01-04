dev:
	@uvicorn main:app --host 0.0.0.0 --port 8000 --reload --ssl-keyfile server.key --ssl-certfile server.crt

serve:
	@gunicorn main:app --name message-gunicorn --workers 8 --worker-class uvicorn_worker.MessageUvicornWorker --bind 0.0.0.0:8000 --preload --pid gunicorn.pid --keep-alive 120 --keyfile server.key --certfile server.crt --ca-certs server.csr
