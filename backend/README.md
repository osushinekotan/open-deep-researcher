## Local

```bash
# Change directory to backend
cd backend

# Make .env file
cp .env.example .env
```

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv

# Activate venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
uv pip install --editable ../

# Start up FastAPI
uv run uvicorn app.main:app --reload
```
