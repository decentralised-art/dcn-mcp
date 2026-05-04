# Studio Score Templates Workflow

Studio templates are local editable draft arrangements of ordinary deployed connector archetypes. They are not special connector types, and the template arrangement itself is not on chain until the user deploys the edited graph.

Templates solve a practical composition problem: an immutable deployed connector cannot be edited in place, but a composer often wants to begin from a meaningful score structure and then insert shaping logic inside it. A template inserts the relevant on-chain archetype connectors into Studio and wires them together as a draft, so the user can disconnect, reconnect, duplicate, insert intermediate connectors, add transformations or conditions, and then deploy the resulting piece-specific connector.

## Current Score Template Archetypes

The Music Score plugin uses layered deployed collector archetypes:

- `score_full_v2`: semantic slots `score_parts_v2`, `score_meter_v2`, `score_clefs_v2`, `score_tempo_v2`, `score_key_v2`, `score_notes_v1`, `score_articulations_v1`, and `score_slurs_v1`
- `score_notes_v1`: semantic slots `score_event_id`, `score_onset`, `score_duration`, `score_pitch`, `score_dynamic_code`, `score_part`, `score_staff`, and `score_voice`
- `score_meter_v2`: semantic slots `score_meter_time_tick`, `score_beats`, and `score_beat_type`
- `score_parts_v2`: semantic slots `score_part` and `score_staff_count`
- `score_clefs_v2`: semantic slots `score_clef_time_tick`, `score_part`, `score_staff`, `score_clef_sign_code`, and `score_clef_line`
- `score_tempo_v2`: semantic slots `score_tempo_time_tick` and `score_tempo_bpm`
- `score_key_v2`: semantic slots `score_key_time_tick`, `score_key_fifths`, `score_key_mode_code`, and `score_part`
- `score_articulations_v1`: semantic slots `score_event_id`, `score_articulation_code`, and `score_placement`
- `score_slurs_v1`: semantic slots `score_event_id`, `score_slur_number`, `score_slur_type`, and `score_placement`

The slot connectors are deployed on chain as normal connectors. The collector connectors are also deployed on chain with their semantic slot composites and `add(1)` pass-through transformations. The local template is the editable arrangement that inserts the collector and its slot connectors into Studio.

Semantic pass-through slot connectors canonically use the `add` transformation with argument `1`.

## What Templates Enable

Templates let the user compose as trees within trees:

- keep stable terminal slot names for plugin interpretation, such as `score_onset`, `score_duration`, `score_pitch`, or `score_dynamic_code`
- insert other connectors between a terminal slot and the collector to shape the values, for example scales above `score_pitch` or phrase-level logic above `score_dynamic_code`
- duplicate semantic groups, such as multiple notes collectors, to build layers or voices
- combine explicit parts, meter, clefs, tempo, key, notes, articulations, slurs, and later score substructures in one larger draft
- use transformations and optional conditions to shape the final numeric streams before the Music Score plugin renders MusicXML

For score-template rendering, `score_` prefixed slot names map to their semantic fields. Inside `score_notes_v1`, `score_onset` and `score_duration` are interpreted as global tick coordinates with `2520` ticks per quarter note. The user composes in global time; the plugin derives MusicXML measures from the separate `score_meter_v2` layer.

The Music Score plugin groups shaped note slots by their nearest `score_notes_v1` collector, so a user can insert a scale, phrase, or other shaping connector between `score_notes_v1` and `score_pitch` without losing the note-row context. `score_meter_v2`, `score_parts_v2`, `score_clefs_v2`, `score_tempo_v2`, and `score_key_v2` are score-level layers, not note fields. `score_articulations_v1` and `score_slurs_v1` attach to notes by matching `score_event_id`. Current articulation codes include `0=accent`, `1=staccato`, `2=tenuto`, and `3=strong-accent`; current slur type codes follow MusicXML enum values `1=start`, `2=stop`, and `3=continue`; placement uses `6=above` and `7=below`. `score_clef_sign_code` supports `0=G`, `1=F`, `2=C`, and `3=percussion`; `score_key_mode_code` supports `0=major`, `1=minor`, `2=none`, and modal labels through `9=locrian`.

## Agent Guidance

When assisting a user:

- Treat templates as editable draft arrangements, not as deployed composite connectors.
- Treat template connector nodes as ordinary on-chain connectors once inserted into Studio.
- Do not describe missing template archetypes as a normal product state; missing archetypes are a chain/data setup issue.
- Suggest the full score template when the user wants a serious composition scaffold, and suggest layer templates when they only want to add or reshape one layer.
- Encourage users to insert shaping connectors between semantic slots and collectors instead of editing deployed archetypes directly.
- Do not describe meter, parts, clef, tempo, or key as conceptually optional for full-score composition. If the plugin renders without one of those layers, treat that as a preview fallback or incomplete draft state.
- Use explicit deployed names when discussing the current score templates: `score_full_v2`, `score_notes_v1`, `score_meter_v2`, `score_parts_v2`, `score_clefs_v2`, `score_tempo_v2`, `score_key_v2`, `score_articulations_v1`, and `score_slurs_v1`.
