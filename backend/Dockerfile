# Backend container image definition.
#
# This file will define the local development image for the FastAPI backend,
# install pinned Python dependencies, set the working directory, and provide the
# runtime command used by Docker Compose.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

