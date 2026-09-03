# The Broke Dev's Guide: Agents & Plugins in Claude Code
*Maximum efficiency. Minimum spend. Zero apologies.*

**Author:** Félix Sotelo · **Version:** v5.38 · §2 per-file limits re-verified against the official docs (2026-09-02) — the table now separates **what the harness enforces from what this guide recommends**: official CLAUDE.md guidance is <200 lines (with a hard skip past 4 MiB), official SKILL.md is <500; the <30 and <200 here are a lowcost stance, not a platform limit. **The hidden skill-listing budget**: Claude Code loads every skill's name and description under a budget that scales at 1% of the context window, and on overflow it **drops descriptions starting with the skills you invoke least* — a skill without its description stops being auto-invoked, with no error. Levers: `skillListingBudgetFraction`, `SLASH_COMMAND_TOOL_CHAR_BUDGET`, and `name-only` in `skillOverrides`. Fixed the description-cap setting name: it is **`skillListingMaxDescChars`**, not `maxSkillDescriptionChars` (§2 and §13)

---

> A battle-tested guide to building multi-agent systems in Claude Code without burning your budget.
> Skills, hooks, agents, plugins, learnings, scope, and the complete global context layer — all validated against official documentation.

> **Language:** The full guide is in Spanish, split across five files:
> [`guia-00-indice.md`](guia-00-indice.md) (index) · [`guia-01-fundamentos.md`](guia-01-fundamentos.md) · [`guia-02-construccion.md`](guia-02-construccion.md) · [`guia-03-calidad.md`](guia-03-calidad.md) · [`guia-04-avanzado.md`](guia-04-avanzado.md).
> [`README.es.md`](README.es.md) is the five concatenated into one page.

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
| Create a hook | §7 — Hooks (33 events, 5 handler types, 5 permission modes, secret guard) |
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

## What's New

<!-- changelog-insert -->

### v5.38 — per-file limits (2026-09-02)

| Area | Change |
|---|---|
| **§2** | The limits table now separates **platform limits from this guide's stance**. Official CLAUDE.md guidance is under 200 lines, with a hard skip past 4 MiB; official SKILL.md guidance is under 500 lines. The `<30` and `<200` here are deliberate lowcost choices, not platform ceilings — worth knowing which is which before treating one as a rule |
| **§2** | **The skill-listing budget, which degrades silently.** Claude Code loads every skill's name plus its description under a character budget that scales at 1% of the model's context window. On overflow it drops descriptions, starting with the skills you invoke least. A skill whose description got dropped stops matching — Claude knows it exists but not when to use it, and nothing reports this |
| **§2** | Levers for that budget: `skillListingBudgetFraction` (or `SLASH_COMMAND_TOOL_CHAR_BUDGET` for a fixed count), `name-only` in `skillOverrides` to free room, and trimming `description` + `when_to_use` at the source |
| **§2 §13** | The setting that configures the 1,536-character description cap is **`skillListingMaxDescChars`**. The guide named it `maxSkillDescriptionChars`, which does not exist |
| **§2** | Added the system-imposed limits the table was missing: `.claude/loop.md` truncates silently at 25,000 bytes, and `MEMORY.md` loads only its first 200 lines or 25 KB |

---

### v5.37 — observability (2026-09-02)

| Area | Change |
|---|---|
| **§21** | The section never mentioned the harness's own instrumentation. Added the "is it alive?" layer: `/hooks` (registered), `/context` → Memory files (loaded), `/tasks` (still running), `/usage`, `/doctor`, and the `InstructionsLoaded` hook |
| **§21** | For hooks, `claude --debug-file <path>` plus `tail -f` beats bare `--debug`, whose output interleaves with the session. It shows which hooks matched, their exit code, stdout and stderr. `/debug` enables it mid-session |
| **§21** | OpenTelemetry was dismissed as overkill. True for collectors and dashboards, not for `OTEL_METRICS_EXPORTER=console`, which needs no infrastructure — and its cost/token metrics are tagged by `query_source` (main/subagent/auxiliary), `agent.name`, `skill.name`, `model`, `speed`, `effort`. That is the breakdown §2, §3 and §25 estimate by hand |
| **§21** | New catalogue of **12 harness silent deaths** with a detection method for each, distilled from this round: `if` on a non-tool event, stdout that stops parsing as JSON, `additionalContext` at the top level, `glob:` instead of `paths:`, a green routine that did nothing, `usage.speed` on Opus 4.6, a cache that never hits, and more |

---

### v5.36 — the guide's own hook (2026-09-02)

