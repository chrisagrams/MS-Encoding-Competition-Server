FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt /app/

RUN pip install -r requirements.txt --no-cache-dir

COPY . /app/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--lifespan", "on", "--log-level", "debug"]
