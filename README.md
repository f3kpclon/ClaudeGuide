# The Broke Dev's Guide: Agents & Plugins in Claude Code
*Maximum efficiency. Minimum spend. Zero apologies.*

**Author:** Félix Sotelo — Broke dev with rich aspirations
**Version:** v4.6 · Production-validated · Estimates updated with real data (2026-05-31)

---

> 🌐 **Language / Idioma:** **🇺🇸 English** · [🇪🇸 Español](README.es.md)

---

> Every byte in context has a cost. This guide exists so you can build powerful systems without your credit card crying at the end of the month.
>
> If you can do something with **haiku**, don't use sonnet. If you can use a rule in CLAUDE.md, don't create an agent. If you can put a gotcha inline, don't make the agent read a file.
>
> This is the philosophy. The rest is implementation.

---

## Where to Start

**First time with the system?** Read in this order:

1. **§4 — The restaurant analogy** → understand the system in 5 minutes before touching code
2. **§1 — What to build?** → the decision tree that saves you from building what you don't need
3. **§2 — Token budget** → the one concept that changes how you design everything
4. **§12 — Critical errors** (first table) → read just that one, avoid the most expensive mistakes
5. **§15 — Glossary** → when a term doesn't make sense, look it up there

**Already know the system and want to build something specific?**

| I want to... | Go to |
|---|---|
| Create an agent | §5 — format, model, tools, trigger list |
| Create a hook | §7 — PreToolUse, PostToolUse, Python templates |
| Build a distributable plugin | §11 — structure, plugin.json, test locally |
| Configure learnings + curator | §9 — postmortem flow → learnings → curator |
| Design multi-agent architecture | §10 — lead, specialists, workflow |
| Know if what I built is overkill | §14 — anti-overkill tree |

---

## Table of Contents

