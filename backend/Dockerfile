# backend/Dockerfile

FROM python:3.11-slim-bullseye

# 1) Create a working directory at /app
WORKDIR /app

# 1a) (NEW) Install system packages for debugging
RUN apt-get update && apt-get install -y iputils-ping netcat

# 2) Copy in requirements first, to leverage Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 3) Copy the rest of the backend code into the container
COPY . /app/backend

# 4) Switch into /app/backend so all "app.*" references work
WORKDIR /app/backend

# 5) Expose FastAPI port (optional)
EXPOSE 8000

# 6) Default command is uvicorn, but overridden by docker-compose.yml if needed
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
