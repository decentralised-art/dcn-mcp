# Boundary Definition

## Core

The core layer may know about:
- DCN transport
- authentication
- connectors
- transformations
- formats
- execution samples
- names
- generic artifact writing
- generic structural connector builders such as parent connectors

The core layer may not know about:
- music
- MIDI
- PTDV as note events
- piano ranges
- cadence or density heuristics

## Adapters

Adapters translate raw sample trees into domain semantics.

The first adapter is `ptdv_music`, which owns:
- note extraction from `pitch/time/duration/velocity`
- register classification
- wrapper helpers for PTDV/music workflows
- MIDI payload construction and export

## Specialist workflows

Reference apps such as `allagma` should compose on top of this boundary. They may depend on the PTDV/music adapter, but the MCP core must remain format-agnostic.
