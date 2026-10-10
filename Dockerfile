FROM python:3.11-slim

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY frontend ./frontend

EXPOSE 8000

# Honor the platform-provided $PORT (Render / Railway / Fly inject it);
# default to 8000 for local docker-compose runs.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
