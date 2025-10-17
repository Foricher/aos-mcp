from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any


@dataclass
class JumpHost:
    name: str
    public_host: str
    private_host: str
    user: str
    password: str
    public_port: int = 22
    private_port: int = 22

    def __post_init__(self):
        if self.public_port is None:
            self.public_port = 22
        if self.private_port is None:
            self.private_port = 22
        self.public_port = int(self.public_port)
        self.private_port = int(self.private_port)

    @classmethod
    def load(cls, data: dict[str, Any]) -> JumpHost:
        jump_box = cls(**{fld.name: data.get(fld.name) for fld in dataclasses.fields(cls)})
        # if jump_box.public_port is None:
        #     jump_box.public_port = 22
        # if jump_box.private_port is None:
        #     jump_box.private_port = 22
        jump_ssh_boxes.append(jump_box)
        return jump_box


@dataclass
class Device:
    host: str
    user: str
    password: str
    jump_ssh_name: str | None
    tags: list[str] = field(default_factory=list)
    port: int = 22
    #   serial_number : Optional[List[str]] = None
    #   name : Optional[str] = None
    #   description : Optional[str] = None
    #   organization : Optional[str] =None
    #   site : Optional[str] = None

    def __post_init__(self):
        if self.port is None:
            self.port = 22
        self.port = int(self.port)

    @classmethod
    def load(cls, data: dict[str, Any]) -> Device:
        device = cls(**{fld.name: data.get(fld.name) for fld in dataclasses.fields(cls)})
        devices.append(device)
        return device

    # @classmethod
    # def load(cls, data: dict[str, Any]):
    #     device = cls(*[data.get(fld.name) for fld in dataclasses.fields(Device)])
    #     if device.port is None:
    #         device.port = 22
    #     devices.append(device)


devices: list[Device] = []  # Global list to store devices
jump_ssh_boxes: list[JumpHost] = []  # Global list to store jump boxes


def get_device_by_host(host: str) -> Device | None:
    return next((d for d in devices if d.host == host), None)


def get_device_by_tag(tag: str) -> Device | None:
    """Get device by tag name."""
    return next((d for d in devices if tag in d.tags), None)


def resolve_host_or_tag(host_or_tag: str) -> Device | None:
    """Resolve a host string which could be an IP/hostname or a tag to a Device object."""
    # First try to find by exact host match
    device = get_device_by_host(host_or_tag)
    if device:
        return device

    # If not found, try to find by tag
    device = get_device_by_tag(host_or_tag)
    if device:
        return device

    return None
