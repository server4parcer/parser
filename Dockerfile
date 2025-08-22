# TimeWeb Cloud Apps optimized Dockerfile with official Playwright base
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set working directory
WORKDIR /app

# Install curl for health checks (Playwright dependencies already included)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright browsers are pre-installed in base image

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data/export

# Expose port 8000 for TimeWeb
EXPOSE 8000

# Health check for TimeWeb
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["python", "lightweight_parser.py"]
