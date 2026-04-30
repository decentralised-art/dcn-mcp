# PTDV Music Workflow

PTDV composition interprets `pitch`, `time`, `duration`, and `velocity` as note-event fields.

Current MIDI scalar contract:
- `pitch`: MIDI note number, `0..127`
- `velocity`: MIDI velocity, `0..127`; zero is a valid silent note-on velocity
- `time`: beat position, starting at beat `0`
- `duration`: beat length, strictly greater than `0`

`durationv2` and `duration_v2` are accepted as aliases for `duration`.

Execution paths preserve connector lineage. Two sibling composites with the same connector name but different indexed path segments, such as `/cell:0/...` and `/cell:1/...`, must remain separate note groups. Do not collapse those paths by connector name when diagnosing which branch produced which notes.

Recommended workflow:
1. deploy reusable vocabulary connectors
2. preview actual executions
3. extract note events
4. measure realized register, density, timing, and duration profile
5. instantiate wrappers with static RI for a specific piece
6. group wrappers into sections
7. collect sections into a final parent
8. render MIDI from the most authoritative realized layer
