# ULTRA MINIMAL - Just Python, no packages
FROM python:3.10-slim
WORKDIR /app
COPY ultra_minimal.py .
EXPOSE 8000
CMD ["python", "ultra_minimal.py"]
