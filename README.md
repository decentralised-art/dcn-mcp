# dcn-mcp

`dcn-mcp` is a general MCP server for the Decentralized Creative Network (DCN).

It exposes:

- a format-agnostic DCN core
- generic execution inspection tools
- specialist adapters on top of the core
- PTDV/music as the first specialist adapter

If you are a user of this repo, the important question is simple:

- install it
- run it as an MCP server
- register it in your MCP-capable host
- use it

## What users get

When `dcn-mcp` is running, an MCP host can use tools such as:

- `core.connector_exists`
- `core.get_connector`
- `core.get_transformation`
- `core.get_condition`
- `core.transformation_exists`
- `core.condition_exists`
- `core.get_feed_page`
- `core.get_feed_stream_replay`
- `core.list_formats`
- `core.get_format`
- `core.get_account`
- `core.get_nonce`
- `core.create_connector`
- `core.create_transformation`
- `core.create_condition`
- `core.simulate_connector`
- `core.prepare_publication`
- `core.publish_entity`
- `core.confirm_publication`
- `core.execute_connector`
- `core.ensure_preflight`
- `core.build_parent_connector`
- `inspect.group_execution_tree`
- `inspect.summarize_execution`
- `music.extract_note_events`
- `music.summarize_note_events`
- `music.build_wrapper_connector`
- `music.build_player_payload`

It also exposes MCP resources such as:

- `core.dcn_core_primer`
- `music.ptdv_music_workflow`
- `music.register_maps`
- `music.score_position_schema_workflow`

## Drafts, publication and execution

`core.create_*` creates local drafts. `core.simulate_connector` previews them
without gas and returns `{particles, execution_mode: "simulation"}`.
`core.execute_connector` requires published entities and returns
`{block_number, block_hash, runner, particles, execution_mode: "chain"}`.
Pass the full chain result as `execution` to music/inspection tools to retain
provenance. To inspect or render a simulation, pass its `particles` array as
`samples`; this has no chain provenance.
Transformation and condition detail responses use `args_count`;
Solidity source is no longer part of runtime details.

Publication is explicit and owner-paid. First inspect `core.prepare_publication`,
then call `core.publish_entity` with `kind`, `name`, `max_fee_per_gas`,
`max_total_fee` (both limits in wei; total means gas limit times max fee), and a
unique `record_path` inside `DCN_ARTIFACT_ROOT`. `chain_id` defaults to Sepolia
(`11155111`). Dependencies must be published before their parents. No chain RPC
URL is required: the account signs locally and the server relays one transaction.
Publish serially for each owner and resolve pending transactions before preparing
the next entity: the registry publication nonce is shared by that owner. Separate
MCP sessions are not a safe way to parallelize one owner's publications.

The publication record is persisted before broadcast. On timeout or lost response,
reuse the same record to confirm the transaction; do not create another record to
retry sending. `core.confirm_publication` also checks an existing transaction by
name, content hash and transaction hash. `mined` is not finalized/indexed: a newly
mined connector may remain unavailable to chain execution until the safe block
advances. Retry execution without republishing or substituting simulation output.

## Quick Start

Preferred onboarding flow:

```bash
cd /path/to/dcn-mcp
make install
make smoke
make stdio
```

That gives users a one-command install path, a one-command verification path, and a one-command MCP server launch path.

If your target is Claude Desktop, build the installable bundle with:

```bash
make mcpb
```

That writes a `.mcpb` file into `dist/`.

Published GitHub releases also attach the built `.mcpb` artifact automatically.

If you want to activate the environment manually after install:

```bash
source .venv/bin/activate
```

## Install From Scratch

If someone cloned the repo and wants the shortest path:

```bash
git clone <repo-url>
cd dcn-mcp
make install
make smoke
make stdio
```

## Install In Codex

If your goal is to make `dcn-mcp` available to Codex, do this:

1. Install the repo-local environment:

```bash
cd /path/to/dcn-mcp
make install
make smoke
```

2. Add this to `~/.codex/config.toml`:

