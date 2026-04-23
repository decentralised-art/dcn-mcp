# DCN Core Primer

DCN core concepts are format-agnostic:
- formats define available feature spaces
- connectors define reusable transformation graphs
- dimensions reference composites and transformation chains
- RI freezes or shifts realizations at execution time
- execution returns sample trees, not application-level semantics

The core layer should never assume a specific interpretation such as MIDI, notes, images, or motion.
