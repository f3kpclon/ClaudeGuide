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

> **[2026-06-03]** > The agent is only as good as the context it receives. Vague context → the agent improvises → correction loops → tokens ×3-5. Define output, scope and success criteria **before** invoking. `/plan` first. (→ §24)
>
### Basics — read first
- [§4 — Analogy: how to think the system](#4-analogy--how-to-think-the-system)
- [§1 — What to build and when?](#1-what-to-build-and-when)
- [§2 — Token budget](#2-token-budget)
- [§25 — Correct model (haiku/sonnet/opus)](#25-correct-model--single-decision-table)
- [§24 — The human factor: context before invoking](#24-the-context-contract--the-human-factor)
### Construction — what you use most
- [§5 — Agents](#5-agents)
- [§7 — Hooks](#7-hooks)
- [§6 — Skills](#6-skills)
- [§8 — Project Scope](#8-project-scope)
- [§9 — Learnings](#9-learnings)
- [§10 — Multi-agent architecture](#10-multi-agent-architecture)
- [§11 — Distributable plugin](#11-distributable-plugin)
- [§17 — Plan + Invocation Templates](#17-plan--invocation-templates--maximum-prompt-efficiency)
### Quality and efficiency
- [§14 — Anti-overkill guide](#14-anti-overkill-guide)
- [§12 — Common errors](#12-common-errors)
- [§13 — Quality checklist](#13-quality-checklist)
- [§23 — Real Token Ceilings](#23-real-token-ceilings--when-to-stop-optimizing)
- [§3 — Consumption estimates](#3-consumption-estimates)
### Advanced and reference
- [§16 — Vector Memory](#16-vector-memory--upgrade-of-the-learning-system)
- [§18 — Security](#18-security)
- [§19 — Agent Testing](#19-agent-testing)
- [§20 — CI/CD](#20-cicd)
- [§21 — Observability and debugging](#21-observability-and-debugging)
- [§22 — Advanced Prompt engineering](#22-prompt-advanced-engineering)
- [§15 — Glossary](#15-glossary)

> **[2026-06-03]** **Version:** v4.7 · Validated in production · Estimates updated with real data (2026-06-03)

> **[2026-06-03]** - [§26 — Global context hook](#26-global-context-hook)
<!-- §26 -->
<a id="26-global-context-hook"></a>
## 26. Global context hook
> CLAUDE.md tells you where to look in the guide, but not when. This hook automatically injects the relevant section before Claude responds — 0 extra tokens if the prompt is not relevant.
### Because
The problem: Claude knows the guide exists but needs to infer when to consult it. Sometimes it doesn't. The hook detects keywords in the prompt and extracts the correct section automatically.
| Without hook | With hook |
|---|---|
| Claude infers when to consult the guide | The relevant section arrives automatically |
| You can skip query when you should do it | 0 extra tokens if the prompt is not relevant |
`UserPromptSubmit` is executed **before** Claude processes the prompt. The stdout of the hook is injected as context into the session.
### 3-step installation
**1. Script** → `~/.claude/hooks/guia_context.py`
````python
#!/usr/bin/env python3
import json, sys, re
from pathlib import Path
GUIDE = Path.home() / "Desktop/ClaudeGuide/guia-agentes-plugins-claude-code.md"
MAX_LINES = 80
KEYWORD_MAP = [
(["agent", "agent", "subagent"], 5),
(["hook", "pretooluse", "posttooluse"], 7),
(["skill"], 6),
(["scope"], 8),
(["learning", "curator", "postmortem"], 9),
(["multi-agent", "lead", "architecture"], 10),
(["plugin", "distributable"], 11),
(["haiku", "sonnet", "opus", "model"], 25),
(["human factor", "invoke"], 24),
(["overkill"], 14),
(["budget", "tokens", "cost"], 2),
(["vector memory", "semantics"], 16),
(["security", "security"], 18),
]
def detect_section(prompt):
p = prompt.lower()
for keywords, n in KEYWORD_MAP:
if any(k in p for k in keywords):
return n

def extract_section(n):
lines = GUIDE.read_text().splitlines()
for anchor in [f"<!-- §{n}-quick -->", f"<!-- §{n} -->"]:
try:
start = next(i for i, l in enumerate(lines) if anchor in l) + 1
exceptStopIteration:
continue
result = []
for line in lines[start:]:
if re.match(r"<!-- §\d", line):
break
result.append(line)
if len(result) > 3:
return "
".join(result[:MAX_LINES]).strip()
return ""
try:
payload = json.load(sys.stdin)
except Exception:
sys.exit(0)
section = detect_section(payload.get("prompt", ""))
if section:
content = extract_section(section)
if content:
print(f"[Guide §{section}]
{content}")
````
**2. Permissions**
```
chmod +x ~/.claude/hooks/guia_context.py
```
**3. Register in `~/.claude/settings.json`**
```json
"UserPromptSubmit": [
{
"hooks": [{
"type": "command",
"command": "python3 /Users/felixsotelo/.claude/hooks/guia_context.py"
}]
}
]
```
### Add sections to the map
To include a new section, add an entry to `KEYWORD_MAP` in the script:
```python
(["keyword1", "keyword2"], N), # §N — Section name
```
### Checklist §26
```
□ guia_context.py created in ~/.claude/hooks/
□ chmod +x applied
□ UserPromptSubmit registered in ~/.claude/settings.json
□ Prompt with "agent" → §5 injected as context
□ Prompt without keywords → without injection
```
---
