FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml ./
COPY airedteam ./airedteam
COPY alembic ./alembic
COPY alembic.ini ./
RUN pip install --no-cache-dir -e .
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn airedteam.api.app:create_app --factory --host 0.0.0.0 --port 8000"]
