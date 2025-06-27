# SIMPLEST POSSIBLE DOCKERFILE - Hello World only
FROM python:3.10-slim
WORKDIR /app
COPY hello_world.py .
EXPOSE 8000
CMD ["python", "hello_world.py"]
