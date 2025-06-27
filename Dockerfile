# STEP 2: FastAPI upgrade - minimal dependencies
FROM python:3.10-slim
WORKDIR /app

# Install FastAPI and uvicorn only
RUN pip install --no-cache-dir fastapi uvicorn

# Copy the FastAPI application
COPY fastapi_app.py .

EXPOSE 8000
CMD ["python", "fastapi_app.py"]
