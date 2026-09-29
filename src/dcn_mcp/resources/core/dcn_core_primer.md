# DCN Core Primer

DCN core concepts are format-agnostic:
- formats define available feature spaces
- connectors define reusable transformation graphs
- transformations and conditions are first-class deployable chain entities
- dimensions reference composites and transformation chains
- RI freezes or shifts realizations at execution time
- chain execution returns `{block_number, block_hash, runner, particles}`; the particle trees carry no application-level semantics
- the event feed is the canonical discovery/index layer for recently added or updated chain entities

Use exact entity endpoints when the caller already knows the name:
- `/connector/{name}`
- `/transformation/{name}`
- `/condition/{name}`

Use `/feed` and `/feed/stream` for discovery and incremental updates. Feed events describe indexed chain entities, not newly created local drafts. Transformation and condition detail endpoints provide `args_count`, `owner`, and `address`; use `args_count` to validate arguments. They do not return Solidity source. Connector details still expose the graph. Address `0x0` means a local draft.

The lifecycle has separate steps:

1. `core.create_connector`, `core.create_transformation`, and `core.create_condition` create server-local drafts. The legacy `core.deploy_*` names are deprecated aliases of these draft operations and spend no gas.
2. `core.simulate_connector` calls `/simulate` to preview a local draft, returning a particle array through `particles` (also `samples` for compatibility). It does not establish chain provenance.
3. `core.prepare_publication` inspects a relay preparation without signing. Publish dependencies first: transformations, conditions and child/bound connectors must exist in the target registry before their parent connector can be published.
4. `core.publish_entity` explicitly authorizes owner-paid publication, defaults to Sepolia chain id `11155111`, and requires `max_fee_per_gas`, `max_total_fee` (wei per transaction), and a unique persistent `record_path` beneath the configured artifact root. It validates the owner, chain, fees and zero-value type-2 transaction, signs locally, sends once, and polls confirmation. Reuse the same record to confirm a pending transaction without broadcasting another. A timeout or lost response is not permission to start a new publication; the record contains its hash.
5. A `mined` receipt is not finality or indexer readiness. `core.execute_connector` reads published state at the server's execution block. If it returns not found/unavailable after mining, wait for the safe block and retry execution; do not present a simulation as chain output or republish because of this delay.
6. Keep the entire chain envelope with the artwork. Inspection/music tools accept it as `execution` and preserve provenance.

The core layer should never assume a specific interpretation such as MIDI, notes, images, or motion.

Publish serially per owner. Resolve a pending publication before preparing the
next entity; the registry publication nonce belongs to the owner, not the entity.
Parallel calls from separate MCP sessions can conflict even with different record
paths.
