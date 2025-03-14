# Open Deep Researcher

## 🚀 Quickstart

Ensure you have API keys set for your desired tools.

Select a web search tool (by default Open Deep Research uses Tavily):

- [Tavily API](https://tavily.com/) - General web search
- [ArXiv](https://arxiv.org/) - Academic papers in physics, mathematics, computer science, and more
- [PubMed](https://pubmed.ncbi.nlm.nih.gov/) - Biomedical literature from MEDLINE, life science journals, and online books

### Running LangGraph Studio UI locally

Clone the repository:

```bash
git clone https://github.com/osushinekotan/open-deep-researcher.git
cd open-deep-researcher
```

Edit the `.env` file with your API keys (e.g., the API keys for default selections are shown below):

```bash
cp .env.example .env
```

Launch the assistant with the LangGraph server locally, which will open in your browser:

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and start the LangGraph server
uv sync
uv run langgraph dev
```

Use this to open the Studio UI:

```
        Welcome to

╦  ┌─┐┌┐┌┌─┐╔═╗┬─┐┌─┐┌─┐┬ ┬
║  ├─┤││││ ┬║ ╦├┬┘├─┤├─┘├─┤
╩═╝┴ ┴┘└┘└─┘╚═╝┴└─┴ ┴┴  ┴ ┴

- 🚀 API: http://127.0.0.1:2024
- 🎨 Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
- 📚 API Docs: http://127.0.0.1:2024/docs
```

### Running Web App Locally with Docker

```bash
docker compose up --build
```

- backend: `FastAPI`
- frontend: `Next.js`
