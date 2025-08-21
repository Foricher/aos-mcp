
## build project 

### syncing the environment 
```bash
uv sync
```

### activate virtual environmment 
```bash
source /aos_ssh/.venv/bin/activate
```

### run 
```bash
uv run aos_ssh
```

### build package
```bash
uv build
uv publish
```

## docker
### build image
```bash
docker build -t foricher/ale-aos-ssh:0.1.2 .
```

### run image
```bash
docker run -it -p 8120:8110 -v ./data/aos-ssh-host-brest.json:/app/data/aos-ssh-host.json -v ./data/aos-ssh-conf.yaml:/app/data/aos-ssh-conf.yaml  docker.io/foricher/ale-aos-ssh:0.1.2
```

