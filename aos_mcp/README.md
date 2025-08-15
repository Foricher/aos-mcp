
## build project 

### syncing the environment 
uv sync

### activate virtual environmment 
source /aos-ssh/.venv/bin/activate

### run 
uv run --native-tls ale_aos_mcp 



## docker
### build image
docker build -t foricher/ale-aos-mcp:0.0.9 .

### run image
docker run -it -p 8000:8000  -v ./data:/app/data -e MCP_TRANSPORT=sse docker.io/foricher/ale-aos-mcp:0.0.9


## mcp inspector

npx @modelcontextprotocol/inspector