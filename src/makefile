dev:
	@uvicorn main:app --host 0.0.0.0 --port 8000 --reload

serve:
	@gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --preload --pid gunicorn.pid --max-requests 1000000 --keep-alive 120
