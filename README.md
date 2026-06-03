# The Broke Dev's Guide: Agents & Plugins in Claude Code
*Maximum efficiency. Minimum spend. Zero apologies.*

**Author:** Félix Sotelo · **Version:** v4.6 · Production-validated (2026-06-02)

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

---

## Official Docs

- [Agents](https://code.claude.com/docs/en/sub-agents) · [Skills](https://code.claude.com/docs/en/skills) · [Hooks](https://code.claude.com/docs/en/hooks-guide) · [Plugins](https://code.claude.com/docs/en/plugins) · [Agent Teams](https://code.claude.com/docs/en/agent-teams)

> **[2026-06-03]** 24. [The context contract — the human factor](#24-the-context-contract--the-human-factor)
25. [Correct model—single-decision table](#25-correct-model--single-decision-table)
<!-- §7-quick -->
<!-- §7-ref -->
Guide (when updating guia-agentes-plugins-claude-code.md)
□ §24 in the Index if added
□ No section exceeds 150 lines — if it exceeds: add <!-- §N-quick --> (rules) and <!-- §N-ref --> (code/examples)
□ New section has anchor <!-- §N --> and entry in Index
<!-- §18-quick -->
<!-- §18-ref -->
<!-- §25 -->
## 25. Correct model — single decision table
> haiku/sonnet/opus is mentioned in §2, §5, §12 and §22. This section is the only lookup necessary.
### Master table
| Task | Model | Reason |
|---|---|---|
| Checklist / validator / reviewer | **haiku** | Fixed input, binary output — no reasoning needed |
| Postmortem / curator / git | **haiku** | Structured task, predictable output |
| skill plan | **haiku** | Read only + fixed format |
| Implementer (≤3 files, known stack) | **sonnet** | You need reasoning, not extreme creativity |
| Lead / orchestrator | **sonnet** | Coordinates, does not implement |
| Debugger (multi-layer, async, runtime) | **sonnet** | Diagnosis requires average reasoning |
| Architect (new project, design decisions) | **sonnet** | Structure decisions, non-trivial |
| Massive refactor/deep research | **opus** | Only when sonnet fails or the error cost is very high |
| Implementer with context > 10k tokens | **opus** | Sonnet loses coherence in very long contexts |
**Rule of thumb:** Does Sonnet do it right? → do not use opus. Does Haiku do it right? → do not use sonnet.
### Anti-frequent patterns
| Error | Fix |
|---|---|
| Reviewer with sonnet | haiku — compare against fixed list |
| Opus for git/postmortem | haiku — structured task |
| Without `model:` in agent | Everyone uses the most expensive model available → always specify |
| Sonnet for triage/dispatch | haiku — simple decision about keywords |
### Checklist §25
```
□ Each agent has model: specified
□ Reviewer → haiku
□ git, postmortem, curator → haiku
□ skill plan → haiku
□ Opus only when there is evidence that sonnet fails
```
---
