
## build project 

### syncing the environment 
```bash
uv sync
```

### activate virtual environmment 
```bash
source /aos-ssh/.venv/bin/activate
```

### run 
```bash
uv run --native-tls ale_aos_mcp 
```

### build package
```bash
uv build
```

### install package
```bash
uv pip install --system dist/ale_aos_mcp-0.1.0-py3-none-any.whl
```


## docker
### build image
```bash
docker build -t foricher/ale-aos-mcp:0.0.9 .
```

### run image
```bash
docker run -it -p 8000:8000  -v ./data:/app/data -e MCP_TRANSPORT=sse docker.io/foricher/ale-aos-mcp:0.0.9
```


## mcp inspector

```bash
npx @modelcontextprotocol/inspector
```
