
import dataclasses
from typing import Any, List,Optional
from dataclasses import dataclass
from dataclasses import field


@dataclass
class JumpHost:
   name : str
   public_host: str
   private_host: str
   user : str
   password : str
   public_port : int = field(default=22)
   private_port : int = field(default=22)

   @classmethod
   def load(cls, data):
        jump_box = cls(
            *[data.get(fld.name) for fld in dataclasses.fields(JumpHost)]
        )
        if jump_box.public_port is None:
            jump_box.public_port = 22
        if jump_box.private_port is None:
            jump_box.private_port = 22
        jump_ssh_boxes.append(jump_box)


@dataclass
class Device :
   host: str
   user : str
   password : str
   port : int = field(default=22)
   jump_ssh_name : Optional[str] = None
#   serial_number : Optional[List[str]] = None
#   name : Optional[str] = None
#   description : Optional[str] = None
#   organization : Optional[str] =None
#   site : Optional[str] = None

   """    @classmethod
   def load(cls, fields: dict):
        device = cls(**fields)
        devices.append (device)
   """

   @classmethod
   def load(cls, data):
        device = cls(
            *[data.get(fld.name) for fld in dataclasses.fields(Device)]
        )
        if device.port is None:
            device.port = 22
        devices.append(device)
   
    



devices : list[Device]= [] # Global list to store devices
jump_ssh_boxes : list[JumpHost]= [] # Global list to store jump boxes

def get_device_by_host(host: str) -> Optional['Device']:
    return next((d for d in devices if d.host == host), None)




