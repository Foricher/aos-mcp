#!/usr/bin/env just --justfile
export PATH := join(justfile_directory(), ".env", "bin") + ":" + env_var('PATH')
set positional-arguments

# Default recipe to display help
default:
    @echo "TL;DR"
    @echo "just run"
    @echo ""
    @echo "Details:"
    @just --list

alias all := start
alias run := start
alias up := start

# Build Docker images
build *OPT:
    @echo "🔨️  Building images..."
    docker compose -f ./deploy/docker-compose.yaml -p aos build {{OPT}}

# Start Docker containers (user can add --build)
start *OPT:
    @echo "🧪  Starting containers..."
    docker compose -f ./deploy/docker-compose.yaml -p aos up {{OPT}}

# Stop Docker container
stop:
    @echo "🛑  Stopping containers..."
    -docker compose -f ./deploy/docker-compose.yaml -p aos down 2>/dev/null || true

# Restart container
restart: stop start

# rebuild each layer of the images without using any cached layers
rebuild:
    # uv cache clean
    set dotenv-filename := ".env.docker"
    docker compose -f ./deploy/docker-compose.yaml -p aos build --no-cache
