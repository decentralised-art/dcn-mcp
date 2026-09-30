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
            env["PYTHONPATH"] = str(SRC) if not existing_path else str(SRC) + os.pathsep + existing_path
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
                    all_tool_names = tool_names_page_1 | tool_names_page_2
                    next_cursor = tools_page_2.nextCursor
                    while next_cursor:
                        page = await session.list_tools(params=types.PaginatedRequestParams(cursor=next_cursor))
                        all_tool_names.update(tool.name for tool in page.tools)
                        next_cursor = page.nextCursor
                    for name in (
                        "create_connector", "create_transformation", "create_condition",
                        "simulate_connector", "prepare_publication", "publish_entity",
                        "confirm_publication", "execute_connector",
                    ):
                        self.assertIn(f"core.{name}", all_tool_names)
                    self.assertTrue(all(name.startswith("core.") for name in all_tool_names))

                    resources_page_1 = await session.list_resources()
                    resource_uris_page_1 = {str(resource.uri) for resource in resources_page_1.resources}
                    self.assertEqual(resource_uris_page_1, {"dcn://resource/core.dcn_core_primer"})
                    self.assertIsNone(resources_page_1.nextCursor)

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
