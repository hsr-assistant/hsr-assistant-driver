import asyncio
import logging
import os
import sys
import traceback

from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

from hsr_assistant_driver.driver import (
    HSR_ASSISTANT_ARGS_JSON_SCHEMA,
    call_hsr_assistant,
)


def tool_definition() -> types.Tool:
    return types.Tool(
        name="hsr_assistant",
        description="",
        inputSchema=HSR_ASSISTANT_ARGS_JSON_SCHEMA,
    )


async def tool_call(*args, **kwargs) -> types.CallToolResult:
    if "run_config" not in kwargs:
        kwargs["run_config"] = None
    try:
        result = await call_hsr_assistant(*args, **kwargs)
        if isinstance(result, str):
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=result)]
            )
        else:
            raise NotImplementedError
    except Exception:
        msg = f"Error calling hsr_assistant, traceback:\n{traceback.format_exc()}"
        logging.exception(msg)
        return types.CallToolResult(
            isError=True, content=[types.TextContent(type="text", text=msg)]
        )


async def call_tool_request_handler(
    request: types.CallToolRequest,
) -> types.ServerResult:
    name = request.params.name
    assert name == "hsr_assistant", "Tool name is not hsr_assistant"
    arguments = request.params.arguments
    result = await tool_call(**arguments)
    return types.ServerResult(root=result)


async def list_tools_request_handler(
    _request: types.ListToolsRequest,
) -> types.ServerResult:
    return types.ServerResult(root=types.ListToolsResult(tools=[tool_definition()]))


async def start_server(mcp_server: Server):
    try:
        async with stdio_server() as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                initialization_options=InitializationOptions(
                    server_name="tool-hsr-assistant",
                    server_version="0.1.0",
                    capabilities=types.ServerCapabilities(
                        tools=types.ToolsCapability()
                    ),
                ),
            )
    except Exception as e:
        logging.critical("Unhandled exception in MCP server: %s", e)
        sys.exit(1)


def main():
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL"),
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    mcp_server = Server("tool-hsr-assistant")
    mcp_server.request_handlers[types.CallToolRequest] = call_tool_request_handler
    mcp_server.request_handlers[types.ListToolsRequest] = list_tools_request_handler
    try:
        asyncio.run(start_server(mcp_server))
    except KeyboardInterrupt:
        logging.warning("MCP server shutdown by user.")
    except Exception as e:
        logging.critical("Failed to start MCP server: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
