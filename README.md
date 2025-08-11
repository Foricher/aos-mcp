
# ALE AOS mcp server 

This project provides a mcp (model context protocol) server for alcatel aos switches, see https://modelcontextprotocol.io/docs/getting-started/intro.  
It contains two subprojects :
 - aos_ssh : provides a rest API to executes ssh command on AlE aos switches
 - aos_mcp : mcp server providing mcp tools to llm to executes basic ssh commands through aos_ssh server.  


 ## copilot sample

![Example with copilot](pictures/copilot.png)


## run docker compose

```  
 cd deploy
 docker compose up 
``` 

## mcp inspector

```  
npx @modelcontextprotocol/inspector
```  


## gemini cli

Zscaler issue
``` 
set NODE_TLS_REJECT_UNAUTHORIZED=0
``` 

``` 
npx https://github.com/google-gemini/gemini-cli
``` 