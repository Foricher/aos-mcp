# Alcatel-Lucent Enterprise AOS mcp server

## Overview
aos_mcp is a Python-based MCP server built with [FastMCP](https://github.com/jlowin/fastmcp)

aos_mcp provides a mcp (Model Context Protocol) server for Alcatel-Lucent Enterprise AOS switches,
see https://modelcontextprotocol.io/docs/getting-started/intro.

aos_mcp provides MCP context and tools to LLM to run basic aos switch cli commands through aos_ssh server REST api.
- 🔌 Establish SSH sessions (with or without jump hosts)
- 📥 Retrieve switch data (e.g., configuration, status)
- ⚙️ Execute commands remotely
- 📡 Monitor and manage multiple switches efficiently

## Installation 
We recommend using [uv](https://docs.astral.sh/uv/) to manage your Python projects.
### Syncing the environment
Syncing ensures that all project dependencies are installed and up-to-date with the lockfile.
If the project virtual environment (`.venv`) does not exist, it will be created.
```bash
cd aos_mcp
uv sync
```

### 🚀 Running the standalone AOS SSH development tools
To run aos_ssh command with uv from the aos_ssh directory:
```bash
uv run ale_aos_mcp --aos-ssh-url http://localhost:8120 --transport streamable-http
```

## 🛠️ Build & Publish package

### 🔨️ Build Python package into source distributions and wheels
```bash
uv build
```

### Install package
```bash
uv pip install --system dist/ale_aos_mcp-0.1.0-py3-none-any.whl
```


## 🛠️ Build & Publish Docker image

### 🔨Build the docker image
```bash
docker build -t ale-aos-mcp:0.1.2 .
```

### 🧪 Run the container locally
```bash
docker run -it -p 8000:8000  -v ./data:/app/data -e MCP_TRANSPORT=streamable-http ale-aos-mcp:0.1.2
```


## mcp inspector

```bash
npx @modelcontextprotocol/inspector
```

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/fr/install-mcp?name=aos&config=eyJ1cmwiOiJodHRwOi8vbG9jYWxob3N0OjgwMDAvbWNwIn0%3D)
