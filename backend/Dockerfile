FROM python:3.13-slim

WORKDIR /backend

COPY requirements.txt /backend/

RUN pip install -r requirements.txt --no-cache-dir

COPY . /backend/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--lifespan", "on", "--log-level", "debug"]