| Area | Change |
|---|---|
| **§26** | The published recipe still pointed `GUIA` at `guia-agentes-plugins-claude-code.md` — the single file that stopped existing in the v5.16 split two months earlier. Copying it produced a hook aimed at a missing file, whose only symptom is stderr noise |
| **tools/** | The audit compared only `KEYWORD_MAP` and `CAP_CHARS`, which is why the stale path survived: the map was perfect and the recipe was broken. **New check 10** diffs the whole published block against the installed hook |
| **§26** | Only `UserPromptSubmit`, `UserPromptExpansion`, `SessionStart` and `PostModelSwitch` turn plain stdout into context. The `UserPromptSubmit` timeout is **30 s**, not the usual 10 minutes, and the event **supports no matcher** — filtering is the script's job |
| **§26** | `additionalContext` placed at the top level instead of inside `hookSpecificOutput` is **silently ignored**. And an `echo` in your shell profile prepends to hook stdout, so a JSON-returning hook stops parsing as JSON with nothing reported on exit 0 |
| **§7 §33** | `SessionStart` has a fifth `source` value: `fork` |

---

### v5.35 — CI and the rest of `.claude/` (2026-09-02)

| Area | Change |
|---|---|
| **§32** | The `.claude/rules/` frontmatter field is **`paths:`**, not `glob:` — and a rule without `paths:` **loads unconditionally, every session**. The previous example silently turned a context-saving file into one that always costs |
| **§32** | CLAUDE.md files are **concatenated**, root-down, not overridden — `.local` "winning" is just an effect of loading last. HTML comments are stripped before injection (free maintainer notes); a file over **4 MiB is skipped entirely**; `@path` imports organize but **save no tokens** |
| **§32** | Verifying what actually loaded: `/context` → Memory files, `/memory`, and the `InstructionsLoaded` hook. Root CLAUDE.md survives `/compact`; path-scoped rules only reload when a matching file is read |
| **§20** | The guide's review workflow passed `prompt`, which is **automation mode** — its review went to the workflow run log, not the PR. Posting to the PR needs `--comment` **and** `--allowedTools` in `claude_args`, even when the skill's own frontmatter already names the tool |
| **§20** | `id-token: write` is **required** by the action's default GitHub App authentication and was missing from the guide's workflows |
| **§20** | `CLAUDE_CODE_OAUTH_TOKEN` (from `claude setup-token`) bills CI runs **against your subscription** instead of the API — but an org-wide secret should stay an API key, since the OAuth token is tied to one person |
| **§20** | Actor checks that silently reject runs: write access on issue/PR events, and bot actors unless listed in `allowed_bots` — which catches scheduled runs attributed to a bot |

---

### v5.33 – v5.34 — plugins, multi-agent, scheduling and native commands (2026-09-02)

| Area | Change |
|---|---|
| **§10** | **`AskUserQuestion` is never available in a subagent** — an agent told to "ask the user when unsure" will guess instead. Every human decision has to be resolved before dispatch or returned as output |
| **§10** | `isolation: worktree` branches from the **default branch, not the parent's HEAD** — a dispatched agent does not see your unmerged commits. Fan-out limits: depth 3, 20 concurrent, warning past 15k tokens of agent descriptions |
| **§10** | `model:` resolution has a middle step the guide missed: `CLAUDE_CODE_SUBAGENT_MODEL`. A stale export silently runs every subagent on a different model than its file says |
| **§11** | `plugin.json` requires only `name`. Manifest path fields **replace** the default directory instead of extending it (`skills` is the sole exception) — declaring `agents:` silently stops `agents/` from being scanned |
| **§11** | `${CLAUDE_PLUGIN_DATA}` (`~/.claude/plugins/data/{id}/`) survives updates — the right home for venvs, caches and generated code. New `workflows/` component; `bin/` flagged "not for distributed plugins" |
| **§30** | CCRs are **Routines**, with three triggers (schedule, API `/fire`, GitHub events) — the guide knew only one. Cloud minimum interval is **1 hour**. Fire `text` arrives wrapped as untrusted data; the prompt must opt in to acting on it |
| **§30** | A whole surface was missing: **Desktop scheduled tasks** run locally, without an open session, with local file access — which solves the per-project learnings case the guide had marked impossible |
| **§30** | **A green run status only means the session started and exited without an infrastructure error.** It says nothing about whether the task succeeded — that lives in the transcript |
| **§33** | `/fork` copies the conversation into another background session; the command that returns a result to this conversation is **`/subtask`**. The previous edition attributed `/subtask`'s behavior to `/fork` |
| **§34** | Jitter: recurring tasks fire up to 30 min late, one-shots at `:00`/`:30` up to 90s early — pick a minute that is neither. A scheduled fire cannot invoke a skill marked `disable-model-invocation: true` |

---

### v5.31 – v5.32 — re-verification against the live docs (2026-09-02)

| Area | Change |
|---|---|
| **§3 §25 §31** | Sonnet 5's introductory $2/$10 **became the standard price** — the September 1, 2026 increase to $3/$15 was cancelled. Opus:Sonnet is **2.5×**, and the ratio no longer expires |
| **§25** | **Opus 5** (`claude-opus-5`) replaces Opus 4.8 as the current Opus and is the account default on Max/Team Premium/Enterprise/API; Fable 5.1 tops the lineup. Claude Code aliases (`best`, `fable`, `opusplan`, `opus[1m]`) documented |
| **§25** | **Fast mode IS an API parameter** — `speed: "fast"` + beta `fast-mode-2026-02-01`. The previous edition claimed it wasn't. Opus 5/4.8 only; Opus 4.7 errors; **Opus 4.6 silently runs at standard speed** |
| **§25** | `xhigh` does not exist on Opus 4.6 or Sonnet 4.6 — there the step up is `max` |
| **§3** | Claude 4.7+ (Opus 5 and Sonnet 5 included) use a **new tokenizer: ~30% more tokens** for the same text. Haiku 4.5 and Sonnet 4.6 don't — so haiku's real advantage is ~2.6×, not 2× |
| **§7** | 33 hook events (`DirectoryAdded`, `PreModelSwitch`, `PostModelSwitch` are new). **`continueOnBlock`**: without it a denied `PreToolUse`/`PostToolUse` kills the turn instead of returning the error to Claude — changed in v2.1.210 |
| **§7** | **`if` is valid on only 5 tool events**; anywhere else it silently stops the hook from running. Fifth handler type `agent`. Hooks can be declared in 7 places, including skill and subagent frontmatter |
| **§6** | **`background: true` is the new default for `context: fork`** (v2.1.218) — narrower tool set, and `/rewind` does not undo its edits. **`skillOverrides` does not affect plugin skills.** Personal skills override project ones |

---

### v5.15

> **Superseded:** the pricing and fast-mode rows below were correct when written and are not any more — see the v5.31–v5.32 entry above. Kept as history.

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
