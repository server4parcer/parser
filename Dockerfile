# STEP 3: Database integration - add asyncpg for PostgreSQL
FROM python:3.10-slim
WORKDIR /app

# Install FastAPI, uvicorn and database dependencies
RUN pip install --no-cache-dir fastapi uvicorn asyncpg

# Copy the database-enabled application
COPY database_app.py .

EXPOSE 8000
CMD ["python", "database_app.py"]
