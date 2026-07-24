FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -e ".[api]"
EXPOSE 8000
# Process listens on 0.0.0.0 inside the container; compose publishes only 127.0.0.1 on the host.
CMD ["uvicorn", "wellguard.api:app", "--host", "0.0.0.0", "--port", "8000"]
