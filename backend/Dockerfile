# Use an official Python image that supports arm64 (3.11-slim-bullseye often works well)
FROM python:3.11-slim-bullseye

# Set the working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY app ./app
COPY tests ./tests

# Expose the FastAPI default port
EXPOSE 8000

# Default command (overridden by docker-compose command)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
