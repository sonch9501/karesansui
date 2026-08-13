# 枯山水 karesansui

**Your markdown notes, rendered as a zen rock garden.**

Point it at any folder of `.md` files. Each note becomes a stone. Each folder becomes a rock island in raked sand. Newer notes are darker ink; older ones weather and fade. The layout is deterministic — your garden always looks like *your* garden.

![demo](docs/demo.gif)

## Why

Every note-taking tool shows you a list. Lists are inventories. A garden is a *place* — you notice at a glance which parts of your life are dense with stones and which are empty sand. karesansui is not a note-taking app. It is a way of looking at the notes you already have.

- **Zero dependencies.** Python standard library only. No npm, no pip, no build step.
- **Local only.** Binds to 127.0.0.1. Your notes never leave your machine.
- **Read-only.** It never writes to your notes folder. Keep editing in whatever you use today.
- **Deterministic.** The garden layout is seeded by your folder path. Reload all you want — the stones stay where they belong.

## Quickstart

```bash
git clone https://github.com/YOURNAME/karesansui.git
cd karesansui
python3 server.py            # opens the bundled sample garden
python3 server.py ~/notes    # opens YOUR garden
```

That's it. Requires Python 3.8+, which your machine almost certainly has.

## How to read the garden

| element | meaning |
|---|---|
| rock island | a top-level folder (or frontmatter `category`) |
| stone | one markdown file |
| stone size | length of the note |
| ink darkness | recency — fresh notes are dark, old ones weathered |
| moss fleck | the note has tags |
| ripples | raked sand around each island |

**Hover** a stone for a preview. **Click** to read the full note in a side panel. **`/`** to search — non-matching stones sink into the sand. Click a category in the legend to isolate one island.

## Frontmatter (optional)

karesansui works on plain `.md` files with no metadata at all. If frontmatter exists, it uses it:

```yaml
---
date: 20260601        # or 2026-06-01; also parsed from filenames
category: journal     # overrides the folder name
tags: [morning, work]
---
```

## Philosophy

At Ryoan-ji in Kyoto there are fifteen stones, arranged so that from any seat you can only ever see fourteen. A journal is the same: you can never see all of yourself at once. But you can rake the sand.

## License

MIT
