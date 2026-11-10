FROM python:3.12-slim AS tests
WORKDIR /service
COPY pyproject.toml ./
RUN pip install --no-cache-dir ".[dev]"
COPY app ./app
COPY tests ./tests
CMD ["python", "-m", "pytest"]

FROM python:3.12-slim AS api
WORKDIR /service
COPY pyproject.toml ./
RUN pip install --no-cache-dir .
COPY app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