1. [What to Build and When?](#1-what-to-build-and-when)
2. [Token Budget](#2-token-budget)
3. [Consumption Estimates](#3-consumption-estimates)
4. [Analogy — How to Think About the System](#4-analogy--how-to-think-about-the-system)
5. [Agents](#5-agents)
6. [Skills](#6-skills)
7. [Hooks](#7-hooks)
8. [Project Scope](#8-project-scope)
9. [Learnings](#9-learnings)
10. [Multi-Agent Architecture](#10-multi-agent-architecture)
11. [Distributable Plugin](#11-distributable-plugin)
12. [Common Errors](#12-common-errors)
13. [Quality Checklist](#13-quality-checklist)
14. [Anti-Overkill Guide](#14-anti-overkill-guide)
15. [Glossary](#15-glossary)

---

## 1. What to Build and When?

> The most important question before writing a single line. Building what you don't need is the most expensive mistake — not for the token it costs now, but for the token it will cost every session forever.

```
What do you need?
│
├── A rule that always applies to this project
│   └── → CLAUDE.md
│
├── A specialized task that repeats
│   └── → Agent (.claude/agents/)
│
├── A reference or template Claude loads when needed
│   └── → Skill (.claude/skills/)
│
├── Something that must always happen (validate, block, notify)
│   └── → Hook (.claude/settings.json)
│
├── Project context (state, decisions, backlog)
│   └── → Scope (.claude/scope/)
│
├── Lessons captured per session
│   └── → Learnings (.claude/learnings/)
│
└── All of the above, reusable across multiple projects
    └── → Plugin (.claude-plugin/)
```

| | Local Agent | Local Skill | Plugin |
|---|---|---|---|
| Location | `.claude/agents/` | `.claude/skills/` | directory with `.claude-plugin/` |
| Scope | This repo only | This repo only | Wherever installed |
| Hooks | `.claude/settings.json` | — | `hooks/hooks.json` |
| Sharing | Only via the repo | Only via the repo | `claude plugin add github:...` |

**Rule:** start with local agents and skills. Convert to a plugin only when reused in another project.

---

## 2. Token Budget

> Thinking in tokens is like thinking in RAM in the 90s: you can't ignore it. The difference is that here every megabyte also costs money. Reading this section once saves you more money than any code optimization you'll ever do.

The most important principle in the entire guide. Every byte in context has a cost.

### The Three Cost Layers

```
Layer 1 — ALWAYS in context (fixed cost per session)
  CLAUDE.md           → re-injected on EVERY tool call (most expensive)
  Agent descriptions  → present in the system prompt
  Skill metadata      → 30-50 tokens per registered skill
                        (user-invocable-only reduces this to zero for the model)

Layer 2 — ON DEMAND (variable cost)
  Inline gotchas      → in the agent's system prompt, zero Read calls
  SKILL.md content    → loaded when Claude activates it
  Learnings           → only the relevant domain — only if not inline
  Scope               → only the file the agent needs
  Reference docs      → only when the agent explicitly requests them

Layer 3 — ZERO COST in the main context
  Running agent       → runs in isolated context
```

### Inline Gotchas vs Learnings File

For gotchas an agent needs **always** (not conditionally), inlining in the agent is cheaper than asking it to read the file:

```
❌ "Read before starting: .claude/learnings/learnings-script.md"
   → 1 Read tool call (request + result wrapper ≈ 300-600 tokens of overhead)
   → extra latency before any work

✅ ## Critical Gotchas
   - AnimationTree active=true silences _physics_process. Fix: active=false.
   - grab_focus() in _ready() doesn't work. Fix: call_deferred().
   → inline in the system prompt, zero tool calls
```

The learnings file still exists for the postmortem to update. Agents read it only on demand (complex tasks, debugging). The most-used gotchas go inline.

### Size Limits per File

| File | Limit | Why |
|---|---|---|
| `CLAUDE.md` | < 30 lines | Re-injected on every tool call |
| Hub skill (project with CLAUDE.md) | < 40 lines | Always in context — triage only |
| Hub skill (plugin without CLAUDE.md) | < 60 lines | Hub is the only dispatch — can carry slightly more context |
| Reference skills | < 200 lines | Loaded on demand |
| Reference docs | < 100 lines | Read in full |
| Learnings per domain | < 150 lines | Loaded only when applicable |
| Scope per domain | < 50 lines | Must be dense and direct |
| `description` | < 1,024 chars | Hard limit from the spec |

### DRY Principles

- **One place per content** — if it exists in a skill, don't copy it in the agent
- **Reference, don't copy** — `read .claude/docs/ref.md` instead of pasting the content
- **Fragment by domain** — a 500-line file is always read in full; 5 files of 100 lines are read only when applicable
- **Critical gotchas inline** — if an agent always reads them, put them directly in its prompt

### CLAUDE.md — Template

```markdown
# [Project]

## Dispatch
≥2 systems or ≥3 files?   → @lead
Bug?                        → @debugger
[Domain A]?                 → @agent-a
Review?                     → @reviewer
End of session?             → @postmortem

## Hard Rules
- Critical rule 1
- Critical rule 2
- Direct code — no over-engineering

## Learnings
[Domain A]: read `.claude/learnings/domain-a.md`

## Scope
Read `.claude/scope/scope-index.md` before any task.
```

---

## 3. Consumption Estimates

> Before starting any task, the broke dev makes an estimate. These numbers are approximate but enough to know if you'll spend $0.02 or $0.50 before writing a line.

Numbers are approximate. They serve to plan before starting.

### Fixed Cost per Session

Tokens always consumed, before any real work.

| Component | Tokens | Notes |
|---|---|---|
| CLAUDE.md (~30 lines) | ~200 | Re-injected on every tool call |
| Hub skill (~40 lines) | ~280 | Only if auto-trigger is active |
| Agent descriptions (×10) | ~400 | ~40t per registered agent |
| scope-index.md (~20 lines) | ~120 | If in CLAUDE.md |
| **Minimum fixed total** | **~1,000** | Per session, before any task |

If the hub has `skillOverrides: user-invocable-only`, the model doesn't auto-activate it and the ~280 tokens aren't spent.

### Cost per Task Type

Additional on top of the fixed cost.

| Task | Agents | Extra tokens (main context) | Subagent tokens (isolated) |
|---|---|---|---|
| Simple bug (1 bug, ≤3 files) | debugger + reviewer | ~600 | ~6-10k |
| Complex bug (2+ bugs, 5+ files) | debugger + reviewer | ~800 | ~14-18k |
| Simple feature (1 system) | specialist + reviewer | ~800 | ~4-8k |
| Medium feature (2 systems) | lead + 2 specialists + reviewer | ~1,400 | ~10-16k |
| Complex feature (3+ systems) | lead + 3 specialists + reviewer | ~2,200 | ~18-28k |
| Cross-cutting refactor | lead + all specialists | ~3,000 | ~30-40k |
| End of session | postmortem + git | ~500 | ~2-4k |

### Model Impact

| Model | Relative cost | When |
|---|---|---|
| haiku | 1x | Fixed tasks: git, postmortem, checklist reviewer |
| sonnet | 5x | Implementation, debugging |
| opus | 15x | Architecture with complex trade-offs |

A reviewer in sonnet costs 5x more than in haiku — same result.

---

## 4. Analogy — How to Think About the System

> If the official documentation doesn't make sense yet, start here. Once you understand the restaurant, everything else just clicks.

Before building anything, this analogy explains why the system works this way.

### The Restaurant

Imagine Claude Code is a **restaurant kitchen**.

```
CLAUDE.md         → the rules board in the kitchen
                    Everyone reads it before starting their shift.
                    If it has 200 rules nobody follows them well.
                    If it has 10 clear rules, everyone follows them.

Agents            → the specialized cooks
                    The pastry chef only makes desserts.
                    The grill cook only makes meats.
                    Neither does the other's work.
                    Each has their own tools.

Lead (orchestrator) → the head chef
                    Doesn't cook — coordinates who does what and when.
                    If they need a dessert, they call the pastry chef.
                    If they need meat, they call the grill cook.
                    No knives (no Bash) — only gives instructions.

Skills            → the recipe books
                    Don't cook alone — they're reference when needed.
                    The pastry chef consults the dessert recipe book.
                    The grill cook consults the meat one.
                    Nobody reads all the recipe books at the same time.

Hooks             → the quality control system
                    Before a dish goes out (PreToolUse):
                    verify temperature, presentation, ingredients.
                    If it doesn't pass → send back to the kitchen.
                    If it passes → let it through.

Scope             → the day's menu
                    What dishes exist, which are missing, what's next.
                    The head chef reads it before organizing the day.
                    The cooks don't need it — they get instructions.

Learnings         → the kitchen's error notebook
                    "Oven 3 takes 5 min longer than normal."
                    "Pizza dough needs 2h to rest, not 1h."
                    Each area has its own notebook.
                    The most common errors are posted on the wall (inline).
                    The full notebook is only read for new problems.

Tokens            → the shift's time
                    Everything in context consumes time before cooking.
                    A board with 200 rules takes 10 min to read.
                    A board with 10 rules takes 1 min.
                    Less time reading → more time cooking.
```

### The Golden Rule

> An agent that does one thing well
> is worth more than an agent that does everything so-so.

The pastry chef who also tries to make meat ends up doing both badly.
Divide responsibilities until each agent has **one single reason to exist**.

---

## 5. Agents

> An agent is Claude with a fixed role, limited tools, and an isolated context. The low-cost key: give it only the tools it needs and the cheapest model that can do the job.

### Format

```markdown
---
name: my-agent
description: Trigger list. Use when the user asks for X, mentions Y,
  or the context involves Z.
tools: Read, Write, Edit, Glob, Grep
model: sonnet
---

# Agent Name

One line of responsibility. No narration.

## Critical Gotchas
- Common error 1: cause and fix in one line.
- Common error 2: cause and fix in one line.

## Rules
- Concrete rule
```

### Frontmatter Fields

| Field | Required | Notes |
|---|---|---|
| `name` | Recommended | How it's invoked: `@my-agent` |
| `description` | **Yes** | Trigger list — the most important thing |
| `tools` | No | Without this inherits everything — always specify |
| `model` | No | `haiku`, `sonnet`, or `opus` |

### Model by Agent Type

| Agent | Model | Criteria |
|---|---|---|
| git, postmortem, checklist reviewer | `haiku` | Fixed instructions — 5x cheaper |
| Implementer, debugger | `sonnet` | Reasons over variable context |
| Architecture with complex trade-offs | `opus` | High-level decisions |

### Tools by Responsibility

| Role | Tools |
|---|---|
| Read-only (reviewer, auditor) | `Read, Glob, Grep` |
| Implementer | `Read, Write, Edit, Glob, Grep` |
| Orchestrator | `Read, Write, Edit, Glob, Grep` — no Bash |
| Git / shell | `Bash, Read` |
| Postmortem | `Read, Write, Glob, Grep, Bash` |

### Description — Trigger List

```markdown
# ❌ Generic — never activates correctly
description: Helps with code reviews.

# ✅ Trigger list — activates in the right cases
description: Convention checker. Use when reviewing, checking, auditing,
  or validating any file. Use after implementing any component or before committing.
```

### Rules in Prompt vs Hooks

Rules written in an agent's system prompt are **suggestions**, not guarantees.

```
❌ In the agent: "NEVER: git push origin master"
   → The agent can still do it if the user says "merge to master"

✅ PreToolUse hook that blocks "git push origin master"
   → The agent physically cannot execute it — the tool is denied
```

### Output Format — The Cheapest Lever

```markdown
## Output — always this format, nothing else
Hypothesis 1 (most likely): [cause in 1 line]
Confirm: [minimum action]
Fix: [concrete change]

Hypothesis 2: [only if 1 doesn't apply]
```

**Measured real impact:**
```
Without output format (general-purpose):              ~21k tokens
With forced output format — simple task:              ~6-10k tokens
With forced output format — complex task (10 uses):   ~14-18k tokens

Savings vs no format: ~30-65%
```

### Base Agents for Any Project

| Agent | Responsibility | Model |
|---|---|---|
| `lead` | Orchestrator ≥2 systems | sonnet |
| `reviewer` | Conventions and quality | haiku |
| `debugger` | Diagnosis before modifying | sonnet |
| `git` | Branches, commits, PRs | haiku |
| `postmortem` | Session-end lessons — capture | haiku |
| `curator` | Monthly learnings maintenance | haiku |

### Agent Size Limits

| Model | Prompt limit | Why |
|---|---|---|
| haiku | < 60 lines | Fixed tasks — concrete instructions |
| sonnet | < 120 lines | Variable reasoning |
| opus | < 80 lines | High-level decisions, not long lists |

### Where to Place Agents

```
~/.claude/agents/          → personal, all your projects
.claude/agents/            → local, this repo only
plugins/my-plugin/agents/  → plugin, wherever installed
```

---

## 6. Skills

> A skill is a recipe book: it doesn't cook alone, but when the agent needs it, it consults it. The difference with an agent is that it has no own context — it shares the main thread.

### Format

```markdown
---
name: my-skill
description: Trigger list. Most important use case first.
disable-model-invocation: false
allowed-tools: Read
---

## Direct instructions.
For detailed reference → `docs/ref.md`
```

### Types and Configuration

| Type | `disable-model-invocation` | Size | Use |
|---|---|---|---|
| Hub / dispatch | `false` | < 40 lines | Automatic triage |
| Reference | `true` | < 200 lines | Conventions, patterns |
| Template | `true` | No practical limit | Never in active context |

### Controlling When a Skill Activates

```json
// .claude/settings.json
{
  "skillOverrides": {
    "my-hub": "user-invocable-only",
    "my-reference": "off"
  }
}
```

| Value | Effect |
|---|---|
| `"on"` (default) | Available for model and user (`/name`) |
| `"user-invocable-only"` | Model does NOT activate it; user CAN call it with `/name` |
| `"off"` | Invisible to everyone |

---

## 7. Hooks

> Hooks are the only real guarantee mechanism. A rule written in an agent's prompt is a suggestion. A PreToolUse hook that blocks an action is pure physics: the agent cannot execute it even if it wants to.

### Where They Go

| Context | File |
|---|---|
| Local project | `.claude/settings.json` |
| Plugin | `hooks/hooks.json` |

### Essential Events

| Event | Blockable | Use |
|---|---|---|
| `PreToolUse` | **Yes** | Validate before writing or executing |
| `PostToolUse` | No | Confirm, notify, auto-format, chain actions |
| `SubagentStop` | No | Chain agents, notify user |
| `Stop` | No | End-of-session reminders |

### PreToolUse — Block with JSON

```python
#!/usr/bin/env python3
import json, sys

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    violations = validate(payload)  # your logic

    if not violations:
        sys.exit(0)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "\n".join(violations)
        }
    }))
    sys.exit(0)

if __name__ == '__main__':
    main()
```

### Hook Rules

- `chmod +x` on all scripts
- `try/except` in **all** hooks — not just PreToolUse
- PreToolUse uses JSON with `permissionDecision` — never `exit(2)`
- SubagentStop and PostToolUse use `systemMessage` — never raw `echo`
- Bash string checks: use `re.split` to isolate the first command
- Project paths: `Path(__file__).parent.parent.parent` — never absolute paths
- MultiEdit: extract from `edits[].new_str`, not `tool_input.new_str`

---

## 8. Project Scope

> Without scope, each agent starts from scratch — reads 5 files to understand what exists before it can do anything. With well-written scope, it goes straight to work.

### Structure

```
.claude/scope/
├── scope-index.md        → 20-line summary — everyone reads this
├── scope-[system-a].md   → detail of a specific system
└── scope-[system-b].md
```

### Who Reads What

- **CLAUDE.md** → points only to `scope-index.md`
- **Lead / orchestrator** → index + scope of the system to plan
- **Specialists** → none (receive context from the lead)
- **Postmortem** → index (to update status)

---

## 9. Learnings

> The learnings system is the project's memory. Without it, every session repeats the same mistakes.

### Structure

```
.claude/learnings/
├── learnings-[domain-a].md   → < 150 lines
├── learnings-[domain-b].md
└── learnings-general.md       → patterns that apply to everything
```

### Entry Format

```markdown
- [YYYY-MM-DD] [CATEGORY] concrete description of the problem.
  Cause: why it occurs.
  Solution: exact fix or correct pattern.
```

### Postmortem → Learnings → Curator Flow

```
Work session
    ↓
@postmortem  →  writes entries in learnings/learnings-[domain].md
                (NOT in the hub — hub is fixed cost per session)
    ↓
stop.py      →  warns if any learnings exceeds 150 lines
    ↓
@curator     →  monthly: dedup + prune + promotes critical gotchas inline
```

---

## 10. Multi-Agent Architecture

> Multiple specialized agents working in sequence, each in their own isolated context, without contaminating the main thread. The secret: the lead coordinates without implementing, specialists implement without coordinating.

### Recommended Workflow

```
1. Commit pending changes     → @git
2. New branch                 → @git
3. Implementation             → specialist or @lead
4. Review                     → @reviewer
5. PR + merge                 → @git
6. End of session             → @postmortem
```

### Design Rules

- **Agents = isolated contexts** — what an agent reads doesn't contaminate the main thread
- **No nesting** — a specialist cannot invoke another specialist
- **Lead has no Bash** — coordinates with instructions, doesn't execute
- **Commit before branching** — uncommitted changes mix between features

---

## 11. Distributable Plugin

Only when you need to reuse across multiple projects or share with the team.

### Structure

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json       ← REQUIRED
├── agents/
├── skills/
├── hooks/
│   └── hooks.json        ← REQUIRED if using hooks
└── README.md             ← REQUIRED for distribution
```

### plugin.json

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "One line of what it does.",
  "author": {"name": "Your Name"},
  "repository": "https://github.com/user/my-plugin",
  "license": "MIT"
}
```

### Test Locally

```bash
claude --plugin-dir ./my-plugin   # load without installing
/reload-plugins                   # reload changes
/hooks                            # verify registered hooks
```

---

## 12. Common Errors

### 🔴 Critical — Fail Silently, High Cost or Irreversible Consequences

| Error | Symptom | Fix |
|---|---|---|
| Long CLAUDE.md | Every tool call consumes tokens before working | < 30 lines. Conventions → skills |
| Hub auto-trigger with dispatch in CLAUDE.md | ~280t extra per task with no benefit | `skillOverrides: {"hub": "user-invocable-only"}` |
| No model in agent | All use the same expensive model | Always specify. haiku for fixed tasks |
| Reviewer with sonnet | Implementer cost for a checklist | haiku |
| Bash in orchestrator | Lead executes instead of delegating | Remove Bash |
| Postmortem writes in the hub | Fixed cost grows every session | Write to `learnings/learnings-[domain].md` |
| `new_str` in MultiEdit always empty | Validation bypassed silently | Extract from `edits[].new_str` |
| PreToolUse with exit 2 | Error without structured reason | Return JSON `permissionDecision: deny`, exit 0 |
| Absolute path in hook | Hook breaks when project is moved | `Path(__file__).parent.parent.parent` |
| Agent git pushes to master | Irreversible | PreToolUse hook blocking `git push origin master` |
| Reviewer with ≥7 files | 34 tool uses → 22.7k tokens (measured) | Only directly modified files (≤4) |

### 🟡 Frequent — Poor Design and Bad Practices

| Error | Symptom | Fix |
|---|---|---|
| Missing `hooks.json` | Python scripts never execute | Create `hooks/hooks.json` |
| Monolithic doc | Agent reads 500 unnecessary lines | Split by domain, max 100 lines each |
| Duplicate content | Paid twice in tokens | One place per content |
| No bash failure protocol | Infinite workaround loop | Max 2 cycles. Report and stop |
| Monolithic learnings | 500+ lines always loaded | Fragment into domains < 150 lines |
| Diagnostic agent without output format | 3-4x more tokens in response | Add `## Output` section with compact template |

---

## 13. Quality Checklist

```
CLAUDE.md
□ < 30 lines
□ Only triage and critical rules
□ Reference to scope-index.md
□ No tables or code examples

Agents
□ description as trigger list
□ model specified (haiku/sonnet/opus)
□ tools at minimum necessary
□ orchestrator without Bash
□ reviewer with haiku
□ agents with Bash have failure protocol (max 2 cycles)
□ single responsibility per agent
□ critical gotchas inline (## Critical Gotchas section)
□ diagnostic agents have ## Output section with forced format
□ no duplicate content with skills or docs

Skills
□ Hub: disable-model-invocation: false, < 40 lines
□ Hub with dispatch in CLAUDE.md → skillOverrides: user-invocable-only
□ References: disable-model-invocation: true
□ description < 1,024 chars

Scope
□ scope-index.md < 20 lines
□ One file per system, < 50 lines
□ Postmortem updates it at end of session

Learnings
□ One file per domain, < 150 lines
□ Concrete entries: problem + cause + solution
□ Top 5-10 critical gotchas inline in the corresponding agent
□ Curator agent for monthly maintenance (not every session)
□ Postmortem writes in learnings/ — NEVER in the hub

Hooks
□ settings.json declares all hooks
□ Scripts with chmod +x
□ PreToolUse uses JSON permissionDecision
□ SubagentStop and PostToolUse use systemMessage (not echo)
□ try/except in ALL hooks
□ No absolute paths
□ MultiEdit extracts edits[].new_str, not tool_input.new_str

Plugin (if applicable)
□ plugin.json with spec fields
□ README.md with installation and usage
□ hooks/hooks.json exists
```

---

## 14. Anti-Overkill Guide

> Every component you add has a fixed cost per session — even if never used. This section is the antidote to the over-engineering instinct.

### The Question That Stops Overkill

> **What happens if I DON'T do it?**

If the answer is "nothing, it works the same" → don't build it.

### Decision Tree

```
Do I need this?
│
├── Has the problem this solves already occurred?
│   NO → wait. Don't design for hypotheticals.
│   YES → continue.
│
├── Will it repeat more than 3 times?
│   NO → solve inline. Don't abstract.
│   YES → continue.
│
├── Does something exist that already solves it?
│   YES → use it.
│   NO → build it.
│
└── Is the abstraction more complex than what it abstracts?
    YES → overkill. Make it simpler or don't do it.
    NO → go ahead.
```

### When NOT to Build Each Component

| Component | Overkill when... | Alternative |
|---|---|---|
| New agent | Task occurs < 3 times | Add a section to the existing agent |
| Hook | Rule has no real consequences if ignored | Rule in the agent prompt |
| Pre-layer (preflight) | Single dev with clear inputs | Direct dispatch from CLAUDE.md |
| Plugin | Code used in one project only | Local agent/skill |
| Curator | Project < 3 months or learnings under 150 lines | Don't run it yet |
| Hub skill | CLAUDE.md already has the complete dispatch | `skillOverrides: user-invocable-only` |
| Opus | Task is implementation, checklist, or git | haiku or sonnet |
| Lead | Task involves 1 system and < 3 files | Direct specialist |

### The Cost of "Just in Case"

```
An agent that's never invoked:           ~40t in system prompt per session
An unnecessary auto-trigger skill:       ~280t per task (LLM call)
A hook running on every Bash:            ~50ms latency per command
A 200-line learnings:                   ~1,400t when loaded
A 60-line CLAUDE.md:                    ~400t re-injected on EVERY tool call
```

The "just in case" is always paid. The "when I need it" is only paid when it occurs.

---

## 15. Glossary

**Token** — Claude's cost unit. ~¾ of an English word. Everything in context consumes tokens. Tokens = money.

**Context** — Claude's "working memory." Has a limit and a cost. If something is in context, Claude sees and processes it.

**Layer 3 / Isolated Context** — When an agent runs, it does so in its own separate context. What the agent reads doesn't contaminate the main thread. Free for the main thread.

**haiku** — Cheapest model. 1x reference cost. For fixed-instruction tasks: git, commits, checklists, postmortem.

**sonnet** — Middle model. 5x more expensive than haiku. For implementation, debugging, variable reasoning.

**opus** — Most powerful and expensive. 15x more than haiku. For complex architectural trade-offs.

**Agent** — Claude with a fixed role, specific tools, and its own system prompt. Runs in isolated context. Invoked with `@agent-name`.

**Skill** — Reference file (Markdown) that Claude loads when needed. Shares the main thread. Invoked with `/skill-name`.

**Hub** — Special always-in-context triage skill. Its only job: tell Claude which agent to use. Keep it short.

**Hook** — Python script that executes automatically when Claude does something. `PreToolUse` is the only blockable type.

**Plugin** — Agents + skills + hooks packaged with `plugin.json`. Installed with `claude plugin add github:user/repo`.

**Learnings** — Markdown files for lessons learned per session. Fragmented by domain. Loaded on demand. Limit: 150 lines per file.

**Gotcha** — Known error documented to prevent the agent from repeating it.

**Inline Gotcha** — Gotcha directly in the agent's system prompt. Zero Read calls — the agent knows it from the start.

**Postmortem** — Agent that captures session lessons into learnings. Never writes in the hub.

**Curator** — Monthly agent that deduplicates learnings and promotes critical gotchas to inline.

**Trigger list** — An agent's description, listing concrete use cases. The most important part of any agent.

**skillOverrides** — Config in `settings.json` to control skill activation: `on`, `user-invocable-only`, or `off`.

**ADR (Architecture Decision Record)** — Scope entry documenting a design decision: what was chosen, what was rejected, and why. Immutable — never edited, only appended.

---

## Official Resources

- [Agents](https://code.claude.com/docs/en/sub-agents)
- [Skills](https://code.claude.com/docs/en/skills)
- [Hooks](https://code.claude.com/docs/en/hooks-guide)
- [Plugins](https://code.claude.com/docs/en/plugins)
- [Agent Teams](https://code.claude.com/docs/en/agent-teams)
