# ---- backend container ----
# Build this container in root directory
# e.g. `docker build -f backend/Dockerfile -t uvicorn-backend .`

FROM python:3.11.4-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY . .

WORKDIR /app/backend
RUN uv pip install -r requirements.txt --system

# Install open_deep_researcher
RUN uv pip install --editable ../ --system

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
