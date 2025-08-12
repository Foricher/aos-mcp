
import dataclasses
import json
from typing import Optional
from .device_manager import Device, devices, get_device_by_host 
from fastapi import FastAPI, HTTPException
import uvicorn
from . import ssh_session_manager as SSHSessionManager
from pydantic import BaseModel
import argparse

aos_filename = "data/aos.json"

app = FastAPI(debug=True)
def load_conf(aos_filename):
    with open(aos_filename) as f:
        data = json.load(f)
        for fields in data :
            Device.load(fields)


@app.get("/")
def read_root():
    return {"aos ssh api": "1.0.0"}


@app.post("/management/devices")
def set_device(device: Device):
    """Create/upadte a device entry."""
    current_device = get_device_by_host(device.host)
    if current_device is not None:
        devices.remove(current_device)
    devices.append(device)
    data = [dataclasses.asdict(d) for d in devices]
    with open(aos_filename, 'w') as fd:
        json.dump(data, fd, indent=2)
    return {"status": "success", "device": device}

@app.delete("/management/devices/{host}")
def delete_device(host: str):
    """Delete a device entry by IP address."""
    device = get_device_by_host(host)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    devices.remove(device)
    data = [dataclasses.asdict(d) for d in devices]
    with open(aos_filename, 'w') as fd:
        json.dump(data, fd, indent=2)
    return {"status": "success", "message": f"Device {host} deleted successfully."}


    
@app.get("/devices/{host}") 
def get_device(host: str) -> Device:      
    """Get a device entry by host.""" 
    device = get_device_by_host(host)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")  

    return {    
        "host": device.host,    
    }  # Return the device as a dictionary  



@app.get("/devices")
def read_devices():
    def to_dict(device: Device) -> dict:
        return {
#            "serial_number": device.serial_number,
            "host": device.host,
#            "name": device.name,
#            "description": device.description,
#            "organization": device.organization,
#            "site": device.site
        }
    arr = list(map(to_dict, devices))
    return arr

class Command(BaseModel):
    host: str
    command: str 
class CommandResponse(BaseModel):
    stdout: Optional[str] = None
    stderr :Optional[str] = None

@app.post("/command")
def execute_command(command:Command):
    device = get_device_by_host(command.host)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    session, error_msg = SSHSessionManager.get_or_create_session(command.host, device.user, device.password,port=device.port)
    if session is None: 
        raise HTTPException(status_code=404, detail=f"Failed to create SSH session: {error_msg}")
    stdin, stdout, stderr = SSHSessionManager.execute_command(command.host, command.command)
    print(f"Command executed: {command.command} on {command.host}\n[stsdout]\n{stdout}\n[stderr]\n{stderr}")
    return CommandResponse(
        stdout=stdout,
        stderr=stderr
    )

def main():
    parser = argparse.ArgumentParser(description='AOS MCP Server Options')
    parser.add_argument('--port', type=int, default=8110, help='AOS SSH Server Port')
    parser.add_argument('--log-level', type=str, default="info", help='Log level (debug, info, warning, error, critical)')
    parser.add_argument('--aos-file', type=str, default="data/aos.json", help='aos configuration file')
    args = parser.parse_args()
    print(f"Start AOS SSH Server Port: {args.port}, log-level: {args.log_level}, aos-file: {args.aos_file}")
    globals()["aos_filename"]  = args.aos_file
    print(globals()["aos_filename"] )
    load_conf(args.aos_file)
    print(devices)
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level=args.log_level)


if __name__ == "__main__":
    main()
