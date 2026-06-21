# Architecture

The skill has two layers.

1. **Deterministic baseline engine** in `src/materials_review_audit/`.
   This layer performs fast extraction, manifest checks, descriptor range checks, CSV output, and report generation.

2. **Multi-agent protocol** in `prompts/` and `AGENTS.md`.
   Codex/OpenClaw can use these instructions to run higher-level review while passing JSON files between agents.

The deterministic engine intentionally does not pretend to understand every scientific claim. Its role is to create reliable ledgers that an expert or agent can inspect.

## Token-saving design

Instead of sending the full manuscript to every agent:

- `draft_map.json` stores paragraph IDs, sections, and flags.
- `selected_context.json` stores only claim-bearing, number-bearing, descriptor-bearing, and figure-bearing paragraphs.
- `evidence_pack.json` stores figure manifest, source-data inventory, database path, and reference numbers.

Each agent reads only the packet relevant to its task.
