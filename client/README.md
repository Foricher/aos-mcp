# Alcatel-Lucent Enterprise AOS MCP test client

## ⚠️ Disclaimer

Important Notice:
<br>The Model Context Protocol (MCP) is a rapidly evolving framework. The APIs, tools, templates, and usage examples
provided in this repository are based on the current state of MCP and may become outdated as the protocol develops.
We recommend consulting the [official MCP documentation](https://modelcontextprotocol.io/docs/getting-started/intro)
for the most up-to-date information.


## Overview
- The directory (`.cursor`) contains the (`mcp.json`) configuration file for [Cursor AI](https://cursor.com/en-US/docs/context/mcp)
- The directory (`.gemini`) contains the (`settings.json`) configuration file for [gemini-cli](https://google-gemini.github.io/gemini-cli/docs/tools/mcp-server.html)
- The directory (`.vscode`) contains the (`mcp.json`) configuration file for [VS Code](https://code.visualstudio.com/docs/copilot/customization/mcp-servers)
- aos_aos_client is a Python-based MCP test client built with [FastMCP](https://github.com/jlowin/fastmcp)


## Installation 
We recommend using [uv](https://docs.astral.sh/uv/) to manage your Python projects.
### Syncing the environment
Syncing ensures that all project dependencies are installed and up-to-date with the lockfile.
If the project virtual environment (`.venv`) does not exist, it will be created.
```bash
cd client
uv sync
```

### 🚀 Running the standalone AOS MCP test client
To run client command with uv from the client directory:
```bash
uv run  ale_aos_client
```

To test the list_devices tool
```bash
uv run ale_aos_client list_devices
```

