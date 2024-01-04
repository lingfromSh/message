dev:
	@cd .. && uvicorn message.main:app --host 0.0.0.0 --port 8000 --reload

serve:
	@cd .. && gunicorn message.main:app --name message-gunicorn --workers 8 --worker-class message.uvicorn_worker.MessageUvicornWorker --bind 0.0.0.0:8000 --preload --pid gunicorn.pid --keep-alive 120
