# The Broke Dev's Guide: Agents & Plugins in Claude Code
*Maximum efficiency. Minimum spend. Zero apologies.*

**Author:** Félix Sotelo · **Version:** v5.32 · §7 hooks + §6 skills re-verified against official docs (2026-09-02) — **33 events** (`DirectoryAdded` and `PreModelSwitch`/`PostModelSwitch` are new: the latter lets you block a model escalation with exit 2, the lowcost lever that was missing). **`continueOnBlock`**: without that flag a denied `PreToolUse`/`PostToolUse` **kills the turn** instead of returning the error to Claude — changed in v2.1.210. **`if` is valid on only 5 tool events; anywhere else it stops the hook from running, silently.** Fifth handler type `agent` (experimental), and prompt hooks run on Haiku = the Advisor Pattern, native. Hooks can be declared in **7 places**, including skill frontmatter (persists for the whole session) and subagent frontmatter. §6: `background: true` is the new default for `context: fork` (v2.1.218) — narrower tool set and **`/rewind` does not undo its edits**; **`skillOverrides` does NOT affect plugin skills** (a trap against the guide's own hub advice); personal > project precedence; commands merged into skills

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
| Use CLAUDE.local.md / output-styles / rules / settings.local.json | §32 — The undocumented files |
| Use native slash commands (`/rewind`, `/fork`, `/compact`...) with agents/hooks | §33 — Native commands |

---

## What's New in v5.15

> *Full audit of the guide against the live API and a real agent session. Cost ratios were stale (Opus 4.5+ dropped its price: it's now ~1.7× Sonnet per token, not 5×), fast mode is Opus-only, 1M context is standard pricing, and two claims about subagents no longer hold. Plus the templates the guide always assumed but never showed: both lead designs, a full multi-agent project tree, and a copy-ready minimal plugin. A new `tools/audit_guia.py` script now guards the guide's own plumbing (marker placement, quick sizes, KEYWORD_MAP sync, version sync).*

| Area | Change |
|---|---|
| **§3 §15 §25 §31** | Real pricing verified (Haiku $1/$5 · Sonnet 5 $3/$15 · Opus 4.8 $5/$25): sonnet = 3× haiku, opus = ~1.7× sonnet — the historical 5×/15× ratios removed |
| **§25** | `effort` scale corrected to `low\|medium\|high\|xhigh\|max` (no "ultra"/"xlow"); not supported on Haiku. Fast mode: Opus 4.8/4.7 only. 1M context is standard pricing — the ×10 "extended context" table was obsolete |
| **§10** | Templates for both lead designs (planner / orchestrator), full multi-agent project tree, end-to-end flow with per-agent budgets |
| **§11** | Copy-ready 5-file minimal plugin, plugin README template, release checklist, `commands/` added to the structure tree |
| **§12** | `subagent_type` now accepts project agents (verified live); the "built-ins only" list was wrong |
| **§10 §11 §13** | Subagents without restricted `tools:` DO have the Skill tool (verified live) — claim nuanced |
| **§13 §26** | New guardrails: quick blocks ≤ hook budget (80), markers never inside code fences, never renumber §N, one-home-per-concept; installed hook is the KEYWORD_MAP source of truth |
| **§19 §21** | Added to the context hook's KEYWORD_MAP — they were orphaned from injection |
| **tools/ NEW** | `audit_guia.py` — pre-commit audit that catches all of the above classes of drift |

<details>
<summary>v5.14 changes</summary>

| Area | Change |
|---|---|
| **§5** | Core+reference split pattern for agents that grow |
| **§22** | Real-world calibration of system-prompt budgets (they're aspirational, not gates) |

</details>

<details>
<summary>v5.13 changes</summary>

> *New §33 covers Claude Code's native slash commands (`/rewind`, `/clear`, `/compact`, `/fork`, `/branch`, `/goal`, `/batch`, `/loop`...) and — verified against the official docs, not assumed — which ones actually integrate with agents, skills, and hooks (`/fork` and `/branch` as native agent-spawning commands, the `PreCompact`/`SessionStart` hook integration points) versus which ones are CLI-only with no programmatic API (`/rewind`, `/clear`, `/compact`).*

| Area | Change |
|---|---|
| **§33 NEW** | Table of commands relevant to builders, with when-to-use for each |
| **§33 NEW** | What actually integrates with agents/skills/hooks: `/fork`, `/branch`, `PreCompact` hook, `SessionStart` matchers |
| **§33 NEW** | What's confirmed NOT possible: no hook event for `/rewind`, no SDK-level checkpoint API |

</details>

<details>
<summary>v5.12 changes</summary>

> *Sonnet's pinned model ID bumped to its current release. No structural changes.*

| Area | Change |
|---|---|
| **§25** | Pinned model ID `claude-sonnet-4-6` → `claude-sonnet-5` (complexity-routing hook example, Cloud Agents model table, alias/defaults table) |

</details>

<details>
<summary>v5.11 changes</summary>

> *No new content. The guide got faster to navigate and cleaner to read: physical section order now matches the Index grouping, examples work for any stack (not just Godot), and the context hook covers 4 more sections.*

| Area | Change |
|---|---|
| **Structure** | Physical section order reordered — §4→§1→§25→§2→§24 (Fundamentos), then Core, then Quality, then Advanced. §25 moved from position 25 → 3; §24 from 24 → 5 |
| **§3** | Godot-specific agent benchmark table (18 rows) → generic archetype table (8 rows: bash-heavy, read-heavy reviewer/debugger, write-heavy, postmortem, orchestrator, curator) |
| **§5** | Redundant model table removed — replaced with pointer to §25, which is now 2 sections earlier |
| **§2 §5 §17** | CLAUDE.md template, gotcha examples, and `/plan` example generalized — applies to any stack |
| **`guia_context.py`** | §12, §13, §22, §23 added to KEYWORD_MAP — context hook now covers 27/32 sections |

</details>

<details>
<summary>v5.10 changes</summary>

> *§27 got its architecture corrected. The context hook got a session deduplication layer and a tighter line budget.*

| Area | Change |
|---|---|
| **§27** | Handoff Protocol — architecture diagram corrected, Stop hook flow clarified |
| **§26** | `guia_context.py` — session deduplication via `/tmp/guia_seen_{sid}.json`; `LINES_BUDGET` 120 → 80 |

</details>

<details>
<summary>v5.9 changes</summary>

> *§32 maps the four files nobody talks about: CLAUDE.local.md (personal gitignored overrides), output-styles/ (response shape on tap, 30-50% output token savings), rules/ (glob-scoped domain rules with practical examples), and settings.local.json (personal permissions). Includes a plugin distribution table so you know what to ship and what to keep local.*

| Area | Change |
|---|---|
| **§32 NEW** | `CLAUDE.local.md` — personal gitignored override, wins over `CLAUDE.md` on conflict |
| **§32 NEW** | `output-styles/` — `terse.md` / `verbose.md` templates, 30-50% output token savings in code agents |
| **§32 NEW** | `rules/` — glob-scoped with `api.md` and `tests.md` practical examples, decision table vs `CLAUDE.md` |
| **§32 NEW** | `settings.local.json` — personal permissions, gitignored by design |
| **§32 NEW** | Plugin distribution table — what to ship (`rules/`, `output-styles/`, `settings.json`) vs what to keep local |

</details>

<details>
<summary>v5.8 changes</summary>

> *§6 now explains the two visibility axes (`disable-model-invocation` × `user-invocable`) as orthogonal flags, adds the 2×2 combination matrix, and introduces the "internal library" skill pattern with its template.*

| Area | Change |
|---|---|
| **§6** | Two-axis visibility model — `disable-model-invocation` vs `user-invocable` explained as independent flags, 2×2 matrix of the 4 combinations, new "Librería interna" template |

</details>

<details>
<summary>v5.7 changes</summary>

> *§3 got a triage desk (quick/ref split). §20 learned to hire Claude as a contractor, not just test the office. The rest filled in the missing instruments from last round.*

| Area | Change |
|---|---|
| **§3** | quick/ref split — estimation tables up front, godot benchmarks and detailed caching examples in ref |
| **§20** | Claude-in-CI: `--print` + `--dangerously-skip-permissions` patterns, `@claude` comment trigger, cost-per-trigger table with model guidance |

</details>

<details>
<summary>v5.5 changes</summary>

> *§3 got a triage desk (quick/ref split). §20 learned to hire Claude as a contractor, not just test the office.*

| Area | Change |
|---|---|
| **§3** | quick/ref split — estimation tables up front, godot benchmarks and detailed caching examples in ref |
| **§20** | Claude-in-CI: `--print` + `--dangerously-skip-permissions` patterns, `@claude` comment trigger, cost-per-trigger table with model guidance |

</details>

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
