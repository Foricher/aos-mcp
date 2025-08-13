
## build project 

### syncing the environment 
uv sync

### activate virtual environmment 
source /aos_ssh/.venv/bin/activate

### run 
uv run aos_ssh

### build package
uv build
uv publish

## docker
### build image
docker build -t foricher/ale-aos-ssh:0.0.7 .

### run image
docker run -it -p 8120:8110 -v ./data:/app/data docker.io/foricher/ale-aos-ssh:0.0.7


