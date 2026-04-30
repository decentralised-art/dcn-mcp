# DCN Core Primer

DCN core concepts are format-agnostic:
- formats define available feature spaces
- connectors define reusable transformation graphs
- transformations and conditions are first-class deployable chain entities
- dimensions reference composites and transformation chains
- RI freezes or shifts realizations at execution time
- execution returns sample trees, not application-level semantics
- the event feed is the canonical discovery/index layer for recently added or updated chain entities

Use exact entity endpoints when the caller already knows the name:
- `/connector/{name}`
- `/transformation/{name}`
- `/condition/{name}`

Use `/feed` and `/feed/stream` for discovery and incremental updates. Feed events tell you what changed and who owns it; detail endpoints provide the full deployable payload when the caller needs to inspect, execute, or compose with an entity.

The core layer should never assume a specific interpretation such as MIDI, notes, images, or motion.