```toml
[mcp_servers.dcn]
command = "/path/to/dcn-mcp/.venv/bin/python"
args = ["-m", "dcn_mcp.server", "stdio"]

[mcp_servers.dcn.env]
PYTHONPATH = "/path/to/dcn-mcp/src"
API_BASE = "https://api.decentralised.art/chain"
PRIVATE_KEY = "<optional>"
DCN_TIMEOUT = "15"
DCN_ARTIFACT_ROOT = "/path/to/dcn-mcp/dcn-mcp-artifacts"
```

Notes:
- replace `/path/to/dcn-mcp` with the real absolute path where you cloned this repo
- if you want live authenticated DCN actions, set `PRIVATE_KEY`
- if you only want read/inspection operations, you can leave `PRIVATE_KEY` empty or omit it

3. Restart Codex or start a fresh Codex session.

4. Verify that Codex sees the server:

```bash
codex mcp list
```

5. In the new session, ask Codex to use it explicitly. For example:

- `Use the DCN MCP to list formats`
- `Use the DCN MCP to read core.dcn_core_primer`

Important:
- a newly registered MCP server usually will not appear inside an already-running session
- the reliable path is: add config, restart Codex, open a new session

## MCP Host Configuration

The safest way to register `dcn-mcp` in any MCP host is to point the host at the project-local venv Python.

Command:

```bash
/path/to/dcn-mcp/.venv/bin/python
```

Args:

```bash
-m dcn_mcp.server stdio
```

Working directory:

```bash
/path/to/dcn-mcp
```

Environment:

```bash
PYTHONPATH=/path/to/dcn-mcp/src
API_BASE=https://api.decentralised.art/chain
PRIVATE_KEY=<your-private-key-if-you-want-authenticated-live-DCN-actions>
DCN_TIMEOUT=15
DCN_ARTIFACT_ROOT=/path/to/dcn-mcp/dcn-mcp-artifacts
```

## Example MCP Config Snippet

Use this as a generic starting point for an MCP-capable host that accepts JSON server definitions:

```json
{
  "dcn-mcp": {
    "command": "/path/to/dcn-mcp/.venv/bin/python",
    "args": ["-m", "dcn_mcp.server", "stdio"],
    "cwd": "/path/to/dcn-mcp",
    "env": {
      "PYTHONPATH": "/path/to/dcn-mcp/src",
      "API_BASE": "https://api.decentralised.art/chain",
      "PRIVATE_KEY": "<optional>",
      "DCN_TIMEOUT": "15",
      "DCN_ARTIFACT_ROOT": "/path/to/dcn-mcp/dcn-mcp-artifacts"
    }
  }
}
```

If your host supports MCP registration but uses a different config format, keep the same values and translate only the wrapper syntax.

After you register the server in any MCP host, restart that host or start a fresh session before testing tool access.

## Host-Specific MCP Config Examples

These are the concrete MCP clients I expect most people to use first:

- Codex
- VS Code
- Cursor
- Claude Code
- MCP Inspector

Replace `/path/to/dcn-mcp` below with the directory where you cloned this repo.

### Codex CLI / Codex app

OpenAI documents Codex MCP configuration in `~/.codex/config.toml`. For `dcn-mcp`, add:

```toml
[mcp_servers.dcn]
command = "/path/to/dcn-mcp/.venv/bin/python"
args = ["-m", "dcn_mcp.server", "stdio"]

[mcp_servers.dcn.env]
PYTHONPATH = "/path/to/dcn-mcp/src"
API_BASE = "https://api.decentralised.art/chain"
PRIVATE_KEY = "<optional>"
DCN_TIMEOUT = "15"
DCN_ARTIFACT_ROOT = "/path/to/dcn-mcp/dcn-mcp-artifacts"
```

Codex CLI and the Codex app share this configuration.

### VS Code MCP config

VS Code reads either workspace `.vscode/mcp.json` or user-profile MCP configuration. A workspace config for `dcn-mcp` looks like:

```json
{
  "servers": {
    "dcn": {
      "type": "stdio",
      "command": "/path/to/dcn-mcp/.venv/bin/python",
      "args": ["-m", "dcn_mcp.server", "stdio"],
      "env": {
        "PYTHONPATH": "/path/to/dcn-mcp/src",
        "API_BASE": "https://api.decentralised.art/chain",
        "PRIVATE_KEY": "<optional>",
        "DCN_TIMEOUT": "15",
        "DCN_ARTIFACT_ROOT": "/path/to/dcn-mcp/dcn-mcp-artifacts"
      }
    }
  }
}
```

