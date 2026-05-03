# Studio Score Templates Workflow

Studio templates are local editable draft arrangements of ordinary deployed connector archetypes. They are not special connector types, and the template arrangement itself is not on chain until the user deploys the edited graph.

Templates solve a practical composition problem: an immutable deployed connector cannot be edited in place, but a composer often wants to begin from a meaningful score structure and then insert shaping logic inside it. A template inserts the relevant on-chain archetype connectors into Studio and wires them together as a draft, so the user can disconnect, reconnect, duplicate, insert intermediate connectors, add transformations or conditions, and then deploy the resulting piece-specific connector.

## Current Score Template Archetypes

The Music Score plugin currently uses these deployed collector archetypes:

- `score_notes_v1`: semantic slots `score_event_id`, `score_measure`, `score_onset`, `score_duration`, `score_pitch`, `score_dynamic_code`, `score_part`, `score_staff`, and `score_voice`
- `score_articulations_v1`: semantic slots `score_event_id`, `score_articulation_code`, and `score_placement`
- `score_slurs_v1`: semantic slots `score_event_id`, `score_slur_number`, `score_slur_type`, and `score_placement`

The slot connectors are deployed on chain as normal connectors. The collector connectors are also deployed on chain, but with open dimensions. The local template is the editable arrangement that connects the collector to its slot connectors.

## What Templates Enable

Templates let the user compose as trees within trees:

- keep stable terminal slot names for plugin interpretation, such as `score_pitch` or `score_dynamic_code`
- insert other connectors between a terminal slot and the collector to shape the values, for example scales above `score_pitch` or phrase-level logic above `score_dynamic_code`
- duplicate semantic groups, such as multiple notes collectors, to build layers or voices
- combine notes, articulations, slurs, and later score substructures in one larger draft
- use transformations and optional conditions to shape the final numeric streams before the Music Score plugin renders MusicXML

For measured-note score rendering, `score_` prefixed slot names map to their semantic fields. For example, `score_measure`, `score_onset`, `score_duration`, `score_pitch`, `score_dynamic_code`, `score_part`, `score_staff`, and `score_voice` are interpreted as score note fields by the plugin.

The Music Score plugin groups shaped note slots by their nearest `score_notes_v1` collector, so a user can insert a scale, phrase, or other shaping connector between `score_notes_v1` and `score_pitch` without losing the note-row context. `score_articulations_v1` and `score_slurs_v1` attach to notes by matching `score_event_id`. Current articulation codes include `0=accent`, `1=staccato`, `2=tenuto`, and `3=strong-accent`; current slur type codes follow MusicXML enum values `1=start`, `2=stop`, and `3=continue`; placement uses `6=above` and `7=below`.

## Agent Guidance

When assisting a user:

- Treat templates as editable draft arrangements, not as deployed composite connectors.
- Treat template connector nodes as ordinary on-chain connectors once inserted into Studio.
- Do not describe missing template archetypes as a normal product state; missing archetypes are a chain/data setup issue.
- Suggest score templates when the user wants to compose toward the Music Score plugin before they have a complete connector tree.
- Encourage users to insert shaping connectors between semantic slots and collectors instead of editing deployed archetypes directly.
- Use explicit deployed names when discussing the current score templates: `score_notes_v1`, `score_articulations_v1`, and `score_slurs_v1`.
