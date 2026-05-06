# Music Score Position Schema Workflow

The Studio Music Score workflow no longer uses local templates. Do not tell users
to open a Templates tab, insert a score template, depend on hidden template
defaults, or build scores from terminal `score_onset` / `score_pitch` connector
semantics. The visible Studio flow is the deploy source of truth.

The Music Score plugin uses a positional score schema. Meaning comes from the
dimension position of a connector occurrence in the score tree. Connector names
under field slots are value-generator names only.

## Root Layers

A score root connector exposes these layer positions:

- D1 Notes
- D2 Parts
- D3 Meter
- D4 Clefs
- D5 Tempo
- D6 Key
- D7 Articulations
- D8 Slurs / spanners
- D9 Directions / text, future
- D10 Barlines / repeats, future
- D11 Settings
- D12 Raw MusicXML tree

The Notes layer is required for notation. Parts, meter, clefs, tempo, and key
may be omitted while drafting; the frontend renderer uses preview defaults where
possible.

## Notes Layer

The Notes layer connects to one note table or to a note set containing multiple
note tables. Every connected dimension of a note set is interpreted as another
note table.

A note table maps its dimensions as:

- D1 `onset_tick`, required
- D2 `duration_tick`, required
- D3 `pitch`, required for pitched notes
- D4 `event_id`, optional, defaults to row index
- D5 `part`, optional
- D6 `staff`, optional
- D7 `voice`, optional
- D8 `dynamic_code`, optional
- D9-D12 future note fields

`onset_tick` and `duration_tick` are global score ticks. The current frontend
score adapter uses `2520` ticks per quarter note.

Minimal note-table example:

```text
SCORE_ROOT
+-- D1 Notes -> NOTE_TABLE
    +-- D1 onset_tick    -> score_quarter_note_tick_grid
    +-- D2 duration_tick -> constant_value
    +-- D3 pitch         -> major_scale_steps
```

## Optional Layers

Use these positional tables for common optional score layers:

- Parts: D1 `part`, D2 `staff_count`
- Meter: D1 `time_tick`, D2 `beats`, D3 `beat_type`
- Clefs: D1 `time_tick`, D2 `part`, D3 `staff`, D4 `clef_sign_code`, D5 `clef_line`
- Tempo: D1 `time_tick`, D2 `bpm`
- Key: D1 `time_tick`, D2 `fifths`, D3 `mode_code`, D4 `part`
- Articulations: D1 `event_id`, D2 `articulation_code`, D3 `placement`
- Slurs: D1 `event_id`, D2 `number`, D3 `type_code`, D4 `placement`

Current code values include:

- articulation code: `0=accent`, `1=staccato`, `2=tenuto`, `3=strong-accent`
- clef sign code: `0=G`, `1=F`, `2=C`, `3=percussion`
- key mode code: `0=major`, `1=minor`, `2=none`
- placement in the frontend score adapter: `0=above`, `1=below`

## Reusable Shapers

Prefer protocol-native connector and transformation patterns over invented
single-purpose transformations. A dimension emits the current running-instance
value first, then applies transformations cyclically.

Useful reusable shapers:

- `constant_value`: set RI start to the desired value and use `add(0)`.
  Reuse it for durations, parts, staff counts, dynamics, key values, tempo
  values, and other constants.
- `counter`: set RI start to the first identity value and use `add(1)`.
- `score_quarter_note_tick_grid`: set RI start to the first onset tick and use
  `add(2520)`.
- `major_scale_steps`: leave the reusable connector open and use cyclic
  transformations `add(2)`, `add(2)`, `add(1)`, `add(2)`, `add(2)`, `add(2)`,
  `add(1)`. The usage RI start chooses the tonic, for example `60` for C major,
  `62` for D major, or `65` for F major.

Do not describe `major_scale_steps` as a fixed C-major connector unless a wrapper
intentionally fixes RI start to `60`.

## Running Instances and Deploy

Existing on-chain connectors should remain references. Do not create renamed
copies such as `piece_constant_value_2` just because the same reusable connector
appears more than once or needs different values in different fields.

Per-use RI values belong to the authored root context:

- A reused connector occurrence with static mode becomes an entry in the new
  root connector's `static_ri` map.
- `static_ri` keys are DFS RI positions in that root context.
- A binding is not an edit to the reused connector. It replaces an open slot of
  a composite occurrence in the root context.
- `/execute` should send only `dynamic_ri` values for positions that are not
  locked by deployed `static_ri`.

If all children and shapers already exist on chain, the normal deployment should
publish only the new root or piece connector. The reused connectors remain
referenced by name, while usage-specific values live in the root's `static_ri`.

## Agent Guidance

When giving concrete Music Score instructions:

- Name the exact parent connector and dimension, for example `SCORE_ROOT D1` or
  `NOTE_TABLE D2`.
- Name the child connector to attach under that slot.
- State RI mode, RI start, RI shift, and transformation sequence where relevant.
- Prefer the position schema over legacy terminal score-field connectors.
- Do not say "insert a template"; users now build or edit ordinary Studio
  connector flows directly.
- Do not infer hidden score layers during deployment. Deleted or omitted nodes
  in the visible graph must stay deleted or omitted.
