FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir ".[postgres]"

RUN useradd --create-home netwatch
USER netwatch

EXPOSE 8000
CMD ["uvicorn", "--factory", "netwatch.main:create_app", "--host", "0.0.0.0", "--port", "8000"]