### Cursor

Cursor supports project `.cursor/mcp.json` and global `~/.cursor/mcp.json`. For a stdio server, the official docs require `type: "stdio"`. Use:

```json
{
  "mcpServers": {
    "dcn": {
      "type": "stdio",
      "command": "/path/to/dcn-mcp/.venv/bin/python",
      "args": ["-m", "dcn_mcp.server", "stdio"],
      "env": {
        "PYTHONPATH": "/path/to/dcn-mcp/src",
        "API_BASE": "https://api.decentralised.art/chain",
        "PRIVATE_KEY": "<optional>",
        "DCN_TIMEOUT": "15",
        "DCN_ARTIFACT_ROOT": "/path/to/dcn-mcp/dcn-mcp-artifacts"
      }
    }
  }
}
```

### Claude Code

Claude Code supports project-scoped `.mcp.json` files and a `claude mcp add` workflow. If you want a checked-in project config, create `.mcp.json` at the repo root:

```json
{
  "mcpServers": {
    "dcn": {
      "command": "/path/to/dcn-mcp/.venv/bin/python",
      "args": ["-m", "dcn_mcp.server", "stdio"],
      "env": {
        "PYTHONPATH": "/path/to/dcn-mcp/src",
        "API_BASE": "https://api.decentralised.art/chain",
        "PRIVATE_KEY": "<optional>",
        "DCN_TIMEOUT": "15",
        "DCN_ARTIFACT_ROOT": "/path/to/dcn-mcp/dcn-mcp-artifacts"
      }
    }
  }
}
```

CLI alternative:

```bash
claude mcp add --transport stdio --scope project \
  --env PYTHONPATH=/path/to/dcn-mcp/src \
  --env API_BASE=https://api.decentralised.art/chain \
  --env DCN_TIMEOUT=15 \
  --env DCN_ARTIFACT_ROOT=/path/to/dcn-mcp/dcn-mcp-artifacts \
  dcn -- /path/to/dcn-mcp/.venv/bin/python -m dcn_mcp.server stdio
```

### Claude Desktop

Claude Desktop now supports local MCP extensions as MCP Bundles (`.mcpb`). This repo includes a direct bundle path.

Build the bundle:

```bash
cd /path/to/dcn-mcp
make install
make mcpb
```

That produces a file like:

```bash
dist/dcn-mcp-<version>.mcpb
```

The same bundle is also uploaded automatically to the corresponding GitHub release asset when a release is published.

Install it in Claude Desktop using any of these:

1. double-click the `.mcpb` file
2. drag the `.mcpb` file into Claude Desktop
3. use `Developer -> Extensions -> Install Extension`

After installation, Claude Desktop will prompt for the bundle's user config:

- `api_base`
- `private_key`
- `dcn_timeout`

Implementation notes:
- the bundle is built as a `manifest_version: "0.4"` MCPB
- it uses the `uv` runtime path instead of bundling a whole Python virtual environment
- this keeps the artifact small and avoids the portability problems of shipping Python site-packages directly

### MCP Inspector

The official MCP Inspector docs show launching a local Python server through a command runner. For this repo, a direct invocation looks like:

```bash
npx @modelcontextprotocol/inspector \
  /path/to/dcn-mcp/.venv/bin/python \
  -m dcn_mcp.server stdio
```

If you want the server to inherit the repo-local environment cleanly, run it with:

```bash
PYTHONPATH=/path/to/dcn-mcp/src \
API_BASE=https://api.decentralised.art/chain \
DCN_TIMEOUT=15 \
DCN_ARTIFACT_ROOT=/path/to/dcn-mcp/dcn-mcp-artifacts \
npx @modelcontextprotocol/inspector \
  /path/to/dcn-mcp/.venv/bin/python \
  -m dcn_mcp.server stdio
```

## Environment Variables

These are the main runtime settings:

- `API_BASE`
  - default: `https://api.decentralised.art/chain`
- `PRIVATE_KEY`
  - optional for read-only inspection
  - required for authenticated draft creation, simulation, publication and chain execution
  - signs the chain API nonce flow (`GET /chain/nonce/{address}` then `POST /chain/auth`)
  - this chain token is separate from the app/services SIWE session used by `hypermusic-backend`
