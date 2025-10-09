# Alcatel-Lucent Enterprise AOS ssh server

## Overview
aos_ssh is a Python-based RESTful service built with [FastAPI](https://github.com/fastapi/fastapi) and [Paramiko-NG](https://github.com/ploxiln/paramiko-ng)
that simplifies the management of network switches over SSH. It reads connection parameters from structured JSON files and exposes endpoints to:
- 🔌 Establish SSH sessions (with or without jump hosts)
- 📥 Retrieve switch data (e.g., configuration, status)
- ⚙️ Execute commands remotely
- 📡 Monitor and manage multiple switches efficiently

This tool is ideal for network automation tasks, remote diagnostics, and centralized switch control in distributed environments.
This service also acts as a transport layer for MCP (Multi-Component Platform) applications, enabling them to securely and programmatically interact with
network devices through a unified API interface.

## Installation 
We recommend using [uv](https://docs.astral.sh/uv/) to manage your Python projects.
### Syncing the environment
Syncing ensures that all project dependencies are installed and up-to-date with the lockfile.
If the project virtual environment (`.venv`) does not exist, it will be created.
```bash
cd aos_ssh
uv sync
```

### Running the standalone AOS SSH development tools
To run aos_ssh command with uv from the aos_ssh directory:
```bash
uv run ale_aos_ssh
```

## Quickstart
Run aos_ssh and browse http://127.0.0.1:8110

You should get something like this:
```json
{
  "aos ssh api": "1.0.0"
}
```
You can interact with it by browsing http://127.0.0.1:8110/docs

Especially the API http://127.0.0.1:8110/docs#/default/execute_command_command_post
```bash
curl -X 'POST' 'http://127.0.0.1:8110/command' \
  -H 'accept: application/json' -H 'Content-Type: application/json' \
  -d '{
  "host": "172.25.190.13",
  "command": "show system"
}' 
```
You should get a 200 OK with something like this:
```json
{
  "stdout": "System:\n  Description:  Alcatel-Lucent Enterprise OS[...]",
  "stderr":""
}
```

You can download the OpenAPI specification from http://127.0.0.1:8110/redoc

## 🛠️ Build & Publish package

### 🔨️ Build Python package into source distributions and wheels
```bash
uv build
```

### 📤 Upload distributions to pypi.org
```bash
uv publish
```

## 🛠️ Build & Publish Docker image

### 🔨Build the docker image
```bash
docker build -t ale-aos-ssh:0.1.2 .
```

### 🧪 Run the container locally
```bash
docker run -it -p 8120:8110 -v ./data/aos-ssh-host-brest.json:/app/data/aos-ssh-host.json -v ./data/aos-ssh-conf.yaml:/app/data/aos-ssh-conf.yaml  ale-aos-ssh:0.1.2
```

