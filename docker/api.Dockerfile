# syntax=docker/dockerfile:1.7
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml ./
COPY airedteam ./airedteam
COPY alembic ./alembic
COPY alembic.ini ./
ENV PIP_DEFAULT_TIMEOUT=1800
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --retries 10 --prefer-binary -e .
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn airedteam.api.app:create_app --factory --host 0.0.0.0 --port 8000"]
