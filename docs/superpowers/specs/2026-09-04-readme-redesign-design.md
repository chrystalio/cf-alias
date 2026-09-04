# README Redesign — Design

**Date:** 2026-09-04
**Status:** Approved

## Problem

The current README is 228 lines of dense prose. Multiple install paths are stacked; troubleshooting is a single script path; usage sections mix preambles and code. New users can't scan it in 30 seconds.

## Goal

Restructure for scannability, hierarchy, and detail-on-demand. Keep all existing information. Make the README feel hand-crafted, not templated.

## Approach

A single full rewrite of `README.md`. Use:

- Shields.io badges at the top
- Tables for the features list
- Code-fence groups with headers (`### ...`)
- FAQ-style troubleshooting accordion (no JS needed; use plain `---` separators and `**bold question:**` answers)
- One emoji max — keep the existing ⚡ in the title

## New Structure

```
1. Hero + badges
2. Features (table with text icons)
3. Prerequisites
4. Quick start (3 steps)
5. Installation (4 paths, each a code group)
6. Configuration
7. Usage (one section per subcommand)
8. TUI section
9. Troubleshooting (FAQ)
```

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `README.md` | rewrite | Single source of truth for user-facing docs |

No new files. No link references to other docs; keep README self-contained.

## Detailed Layout

### Hero (lines ~1-15)

```markdown
<div align="center">

# ⚡ cf-alias

**Cloudflare email aliases from your terminal. Your primary inbox deserves peace and zero newsletters.**

| License | Python | uv |
|---------|--------|-----|
| ![](https://img.shields.io/badge/license-MIT-blue) | ![](https://img.shields.io/badge/python-3.10%2B-blue) | ![](https://img.shields.io/badge/uv-tool-orange) |

</div>
```

> User wants rest of it aligned-left (no `<div>` below the hero), per README convention. The `<div align="center">` wraps only the hero block.

### Features (table)

| Goal | What `cf-alias` does |
|---|---|
| Create | `cf-alias create github` — one alias in seconds |
| Generate | `cf-alias create --generate` — random name when you don't care |
| List | All rules in one aligned table |
| Delete | Confirm before touching the API |
| Categorize | Local SQLite tags for grouping |
| TUI | Interactive arrow-key menu |

### Prerequisites

```
1. A domain with Cloudflare Email Routing enabled
2. A Cloudflare API token with Email Routing: Edit permission
3. Your zone ID (sidebar of Cloudflare dashboard)
4. Python 3.10+ (or uv for everything)
```

### Quick Start (3 commands)

```
git clone … && cd cf-alias
cp .env.example .env && $EDITOR .env
cf-alias create github
```

### Installation (4 paths, code groups)

Each path:
- 4-6 line code block
- one short sentence about when to use it

Paths:
1. uv tool (recommended)
2. pip install -e .
3. uv run (no install)
4. raw script (no install)

### Configuration

- Where `.env` is found (3 paths)
- One `.env` template inline
- One paragraph on how to fill

### Usage (one block per subcommand)

Each block:
- short intent sentence
- minimal example
- optional prose for non-obvious flags

Subcommands to cover:
- `create` (custom, --generate, --print-only, --category)
- `list`
- `delete` (with -y, --dry-run)
- `categorize` (set, clear)
- `tui`

### TUI

Short subsection: what it shows, navigation keys, link or note it uses `questionary` + `rich`.

### Troubleshooting (FAQ)

Format:
```
**Q: Stuck on a bug I already fixed locally?**
A: …

**Q: …**
```

Common Q/A pulled from current README's troubleshooting prose plus typical FAQ (env vars, missing token, duplicate alias).

## Error / Edge Handling

- No edge cases for a doc rewrite — content covers everything, nothing user-controlled changes.

## Verification

1. `wc -l README.md` is < 250 lines (target: ~180)
2. Lint: no emojis except ⚡
3. Manual visual scan: each section has clear hierarchy
4. All commands documented in `--help` are in the README
5. `cf-alias create --generate` examples match the actual CLI

## Non-Goals

- Translate to other languages
- Split out into multiple files
- Replace prose with diagrams (no Mermaid)
- Add a contributing section
- Add license section
- Add screenshots
