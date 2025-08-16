
# ALE AOS mcp server 

This project provides a mcp (model context protocol) server for alcatel aos switches, see https://modelcontextprotocol.io/docs/getting-started/intro. 
Basic switch cli commands can vbe used through a ssh connection.
It enables LLM interactions with alcatel aos network switches.
It contains two subprojects :
 - aos_ssh : provides a rest API to run ssh cli command on ALE aos switches
 - aos_mcp : mcp server providing mcp tools to llm to run basic ssh commands through aos_ssh server REST api.  

## Architecture

![ALE AOS mcp server architecture](pictures/ale_aos_mcp.drawio.png)


## Deploy mcp and ssh servers 

Docker images for aos_ssh and aos_mcp servers are availables:
  - docker.io/foricher/ale-aos-ssh:[tag]
  - docker.io/foricher/ale-aos-mcp:[tag]

Under  `deploy` folder, the mcp server side is available with a docker compose deployment.

Update `data\aos-ssh.json` file with your switches host, user, password for ssh connections. 

```json
[ 
    { 
      "host": "host_or_ip_address1",
      "user": "user", 
      "password": "password"
    },
    { 
      "host": "host_or_ip_address2",
      "user": "user", 
      "password": "password",
      "port" : 22 //optional
    }
]
```


`data\mcp_tools.yaml` file describes tools used by LLM to run aos commands. 




`docker-compose.yaml` file:
```yaml
services:
  aos-ssh:
    image: docker.io/foricher/ale-aos-ssh:0.0.9
    ports:
      - "8210:8110"
    volumes:
      - ./data/aos-ssh.json:/app/data/aos-ssh.json
  aos-mcp:
    image: docker.io/foricher/ale-aos-mcp:0.0.9
    ports:
      - "8000:8000"
    environment:
      - ALE_AOS_MCP_SSH_URL=http://aos-ssh:8110
      - ALE_AOS_MCP_TRANSPORT=streamable-http
#      - ALE_AOS_MCP_TRANSPORT=sse
    volumes:
      - ./data:/app/data
    depends_on:
      - aos-ssh
```

Launch docker compose

```bash  
 cd deploy
 docker compose up 
``` 

By default, mcp server is deployed with transport streamable-http

## Test with mcp inspector

You can test aos mcp server by using mcp inpector tool, see https://modelcontextprotocol.io/legacy/tools/inspector 

```  
npx @modelcontextprotocol/inspector
```  

- Use Tranport Type : Streamable HTTP
- Enter your url : http://mcp-host:8000/mcp
- Enter proxy session Token


![mcp inspector](pictures/mcp-inspector.png)


 ## Client



- Connect to remote MCP server with Streamable http transport.

  Both servers ale_aos_mcp, ale_aos_ssh run remotely.

 ```json
 {
  "mcpServers": {
    "aos": {
      "type": "http",
      "url": "http://<aos-mcp-host>:8000/mcp"
    }
  }
}

 ```

- Connect to local MCP server with stdio transport.

  Local ale_aos_mcp server connect to a remote ale_aos_ssh server via provided argument --aos-ssh-url url.


 ```json
{
    "mcpServers": {
        "aos": {
            "command": "uv run ale_aos_mcp",
            "args": [
                "--aos-ssh-url",
                "http://<aos-ssh-host>:8210"
            ],
            "env": {
            }
        }
    }
}
 ```

 ### Use Github Copilot with visual stdio code

Under your workspace, inside `.vscode` folder, put file `mcp.json` as below. 
- with Streamable http transport

 ```json
 {
  "servers": {
    "aos": {
      "type": "http",
      "url": "http://<aos-mcp-host>:8000/mcp"
    }
  }
}

 ```

- with stdio transport

 ```json
{
    "servers": {
        "aos": {
            "command": "uv run ale_aos_mcp",
            "args": [
                "--aos-ssh-url",
                "http://<aos-ssh-host>:8210"
            ],
            "env": {
            }
        }
    }
}
 ```

![Example with github copilot](pictures/copilot.png)



 ### Use cursor with visual stdio code

Under your workspace, inside `.cursor` folder, put file `mcp.json` as below. 

 ```json
{
    "mcpServers": {
        "aos": {
            "url": "http://<aos-mcp-host>:8000/mcp"
        }
    }
}
 ```

![Example with cursor](pictures/cursor.png)




### Use gemini cli

 put under `.gemini` folder, file 'settings.json' as below. 

  ```json
{
  "mcpServers": {
    "aos": {
      "name": "AOS MCP Server",
      "description": "AOS MCP Server for managing AOS switches",
      "httpUrl": "http://<aos-mcp-host>:8000/mcp",
      "timeout" : 60000
    }
  }
}
```

Zscaler issue
```bash 
set NODE_TLS_REJECT_UNAUTHORIZED=0
``` 

```bash 
npx https://github.com/google-gemini/gemini-cli -m gemini-2.5-flash
``` 

![gemini cli](pictures/gemini-cli.png)
