# STEP 4: Production YClients Parser - Final Version
FROM python:3.10-slim
WORKDIR /app

# Install all required dependencies for production parser
RUN pip install --no-cache-dir fastapi uvicorn asyncpg

# Copy the production parser
COPY production_parser.py .

EXPOSE 8000
CMD ["python", "production_parser.py"]
