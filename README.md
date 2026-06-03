# The Broke Dev's Guide: Agents & Plugins in Claude Code
*Maximum efficiency. Minimum spend. Zero apologies.*

**Author:** Félix Sotelo · **Version:** v4.8 · Production-validated (2026-06-03)

---

A practical guide to building multi-agent systems in Claude Code without burning your budget.
Covers agents, skills, hooks, plugins, learnings, scope, multi-agent architecture, vector memory, and invocation efficiency.

> **Language note:** The full guide is written in Spanish — [`guia-agentes-plugins-claude-code.md`](guia-agentes-plugins-claude-code.md).
> It updates frequently with new production knowledge. Translate on demand with Claude or DeepL as needed.

---

## Where to Start

| I want to... | Section |
|---|---|
| Understand the system in 5 min | §4 — The restaurant analogy |
| Know what to build before building it | §1 — What to build and when |
| Control token costs | §2 — Token budget |
| Create an agent | §5 — Agents |
| Create a hook | §7 — Hooks |
| Build a distributable plugin | §11 — Distributable plugin |
| Design multi-agent architecture | §10 — Multi-agent architecture |
| Upgrade learnings to semantic search | §16 — Vector memory |
| See a plan before executing | §17 — Plan + Invocation templates |
| Know when to stop optimizing tokens | §23 — Real ceilings, formula, levers by impact |
| Avoid the most expensive mistakes | §12 — Common errors (first table) |
| Auto-inject guide context per session | §26 — Global context hook |

---

## Official Docs

- [Agents](https://code.claude.com/docs/en/sub-agents) · [Skills](https://code.claude.com/docs/en/skills) · [Hooks](https://code.claude.com/docs/en/hooks-guide) · [Plugins](https://code.claude.com/docs/en/plugins) · [Agent Teams](https://code.claude.com/docs/en/agent-teams)

> **[2026-06-03]** # ← Adjust with the path where you cloned this repo
GUIDE = Path("~/path/to/guide-agents-plugins-claude-code.md").expanduser()
"command": "python3 ~/.claude/hooks/guia_context.py"
