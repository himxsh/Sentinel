# Sentinel agent + product UI
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY lambdas ./lambdas
COPY infra ./infra
COPY scripts ./scripts

RUN pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src:/app
EXPOSE 8000

# DATABASE_URL and other secrets via env / Secrets Manager at runtime — never bake in.
CMD ["uvicorn", "sentinel.server:app", "--host", "0.0.0.0", "--port", "8000"]
