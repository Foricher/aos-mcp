
import dataclasses
from typing import Any, List,Optional
from dataclasses import dataclass


devices = [] # Global list to store devices

def get_device_by_ip_address(ip: str) -> Optional['Device']:
    return next((d for d in devices if d.ip_address == ip), None)


@dataclass
class Device :
   ip_address: str
   user : str
   password : str
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
        devices.append(device)
   
    


