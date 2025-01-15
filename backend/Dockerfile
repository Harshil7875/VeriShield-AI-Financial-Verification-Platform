# backend/Dockerfile

# Use a Python 3.11 slim image
FROM python:3.11-slim-bullseye

# First, we'll create a working directory at /app
WORKDIR /app

# Copy only requirements.txt first, to leverage Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Now copy the entire 'backend' folder (which includes app/, tests/, etc.) to /app/backend
COPY . /app/backend

# Switch working directory to /app/backend, so that
#   'backend.app' references match the container's directory layout
WORKDIR /app/backend

# Expose the FastAPI default port (optional, but good practice)
EXPOSE 8000

# Default command to run the FastAPI app; Docker Compose can override if needed
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
