
import dataclasses
from typing import Any, List,Optional
from dataclasses import dataclass
from dataclasses import field


devices = [] # Global list to store devices

def get_device_by_host(host: str) -> Optional['Device']:
    return next((d for d in devices if d.host == host), None)


@dataclass
class Device :
   host: str
   user : str
   password : str
   port : int = field(default=22)
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
   
    