- `DCN_TIMEOUT`
  - request timeout in seconds
- `DCN_ARTIFACT_ROOT`
  - directory where artifact-writing tools are allowed to create files
  - default: `dcn-mcp-artifacts`

## Verify That It Actually Works

There are three levels of verification.

### A. Unit and transport tests

```bash
cd /path/to/dcn-mcp
source .venv/bin/activate
python -m unittest discover -s tests -v
```

Important test coverage includes:

- registry and schema validation
- resource exposure
- fake-client integration for core tools
- real MCP stdio lifecycle smoke test

### B. Local CLI inspection

```bash
cd /path/to/dcn-mcp
source .venv/bin/activate
python -m dcn_mcp.server list-tools
python -m dcn_mcp.server list-resources
python -m dcn_mcp.server invoke core.build_parent_connector '{"name":"piece","child_names":["a","b"]}'
```

### C. Real MCP host integration

Register the server in your MCP host and confirm that the host can:

- list tools
- list resources
- read `core.dcn_core_primer`
- call `core.build_parent_connector`

## Make Targets

The preferred user interface is now `make`:

### `make install`

Creates or updates `.venv` and installs `dcn-mcp` in editable mode.

### `make smoke`

Runs the repo smoke test.

### `make test`

Runs the full test suite.

### `make stdio`

Runs the real MCP stdio server from the local environment.

### `make mcpb`

Builds a Claude Desktop `.mcpb` bundle in `dist/`.

### `make list-tools`

Lists local tool metadata.

### `make list-resources`

Lists local resource metadata.

### `make list-adapters`

Lists registered adapters.

### `make read-core-primer`

Reads the core primer resource.

### `make invoke-example`

Runs one sample tool invocation locally.

## Helper Scripts

These still exist underneath the Makefile:

### `./scripts/bootstrap_venv.sh`

Creates `.venv`, upgrades `pip`, and installs `dcn-mcp` in editable mode.

### `./scripts/run_stdio.sh`

Runs the real MCP stdio server from the local environment.

### `./scripts/build_mcpb.sh`

Builds a Claude Desktop `.mcpb` bundle in `dist/`.

### `./scripts/smoke_test.sh`

Runs the repo test suite and a couple of local inspection checks.

## CLI Commands

Run as a real MCP stdio server:

```bash
python -m dcn_mcp.server stdio
```

List tools:

```bash
python -m dcn_mcp.server list-tools
```

List adapters:

```bash
python -m dcn_mcp.server list-adapters
```

List resources:

```bash
python -m dcn_mcp.server list-resources
```

Read a resource:

```bash
python -m dcn_mcp.server read-resource core.dcn_core_primer
```

Invoke a tool:

```bash
python -m dcn_mcp.server invoke core.connector_exists '{"name":"pitch"}'
```

Tool invocation returns a structured envelope:

```json
{"ok": true, "data": {...}}
```

or

```json
{ "ok": false, "error": { "code": "validation_error", "message": "..." } }
```

## Architecture

`dcn-mcp` is split into three layers.

### 1. `core`

- format-agnostic DCN operations
- create drafts, simulate, publish, fetch, execute, inspect, naming, artifacts
- no music assumptions

### 2. `adapters`

- format-family semantics
- PTDV/music is the first specialist adapter
- more adapters can be added later for other formats or multi-format workflows

### 3. `tools`

- transport-independent tool definitions and schemas
- these are the capabilities the MCP transport exposes

## Architecture Boundary

- `core.*` tools are general DCN operations.
- `inspect.*` tools are generic execution-tree inspection.
- `music.*` tools come from the PTDV/music adapter.
- resources expose compositional and protocol knowledge without baking it into the core runtime.
- generic structural helpers such as parent connector building belong in `core`, not in format-specific adapters.

## Pagination

The MCP transport supports paginated:

- `tools/list`
- `resources/list`

Pagination is implemented with opaque numeric cursors managed by the server.

## Notes For Maintainers

- Use the project-local `.venv` for `dcn-mcp` work.
- Do not rely on the shared interpreter for long-term use.
- The current server uses the official MCP Python SDK low-level server so that exact JSON Schemas stay under our control.
