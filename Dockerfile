FROM python:3.13-slim
WORKDIR /app

RUN pip install uv

COPY uv.lock pyproject.toml ./
RUN uv sync --frozen --no-dev

COPY alembic.ini .
COPY alembic ./alembic

COPY main.py .
COPY app ./app

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]