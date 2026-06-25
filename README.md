# The Broke Dev's Guide: Agents & Plugins in Claude Code
*Maximum efficiency. Minimum spend. Zero apologies.*

**Author:** Félix Sotelo · **Version:** v5.5 · Production-validated · 2026-06-24

---

> A battle-tested guide to building multi-agent systems in Claude Code without burning your budget.
> Skills, hooks, agents, plugins, learnings, scope, and the complete global context layer — all validated against official documentation.

> **Language:** The full guide is in Spanish: [`guia-agentes-plugins-claude-code.md`](guia-agentes-plugins-claude-code.md).
> Translate on demand with Claude or DeepL as needed.

---

## Where to Start

**First time?** Read in this order:
1. **§4** — The restaurant analogy (5 min mental model)
2. **§1** — What to build and when
3. **§2** — Token budget
4. **§12** — Critical errors (first table only)

**Building something specific?**

| I want to... | Section |
|---|---|
| Create an agent | §5 — Agents |
| Create a skill | §6 — Skills (types, lifecycle, `context:fork`) |
| Create a hook | §7 — Hooks (10 events, 5 permission modes, secret guard, complexity routing) |
| Build a distributable plugin | §11 — Plugin |
| Design multi-agent architecture | §10 — Multi-agent |
| Choose the right model | §25 — Model selection + `effort` |
| Preview before executing | §17 + §28 — `/plan` |
| Use prompt shortcuts | §28 — Prompt Library |
| Build my own global context | §29 — Global context system |
| Auto-inject guide context per session | §26 — Global context hook |
| Schedule cloud agents | §30 — Cloud Agents (CCR) |
| Know when to stop optimizing | §23 — Real token ceilings |
| Validate what I built | §13 — Quality checklist |
| Avoid the most expensive mistakes | §12 — Common errors |

---

## What's New in v5.5

> *§3 got a triage desk (quick/ref split). §20 learned to hire Claude as a contractor, not just test the office. The rest filled in the missing instruments from last round.*

| Area | Change |
|---|---|
| **§3** | quick/ref split — estimation tables up front, godot benchmarks and detailed caching examples in ref |
| **§20** | Claude-in-CI: `--print` + `--dangerously-skip-permissions` patterns, `@claude` comment trigger, cost-per-trigger table with model guidance |

<details>
<summary>v5.4 changes</summary>

> *Five new instruments in the orchestra: a cost meter (caching), a smarter conductor (model routing), a sous-chef reviewer (Advisor), isolated practice rooms (worktrees), and a safety net before the stage collapses (auto-compaction).*

| Area | Change |
|---|---|
| **§3** | Prompt Caching — 90% cost discount on repeated system prompts, TTL behavior, cache read vs creation, design rules |
| **§25** | Full effort scale (`xlow`→`ultra`), Fable 5 as default alias, Fast Mode toggle, Extended Context 1M cost/benefit framework |
| **§31 NEW** | Advisor Pattern — haiku reviewing sonnet output at ~1.15× cost vs ~5× for Opus upgrade |
| **§10** | Worktrees — git-isolated parallel agents, `isolation: "worktree"` in Agent tool |
| **§27** | Auto-compaction behavior — what survives, what doesn't, how to prepare context before it happens |

</details>

<details>
<summary>v5.3 changes</summary>

> *§7 went from a "no entry" sign to a full keycard system: triage nurse at the door, metal detector on every file write, VIP list at the permission window.*

| Area | Change |
|---|---|
| **§7** | 5 permission modes — from read-only audit (`plan`) to full bypass (`bypassPermissions`), with when to use each |
| **§7** | Complexity routing hook — like a triage nurse: reads the prompt, assigns haiku/sonnet/opus before Claude even starts planning. 0 tokens if no match |
| **§7** | Secret detection guard — airport scanner for file writes: blocks API keys and credentials before they hit disk, skips `.env.example` and docs |
| **§7** | PermissionRequest hook — VIP list pattern: Read/Glob/Grep walk in without waiting; everything else goes through the filter |

</details>

<details>
<summary>v5.2 changes</summary>

| Area | Change |
|---|---|
| **§7** | 5 permission modes — from read-only audit (`plan`) to full bypass (`bypassPermissions`), with when to use each |
| **§7** | Complexity routing hook — like a triage nurse: reads the prompt, assigns haiku/sonnet/opus before Claude even starts planning. 0 tokens if no match |
| **§7** | Secret detection guard — airport scanner for file writes: blocks API keys and credentials before they hit disk, skips `.env.example` and docs |
| **§7** | PermissionRequest hook — VIP list pattern: Read/Glob/Grep walk in without waiting; everything else goes through the filter |

<details>
<summary>v5.2 changes</summary>

| Area | Change |
|---|---|
| **§30 NEW** | Cloud Agents (CCR) — `/schedule`, `/web-setup`, self-contained prompts, cron reference |
| **§26** | Two-tier keyword detection for plugin-level `UserPromptSubmit` hooks (domain symbols + proximity) |
| **§14** | New anti-pattern: agent with `## Catalog` sections storing full API shapes |
| **§10** | Lead delegation checkpoint — state lives in conversation, not filesystem |

</details>

<details>
<summary>v5.0 changes</summary>

| Area | Change |
|---|---|
| **§6 Skills** | Full 17-field frontmatter, skill lifecycle, `context:fork`, supporting files, `ultrathink` |
| **§7 Hooks** | 10 events (was 4), `updatedInput`, npm security guard (supply chain + slopsquatting) |
| **§25 Model** | `effort` as Opus alternative (~5×), Opus decision framework, `security-auditor` example |
| **§28 NEW** | Prompt Library — 8 shortcuts with tags, 4 recipes, 4 Laws |
| **§29 NEW** | Global context system — build your own `~/.claude/` from scratch |
| **Docs** | 5 factual errors corrected vs official Claude Code documentation |

</details>

---

## Official Docs

[Agents](https://code.claude.com/docs/en/sub-agents) · [Skills](https://code.claude.com/docs/en/skills) · [Hooks](https://code.claude.com/docs/en/hooks-guide) · [Plugins](https://code.claude.com/docs/en/plugins) · [Agent Teams](https://code.claude.com/docs/en/agent-teams)

---

## Contributing

Open an [Issue](../../issues) to suggest something. If it fits the workflow, it gets incorporated. Thanks for reading.
