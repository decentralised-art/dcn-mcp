import os
import sys
import unittest
from pathlib import Path

import anyio
import mcp.types as types
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class MCPStdioTests(unittest.TestCase):
    def test_stdio_server_lifecycle(self):
        async def _run():
            env = dict(os.environ)
            existing_path = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = str(SRC) if not existing_path else f"{SRC}:{existing_path}"
            server = StdioServerParameters(
                command=sys.executable,
                args=["-m", "dcn_mcp.server", "stdio"],
                env=env,
                cwd=str(ROOT),
            )
            async with stdio_client(server) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()

                    tools_page_1 = await session.list_tools()
                    tool_names_page_1 = {tool.name for tool in tools_page_1.tools}
                    self.assertIn("core.connector_exists", tool_names_page_1)
                    self.assertTrue(tools_page_1.nextCursor)

                    tools_page_2 = await session.list_tools(params=types.PaginatedRequestParams(cursor=tools_page_1.nextCursor))
                    tool_names_page_2 = {tool.name for tool in tools_page_2.tools}
                    self.assertTrue(tool_names_page_2)
                    self.assertNotEqual(tool_names_page_1, tool_names_page_2)

                    resources_page_1 = await session.list_resources()
                    resource_uris_page_1 = {str(resource.uri) for resource in resources_page_1.resources}
                    self.assertIn("dcn://resource/core.dcn_core_primer", resource_uris_page_1)

                    if resources_page_1.nextCursor:
                        resources_page_2 = await session.list_resources(params=types.PaginatedRequestParams(cursor=resources_page_1.nextCursor))
                        self.assertTrue(resources_page_2.resources)

                    read_result = await session.read_resource("dcn://resource/core.dcn_core_primer")
                    self.assertEqual(len(read_result.contents), 1)
                    self.assertIn("format-agnostic", read_result.contents[0].text)
                    self.assertEqual(str(read_result.contents[0].uri), "dcn://resource/core.dcn_core_primer")

                    call_result = await session.call_tool("core.build_parent_connector", {"name": "piece", "child_names": ["a", "b"]})
                    self.assertFalse(call_result.isError)
                    self.assertEqual(call_result.structuredContent["data"]["name"], "piece")
                    self.assertEqual(len(call_result.structuredContent["data"]["dimensions"]), 2)

        anyio.run(_run)


if __name__ == "__main__":
    unittest.main()
