FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.12.10 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_NO_CACHE=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install dependencies before copying application source.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Install the application and generate the model.
COPY README.md ./
COPY src/ ./src/
COPY scripts/train_model.py ./scripts/train_model.py
RUN uv sync --frozen --no-dev --no-editable \
    && python scripts/train_model.py

# Run the service as a non-root user.
RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).close()"]

CMD ["uvicorn", "dsan6700_ml_service.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
