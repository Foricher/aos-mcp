#from mcp import FastMCP
from mcp.server.fastmcp import FastMCP, Context
import argparse
import requests
import yaml
import logging
from pydantic import Field
from importlib.resources import files
import os 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aos-mcp")
parser = argparse.ArgumentParser(description='AOS MCP Server Options')
parser.add_argument('--aos-ssh-url', type=str, default=os.environ.get('ALE_AOS_MCP_SSH_URL',"http://localhost:8110"), help='AOS Server URL')
parser.add_argument('--transport', type=str, default=os.environ.get('ALE_AOS_MCP_TRANSPORT',"stdio"), help='transport method (stdio, streamable-http, sse, etc.)')
parser.add_argument('--port', type=int, default=os.environ.get('ALE_AOS_MCP_PORT',8000), help='port for AOS MCP server')
parser.add_argument('--aos-tools-file', type=str, default=os.environ.get('ALE_AOS_MCP_TOOLS_FILE',""), help='mcp Tools file')
parser.add_argument('--log-level', type=str, default=os.environ.get('ALE_AOS_MCP_LOG_LEVEL',"INFO"), help='Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
args = parser.parse_args()
print(f"Using AOS SSH URL: {args.aos_ssh_url}")
print(f"Using transport: {args.transport}")


resource_path = files('ale_aos_mcp.data')
mcp_tools_file = resource_path / 'mcp_tools.yaml'
if args.aos_tools_file:
	mcp_tools_file = args.aos_tools_file

print(mcp_tools_file)

mcp = FastMCP("AOS MCP Server",host="0.0.0.0", port=args.port)



@mcp.tool()
def list_devices() -> str:
    """list all Alcatel aos switches devices.
    returns:
        str: The unstructured content of the command execution or an error message
    """
    r = requests.get(f'{args.aos_ssh_url}/devices')
    print(r.json())
    if r.status_code == 200:
        return r.text
    else:
        return f"Error executing list_devices: {r.status_code} - {r.text}"



#@mcp.tool()
def execute_command(host: str = Field(description="The host of the aos switch, host is the ip address or hostname of the switch"),
                     command: str = Field(description="The command to execute on the aos switch"), ctx:Context= None) -> str:
    """execute a command on an Alcatel AOS switch via its ip address.
       Command list : 
         - `show system`: Displays basic system information for the switch. Information includes a switch name, user-defined system description, system version
name, administrative contact, location, object ID, up time, and system services.
         - `show chassis`: Displays the basic configuration and status information for the switch chassis (serial number, model name, mac address, part number).
         - `show virtual-chassis topology`: Provide a detailed status of the virtual chassis topology.
         - `show vlan <vlanid>`: Displays VLAN information for the switch. if <vlanid> parameter is present, displays information for a specific VLAN otherwise display all vlans.
         - `show vlan <vlanid> members`: Displays VLAN port associations (VPAs) for all VLANs or a specific VLAN if <vlanid> parameter is present, for all ports. 
         - `show vlan <vlanid> members port <portid>`: Displays VLAN port associations (VPAs) for all VLANs, a specific VLAN if <vlanid> parameter is present  , for a specific port with parameter <portid> as format chassis/slot/port . 
         - `show ip routes`: Displays the IP routing table.
         - `show ip interface`: Displays the configuration and status of IP interfaces.
         - `show hardware-info`: Display hardware information for cpu, ram, flash, u-boot version.
         - `show powersupply`: Displays the hardware information and current status for chassis power supplies.
         - `show linkagg`: Displays information about static and dynamic (LACP) aggregate groups.
         - `ping <addr>`: Tests whether an IP destination can be reached from the local switch. This command sends an ICMP echo request to a destination and then waits for a reply. To ping a destination, enter the ping command and enter either the IP address or hostname of the destination. <addr> is hostname or IP address parameter to ping.
         - `traceroute <addr>`: Traces the route to a destination IP address or hostname. This command sends a series of ICMP echo requests to the destination and then waits for replies. The command displays the IP address of each hop along the route to the destination. <addr> is hostname or IP address parameter to traceroute.
         - `show interfaces <port>`: Displays the switch interfaces. Optional parameter <port> is the port to display, in format chassis/slot/port.

    args:
        host (str): The host of the aos switch, host is the ip address or hostname of the switch
        command (str): The command to execute on the aos switch
    returns:
        str: The unstructured content of the command execution or an error message
    """
    logger.info(f"Executing command: {command} on device with host: {host}")
    r = requests.post(f'{args.aos_ssh_url}/command', json={"host": host, "command": command})
    logger.debug(r.json())
    if r.status_code == 200:
        return r.json().get("stdout", "No output returned")
    else:
        return f"Error executing command: {r.status_code} - {r.text}"


@mcp.prompt()
def aos_system_hardware_info(switch_host: str) -> str:
    return f"Display system information and hardware information of switch : {switch_host}"

@mcp.prompt()
def aos_commands() -> str:
    return f"display all commands available for switches"

@mcp.resource("aos://information/{name}")
def aos_hello(name: str) -> str:
    return f"Hello from aos mcp server, {name}!"

def load_mcp_tools():
    with open(mcp_tools_file) as f:
        try:
            logger.info("Loading MCP tools from YAML file...")
            mcp_tools = yaml.safe_load(f)
            for tool in mcp_tools.get("tools", []):
                name = tool.get("name")
                title = tool.get("title","")
                description = tool.get("description", "")
                if name:
                    logger.info(f"Registering tool: {name} - {title}")
                    mcp.add_tool(execute_command, name=name, title=title, description=description)
                else:
                    logger.error(f"Skipping tool with missing name : {tool}")
        except yaml.YAMLError as exc:
            logger.error(exc)

def main():
    logger.setLevel(args.log_level.upper())
    print(logger.getEffectiveLevel())
    logger.info("aos-mcp starting port: %i, transport: %s ...", args.port, args.transport)
    logger.info("aos-ssh-url: %s",args.aos_ssh_url)
    load_mcp_tools()
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()