```bash
# Change directory to backend
cd backend

# Make .env file
cp .env.example .env
```

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -r requirements.txt

# Activate venv
. .venv/bin/activate

# Start up FastAPI
uvicorn app.main:app --reload
```
