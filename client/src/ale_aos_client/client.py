# my_client.py
import asyncio
import sys

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


async def interact_with_server():
	print("Creating client...")

	transport = StreamableHttpTransport(url="http://localhost:8000/mcp")
	client = Client(transport)

	try:
		async with client:
			print("Client connected")
			print(
				"_________ _______  _______  _       _______\n"
				"\\__   __/(  ___  )(  ___  )( \\     (  ____ \\\n"
				"   ) (   | (   ) || (   ) || (     | (    \\/\n"
				"   | |   | |   | || |   | || |     | (_____ \n"
				"   | |   | |   | || |   | || |     (_____  )\n"
				"   | |   | |   | || |   | || |           ) |\n"
				"   | |   | (___) || (___) || (____/Y\\____) |\n"
				"   )_(   (_______)(_______)(_______|_______)\n"
			)
			# print(await client.list_tools_mcp())
			tools = await client.list_tools()
			print(tools)
			# tools -> list[mcp.types.Tool]
			for tool in tools:
				print(f"🔨  Tool: {tool.name}")
				print(f"\tDescription: {tool.description}")
				if tool.inputSchema:
					print(f"\tParameters: {tool.inputSchema}")
				# Access tags and other metadata
				if hasattr(tool, "meta") and tool.meta:
					fastmcp_meta = tool.meta.get("_fastmcp", {})
					print(f"\tTags: {fastmcp_meta.get('tags', [])}")

			print(
				" _______  _______  _______  _______           _______  _______  _______  _______\n"
				"(  ____ )(  ____ \\(  ____ \\(  ___  )|\\     /|(  ____ )(  ____ \\(  ____ \\(  ____ \\\n"
				"| (    )|| (    \\/| (    \\/| (   ) || )   ( || (    )|| (    \\/| (    \\/| (    \\/\n"
				"| (____)|| (__    | (_____ | |   | || |   | || (____)|| |      | (__    | (_____\n"
				"|     __)|  __)   (_____  )| |   | || |   | ||     __)| |      |  __)   (_____  )\n"
				"| (\\ (   | (            ) || |   | || |   | || (\\ (   | |      | (            ) |\n"
				"| ) \\ \\__| (____/\\/\\____) || (___) || (___) || ) \\ \\__| (____/\\/\\____) || (____/\\/\\____) |\n"
				"|/   \\__/(_______/\\_______)(_______)(_______)|/   \\__/(_______/(_______/\\_______)\n"
			)
			resources = await client.list_resources()
			# resources -> list[mcp.types.Resource]
			for resource in resources:
				print(f"Resource URI: {resource.uri}")
				print(f"Name: {resource.name}")
				print(f"Description: {resource.description}")
				print(f"MIME Type: {resource.mimeType}")
				# Access tags and other metadata
				if hasattr(resource, "_meta") and resource._meta:
					fastmcp_meta = resource._meta.get("_fastmcp", {})
					print(f"Tags: {fastmcp_meta.get('tags', [])}")

			print(
				"_________ _______  _______  _______  _        _______ _________ _______  _______\n"
				"\\__   __/(  ____ \\(       )(  ____ )( \\      (  ___  )\\__   __/(  ____ \\(  ____ \\\n"
				"   ) (   | (    \\/| () () || (    )|| (      | (   ) |   ) (   | (    \\/| (    \\/\n"
				"   | |   | (__    | || || || (____)|| |      | (___) |   | |   | (__    | (_____ \n"
				"   | |   |  __)   | |(_)| ||  _____)| |      |  ___  |   | |   |  __)   (_____  )\n"
				"   | |   | (      | |   | || (      | |      | (   ) |   | |   | (            ) |\n"
				"   | |   | (____/\\| )   ( || )      | (____/\\| )   ( |   | |   | (____/\\/\\____) |\n"
				"   )_(   (_______/|/     \\||/       (_______/|/     \\|   )_(   (_______/\\_______)\n"
			)
			templates = await client.list_resource_templates()
			# templates -> list[mcp.types.ResourceTemplate]
			for template in templates:
				print(f"Template URI: {template.uriTemplate}")
				print(f"Name: {template.name}")
				print(f"Description: {template.description}")
				# Access tags and other metadata
				if hasattr(template, "_meta") and template._meta:
					fastmcp_meta = template._meta.get("_fastmcp", {})
					print(f"Tags: {fastmcp_meta.get('tags', [])}")

			print(
				" _______  _______  _______  _______  _______ _________ _______ \n"
				"(  ____ )(  ____ )(  ___  )(       )(  ____ )\\__   __/(  ____ \\\n"
				"| (    )|| (    )|| (   ) || () () || (    )|   ) (   | (    \\/\n"
				"| (____)|| (____)|| |   | || || || || (____)|   | |   | (_____\n"
				"|  _____)|     __)| |   | || |(_)| ||  _____)   | |   (_____  )\n"
				"| (      | (\\ (   | |   | || |   | || (         | |         ) |\n"
				"| )      | ) \\ \\__| (___) || )   ( || )         | |   /\\____) |\n"
				"|/       |/   \\__/(_______)|/     \\||/          )_(   \\_______)\n"
			)
			prompts = await client.list_prompts()
			# prompts -> list[mcp.types.Prompt]
			for prompt in prompts:
				print(f"Prompt: {prompt.name}")
				print(f"Description: {prompt.description}")
				if prompt.arguments:
					print(f"Arguments: {[arg.name for arg in prompt.arguments]}")
				# Access tags and other metadata
				if hasattr(prompt, "_meta") and prompt._meta:
					fastmcp_meta = prompt._meta.get("_fastmcp", {})
					print(f"Tags: {fastmcp_meta.get('tags', [])}")

	except Exception as e:
		print(f"❌ Error: {e}")
	finally:
		print("Client interaction done")


async def run_test_elicit():
	print("Creating client...")
	transport = StreamableHttpTransport(url="http://localhost:8000/mcp")
	client = Client(transport)
	try:
		async with client:
			print("Client connected")
			print("Calling test_elicit tool...")
			result = await client.call_tool(
				name="test_elicit", arguments={"name": "John", "email": "john.doe@nowehere.com"}, timeout=240.0,
			)
			print(result)
	except Exception as e:
		print(f"❌ Error: {e}")
	finally:
		print("✅ Client interaction done")


async def run_list_devices():
	print("Creating client...")
	transport = StreamableHttpTransport(url="http://localhost:8000/mcp")
	client = Client(transport)
	try:
		async with client:
			print("Client connected")
			print("Calling list_devices tool...")
			result = await client.call_tool(name="list_devices")
			print(result)
	except Exception as e:
		print(f"❌ Error: {e}")
	finally:
		print("✅ Client interaction done")


def main():
	if len(sys.argv) > 1:
		if sys.argv[1] == "test_elicit":
			asyncio.run(run_test_elicit())
		elif sys.argv[1] == "list_devices":
			asyncio.run(run_list_devices())
	else:
		asyncio.run(interact_with_server())


if __name__ == "__main__":
	main()
