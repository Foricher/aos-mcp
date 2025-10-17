from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import os
import re
from typing import Annotated

import uvicorn
import yaml
from fastapi import FastAPI, HTTPException, Query, status

# from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from . import ssh_session_manager as SSHSessionManager
from .device_manager import Device, JumpHost, devices, get_device_by_host, jump_ssh_boxes, resolve_host_or_tag

aos_host_file: str = "data/aos-ssh-host.json"
allowed_aos_commands: list[str] = []

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("aos-ssh")
app = FastAPI(title="Alcatel-Lucent Enterprise AOS SSH Server", debug=True)


def load_host(aos_file: str):
    with open(aos_file) as f:
        data = json.load(f)
        for fields in data.get("jump_ssh_hosts", []):
            JumpHost.load(fields)
        for fields in data.get("hosts", []):
            Device.load(fields)


def load_config(config_file: str):
    with open(config_file, encoding="utf-8") as f:
        try:
            logger.info("Loading config from YAML file...")
            ssh_config = yaml.safe_load(f)
            globals()["allowed_aos_commands"] = ssh_config.get("allowed_aos_commands", [])
            logger.info(f"Allowed commands: {globals()['allowed_aos_commands']}")
        except yaml.YAMLError as exc:
            logger.error(exc)


def check_command(command: str) -> bool:
    """Check if the command is allowed."""
    logger.info(f"Checking command: {command}, allowed commands: {allowed_aos_commands}")
    for allowed in allowed_aos_commands:
        if re.match(allowed, command):
            return True
    return False


@app.get("/")
def read_root():
    return {"aos ssh api": "1.0.0"}


@app.get(
    "/health",
)
def health_check():
    return {"status": "healthy"}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/management/devices")
def set_device(device: Device):
    """Create/update a device entry."""
    current_device = get_device_by_host(device.host)
    if current_device is not None:
        devices.remove(current_device)
    devices.append(device)
    data = [dataclasses.asdict(d) for d in devices]
    with open(aos_host_file, "w") as fd:
        json.dump(data, fd, indent=2)
    return {"status": "success", "device": device}


@app.delete("/management/devices/{host}")
def delete_device(host: str):
    """Delete a device entry by IP address or tag."""
    device = resolve_host_or_tag(host)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    devices.remove(device)
    data = [dataclasses.asdict(d) for d in devices]
    with open(aos_host_file, "w") as fd:
        json.dump(data, fd, indent=2)
    return {"status": "success", "message": f"Device {device.host} (requested: {host}) deleted successfully."}


@app.get("/devices/{host}")
def get_device(host: str) -> dict[str, str]:
    """Get a device entry by host or tag."""
    device = resolve_host_or_tag(host)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    return {
        "host": device.host,
    }  # Return the device as a dictionary


@app.get("/devices")
def read_devices(tags: Annotated[list[str] | None, Query(description="Filter devices by tags")] = None) -> list[dict]:
    def to_dict(device: Device) -> dict:
        return {
            "host": device.host,
            "tags": device.tags,
        }

    def device_matches_tags(device_dict: dict) -> bool:
        if tags is None:
            return True
        # Return True if the device has at least one of the specified tags
        return any(tag in device_dict["tags"] for tag in tags)

    arr = list(filter(device_matches_tags, map(to_dict, devices)))
    return arr


class Command(BaseModel):
    host: str
    command: str


class CommandResponse(BaseModel):
    stdout: str | None
    stderr: str | None


@app.post("/command")
def execute_command(command: Command):
    device = resolve_host_or_tag(command.host)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    if not check_command(command.command):
        raise HTTPException(status_code=403, detail=f"Command '{command.command}' is not allowed")
    #    session, error_msg = SSHSessionManager.get_or_create_session(command.host, device.user, device.password,
    #    port=device.port,jump_ssh_host=device)
    session, error_msg = SSHSessionManager.get_session(device)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Failed to create SSH session: {error_msg}")
    # Use the actual device host for SSH connection, not the tag
    jump_name = device.jump_ssh_name or ""  # Convert None to empty string
    stdin, stdout, stderr = SSHSessionManager.execute_command(device.host, command.command, jump_name)
    logger.debug(
        f"Command executed: {command.command} on {device.host} (requested: {command.host})\n"
        f"[stdout]\n{stdout}\n"
        f"[stderr]\n{stderr}"
    )
    return CommandResponse(stdout=stdout, stderr=stderr)


def main():
    parser = argparse.ArgumentParser(description="AOS MCP Server Options")
    parser.add_argument(
        "--port", type=int, default=os.environ.get("ALE_AOS_SSH_PORT", "8110"), help="AOS SSH Server Port"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.environ.get("ALE_AOS_SSH_LOG_LEVEL", "info"),
        help="Log level (debug, info, warning, error, critical)",
    )
    parser.add_argument(
        "--aos-ssh-conf-file",
        type=str,
        default=os.environ.get("ALE_AOS_SSH_CONF_FILE", "data/aos-ssh-conf.yaml"),
        help="aos ssh configuration file",
    )
    parser.add_argument(
        "--aos-ssh-host-file",
        type=str,
        default=os.environ.get("ALE_AOS_SSH_HOST_FILE", "data/aos-ssh-host.json"),
        help="aos ssh host file",
    )
    args = parser.parse_args()
    logger.setLevel(args.log_level.upper())
    logger.info(
        f"Start AOS SSH Server Port: {args.port}, log-level: {args.log_level}, "
        f"aos-ssh-conf-file: {args.aos_ssh_conf_file}, aos-ssh-host-file: {args.aos_ssh_host_file}"
    )
    globals()["aos_host_file"] = args.aos_ssh_host_file
    print(globals()["aos_host_file"])
    load_config(args.aos_ssh_conf_file)
    load_host(args.aos_ssh_host_file)
    #    print(devices)
    logger.info(f"Loaded {len(jump_ssh_boxes)} jump ssh hosts")
    logger.info(f"Loaded {len(devices)} devices")
    SSHSessionManager.init_ssh_session_manager()
    # origins = os.getenv("ALLOWED_ORIGINS", f"http://localhost:{args.port},http://127.0.0.1:{args.port}").split(",")
    # app.add_middleware(
    #    CORSMiddleware,
    #    allow_origins=origins,
    #    allow_credentials=True,
    #    allow_methods=["*"],
    #    allow_headers=["*"],
    # )
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level=args.log_level)


if __name__ == "__main__":
    main()
