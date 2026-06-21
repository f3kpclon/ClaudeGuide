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

---

## Contributing 👻

If you'd like to suggest something, open an [Issue](../../issues) and I'll take a look. If it fits my workflow, I'll incorporate it myself. Thanks for reading!

> **[2026-06-21]** - [§28 — Prompt Library (shortcuts + recipes)](#28-prompt-library--shortcuts-para-claude-code)
| `description` | < 1,536 chars | Actual system limit (`maxSkillDescriptionChars` configurable) |
### When to create a skill
The question is not "can I do this with a skill?" — is “where does this content best live?”
| Content | Where is it going | Why |
| Rule that applies **always**, in every task | `CLAUDE.md` | Fixed cost justified — it's the restaurant contract on the wall |
| Procedure that is loaded **on demand** | Skill | Free in tokens until summoned — the menu of the day |
| Task with **own context** or that would contaminate the thread | Agent (`context: fork`) | The sous-chef works in his separate kitchen — the main thread does not get dirty |
**Practical Trigger (Official):** Create a skill when you keep pasting the same instructions in the chat, or when a section of CLAUDE.md grew to be a procedure instead of a fact.
| Type | `disable-model-invocation` | Size | What Claude sees in context |
| Hub/dispatch | `false` | < 40 lines | Name + description always visible — automatic triage |
| Reference | `true` | < 200 lines | **Nothing** — neither name nor description — Claude doesn't know it exists until the user invokes it |
| Template | `true` | No practical limit | **Nothing** — same as reference, never in active context |
> **Analogy:** `disable-model-invocation: true` is not "do not activate" — it is removing the shelf tag. The recipe book is still there, but Claude doesn't even know it exists. A hub with `false` is the recipe book open in the kitchen — always visible. A reference skill with `true` is the technical manual in the drawer — free in tokens until someone asks for it.
| Value | Claude sees her | User can `/name` | Analogy |
| `"on"` (default) | Name + description | Yes | Recipe book on shelf with label and summary — Claude knows when to open it |
| `"name-only"` | Just the name | Yes | Recipe book with just the title — Claude knows it exists but not when to use it |
| `"user-invocable-only"` | Nothing | Yes | Recipe book in the drawer — the cook (user) looks for it, the model does not see it |
| `"off"` | Nothing | No | Recipe book in the basement — no one sees it, zero tokens |
### Lifecycle — what happens after invoking a skill
An invoked skill enters the context as a message and **stays for the entire session** — Claude does not read the file again. It's garlic bread on the table: once it arrives, it stays until you leave.
Auto-compaction rebinds the most recent skills with a budget of **5,000 tokens per skill, 25,000 shared tokens**. If you summoned many skills, the oldest ones drop first. Problem sign: skill "stops working" after too much sharing — re-invoking it with `/name` restores it.
### Frontmatter complete — all fields
| Field | Default | Usage |
| `name` | directory name | Display in list — does not change the `/` command |
| `description` | first paragraph | Automatic activation trigger. **First the most important case.** |
| `when_to_use` | — | Additional context — adds `description` towards the 1,536 chars limit |
| `argument-hint` | — | Hint on autocomplete: `[issue-number]`, `[file][format]` |
| `arguments` | — | Names for `$name` substitution: `arguments: [issue, branch]` |
| `disable-model-invocation` | `false` | `true` = removes shelf tag — Claude doesn't know it exists |
| `user-invocable` | `true` | `false` = hidden from menu `/` — Claude can invoke it, the user cannot |
| `allowed-tools` | — | Tools without permission prompt while skill is active |
| `disallowed-tools` | — | Tools blocked while skill is active (clears next message) |
| `model` | inherits session | Model override **for this shift only** |
| `effort` | inherits session | Effort override: `low\|medium\|high\|xhigh\|max` |
| `context` | — | `fork` = runs on isolated subagent |
| `agent` | `general-purpose` | Which subagent uses `context: fork` (`Explore`, `Plan`, or custom) |
| `hooks` | — | Hooks scoped to the skill life cycle |
| `paths` | — | Glob — skill is activated only when working with files that match |
| `shell` | `bash` | Shell for `!` commands: `bash` or `powershell` |
### String substitutions
**Example with named args:**
Invocation: `/fix-issue 42 feat/auth` → `$issue=42`, `$branch=feat/auth`.
### context: fork — isolated skill in subagent
Use `context: fork` when the skill would do heavy lifting that would contaminate the main thread (long diffs, exhaustive searches, file parsing). The content of SKILL.md becomes the subagent prompt — the main thread only receives the summary.
> **Rule:** If the skill searches or reads more than 3 files, consider `context: fork`. The subagent pays for its own context — the main thread doesn't mess with intermediate results.
`agent: Explore` is the cheapest to read: it does not load CLAUDE.md or git status. `agent: general-purpose` when you need more capacity.
### Supporting files — skill as directory
A skill can be a directory with support files. SKILL.md is the entrypoint; the rest are only loaded when explicitly referenced:
Reference from SKILL.md:
**When to use:** when SKILL.md exceeds 200 lines. The rule is the same as for any file on the system: a 500-line file is always read complete; Divided into parts, you read only what applies.
Prefix `!` executes a command and pastes the output into the context **before** Claude reads the skill — Claude receives actual data, not the command:
Use only when output is essential — each line costs tokens. For multi-line commands:
node --version
npm --version
git status --short
**`ultrathink` — extended reasoning in one word:** including `ultrathink` anywhere on the body activates deep thinking for that invocation. Use in audit skills or architectural decisions where the cost of error justifies the cost of reasoning.
### Events — full map
> A hook is the doorman of the building: the rule in the agent prompt is the "no entry" sign — the agent can ignore it. The PreToolUse hook is the locked door — the agent can't open it even if he wants to.
**Blockers** — can stop the action by returning `permissionDecision: deny` + exit 0:
| Event | Matcher | When does he shoot | Typical use |
| `PreToolUse` | Tool name | Before running any tool | Validate paths, block dangerous commands |
| `UserPromptSubmit` | Without matcher | Before Claude processes the user prompt | Block dangerous instructions, inject context |
| `PermissionRequest` | Tool name | When permission dialog appears | Auto-approve known safe commands |
| `PostToolBatch` | Without matcher | When finishing a batch of tools in the agentic loop | Stop the entire loop if something went wrong |
**Non-blocking** — observational, can inject context with `systemMessage` or `additionalContext`:
| Event | Matcher | When does he shoot | Typical use |
| `PostToolUse` | Tool name | After the tool was successful | Auto-format, chain actions, notify |
| `SubagentStop` | Agent name | Upon termination of a subagent | Chain agents, confirm user |
| `Stop` | Without matcher | At the end of Claude's turn | Reminders, end of session validations |
| `StopFailure` | Error type | When Claude stops by mistake | React to `rate_limit`, `overloaded`, `authentication_failed` |
| `SessionStart` | `startup\|resume\|clear\|compact` | When you log in or log back in | Inject initial context, `watchPaths`, `reloadSkills` |
| `FileChanged` | File name | Watched file changes on disk | Reload `.env`, trigger external validations |
### Handler types
The guide uses `"type": "command"` (Python/shell) in all examples. There are 3 more types:
| Type | When to use it |
| `"command"` | Local script — the most flexible, covers 95% of the cases |
| `"http"` | POST to an external server — webhooks, centralized logging, CI |
| `"mcp_tool"` | Directly calls a tool from an already connected MCP server |
| `"prompt"` | Claude decides yes/no with a prompt — for natural language validations |
### Optional fields per hook
- PreToolUse blocks with JSON `permissionDecision: deny` + exit 0 — never direct `exit(2)` (exit 2 blocks but without structured reason; any exit other than 0 and 2 shows the first line of stderr as a non-blocking error and the action continues the same)
### update Input — write instead of blocking
`updatedInput` is more powerful than `deny`: instead of rejecting the action, it silently corrects it before executing. The agent does not know that the command changed.
> The agent receives `npm ci` as if he had written it. `additionalContext` explains the change to you on the next turn.
### SessionStart — inject context on startup
`Session_Start` fires before Claude proceeds with the first message. Useful for loading external state (current branch, open tickets, active submission) without the user having to paste it.
### npm security guard — supply chain and slopsquatting
> **Analogy:** `npm install <package>` is like hiring a new employee without checking references — the postinstall script can execute arbitrary code from the moment it arrives. `npm ci` is to hire someone already verified (lockfile exact). `npx` is to let the employee bring his friends without introducing them.
**Specific risk to Claude Code — slopsquatting:** Attackers publish packages with names that AI models tend to mess up. If Claude suggests `import` of a package that does not exist and the agent does `npm install` directly, the malicious package is already installed.
**What this hook covers:**
| Command | Hook action | Why |
| `npx <package>` | Blocks + explains slopsquatting | Download and run without verification |
| `npm install <pkg>` | Blocks + suggests `--ignore-scripts` | Lifecycle scripts can be malicious |
| `npm install` | Rewrite to `npm ci` | Reproducible, does not modify lockfile |
| `npm ci` | Allows without intervention | Safe by design |
| `npm install <pkg> --ignore-scripts` | Allows | User explicitly opted in |
| PreToolUse with exit 2 | Blocks but for no reason visible to the user | Return JSON `permissionDecision: deny` + exit 0 — field accepts `deny\|allow\|ask\|defer` |
□ description < 1,536 chars (combined description + when_to_use; configurable with maxSkillDescriptionChars)
□ Skill with heavy work (> 3 long files/logs) → context: fork with agent: Explore
□ SKILL.md > 200 lines → split into SKILL.md + reference.md (directory as support)
□ Skill invoked in long session → re-invoke with /name if "forgotten" post-compact
□ model / effort only when the override is justified (do not use sonnet where haiku reaches)
□ user-invocable: false for background knowledge that is not a user action
□ PreToolUse uses JSON permissionDecision (deny|allow|ask|defer) + exit 0 — never exit 2
□ Node.js projects have npm_guard.py blocking npx and npm install <pkg> without --ignore-scripts
□ updatedInput instead of deny when the correction is mechanical (ex: npm install → npm ci)
□ SessionStart with matcher "startup|resume" to inject branch/state context at startup
| Specialist agent | The task is to copy an existing pattern with ≤3 changes and ≤2 files | Making it direct in main context — agent overhead (~3-4k cold start tokens) overcomes the risk of violating conventions |
**permissionDecision** — JSON field that a PreToolUse hook uses to control an action. Accepts `deny` (blocks), `allow` (approves without prompt), `ask` (shows equal dialog) or `defer` (delegates to the next hook). Always combined with exit 0: `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "reason"}}`. Exit 2 also blocks but for no structured reason — don't use it in PreToolUse.
**skillOverrides** — Setting in `settings.json` that controls what Claude sees for each skill. Four values: `"on"` (name + description in context, visible menu), `"name-only"` (only the name in context, visible menu — Claude knows it exists but not when to use it), `"user-invocable-only"` (hides from Claude, visible in menu to the user), `"off"` (invisible to everyone).
**disable-model-invocation** — Skill frontmatter field. `true` = removes the shelf tag: neither the name nor the description appear in Claude's context — the skill does not exist for him until the user invokes it with `/name`. `false` = the recipe book is on the shelf with visible label — Claude decides when to open it.
> **Analogy:** the model is the level of the chef you hire. Haiku = fast food cook — fast, economical, perfect for repeatable tasks. Sonnet = restaurant chef — for dishes that require technique. Opus = Michelin chef — for when the cost of ruining the dish exceeds the cost of the chef.
| Massive refactor/deep research | **opus** | Only when sonnet fails OR the cost of the error is irreversible |
| Context > 10k active tokens | **opus** | Sonnet loses coherence in very long contexts |
### Before Opus — try `effort` first
`effort` isn't a better model — it's giving today's chef more time to think. ~5× cheaper than upgrading to Opus.
**When `effort: xhigh` resolves what seemed like Opus:**
| Symptom | First attempt | If it keeps failing |
| Superficial reasoning in complex task | Sonnet + `effort: xhigh` | Opus |
| Loses the thread in long context | Fragment the problem | Opus |
| Hallucinations in architectural decisions | Sonnet + `effort: xhigh` + `/plan` | Opus one-shot |
### The decision framework for Opus
The question is not "is it a difficult task?" - is:
> **Does the cost of Sonnet being wrong exceed the cost of Opus?**
Opus costs ~5× more per token than Sonnet. If a Sonnet error costs 30 minutes to correct → Opus is worth it. If it costs 5 minutes → no.
**When Opus has real justification:**
| Case | Why Opus | Why not Sonnet |
| Security audit before merge to main | False negative = output gap | Can miss subtle attack patterns |
| Initial system architecture > 2 years of life | Error = months of refactor | With effort:xhigh you may not see long-term trade-offs |
| Multi-layer debug with context > 10k active tokens | Coherence in long context | Sonnet loses the plot — documented |
| One-shot decision without a second chance | No iteration possible | Sonnet in loop with validator is alternative |
### Concrete example — security-auditor with Opus justified
**Why Opus here and not Sonnet:** the audit runs once per PR. The cost delta is ~$0.04 per run. A false negative (vulnerability that goes into production) is worth orders of magnitude more. The agent has `tools: Read, Glob, Grep` — no Write or Bash — so the extra cost is only in reasoning, not execution.
**Why not `effort: xhigh` in Sonnet:** Subtle security patterns (IDOR, timing attacks, second-order injection) require Opus' level of reasoning. In security audits, the cost of error justifies the most capable model available.
| Default opus "to be safe" | Sonnet + `effort: xhigh` first — 5× cheaper |
| global `effort:xhigh` in settings.json | Only in agents or specific skills — the cost is multiplied for each tool call |
□ Before Opus → try Sonnet with effort: xhigh (skill frontmatter or settings.json)
□ Opus only if: security/arch one-shot OR context > 10k tokens OR error cost is irreversible
□ Opus Agents have minimal tools (Read/Grep/Glob) — the extra cost should be in reasoning, not execution
□ effort: xhigh not in global settings.json — only in agents/skills that need it
### Security and CI
This project installs hooks that run in **every user's Claude session**. A malicious PR in `hooks/` or `install.sh` is a real supply chain attack.
**GitHub Actions** (`.github/workflows/ci.yml`) — run in each PR towards `main`:
| Job | What does it do |
| `ShellCheck` | Lint of all `.sh` — errors and unsafe patterns |
| `Tests` | `bash test.sh` — 16 assertions, fails if install.sh aborts |
| `Security Scan` | Detect new dangerous patterns in `hooks/`, `install.sh`, `commands/`: `curl`, `wget`, `base64 -d`, `/dev/tcp`, `nc`, `python3 -c.*exec` |
**Note:** `set -euo pipefail` in `install.sh` causes tests to fail if the attacker injects an unresponsive `curl` — double protection without extra code.
**Branch protection** configured via API:
- Mandatory PRs with codeowner approval
- All 3 checks must pass before merging
- `enforce_admins: false` — the owner can do direct push
- `CODEOWNERS` in `.github/CODEOWNERS` — review auto-request to owner
□ Snapshots in {repo}/.claude/handoffs/ (created automatically, ignored by git)
□ CI passes in main (ShellCheck + Tests + Security Scan)
□ Branch protection active — Mandatory PRs for collaborators
□ CODEOWNERS configured — owner receives auto-request on each PR
/plan add rate limiting to login endpoint
> Complete skill in §27. The snapshot in `.claude/handoffs/latest.md` allows you to restart without questions.
#### `/new-agent [name]` · `HAIKU ONLY`
Generates the complete frontmatter + minimal structure for a new agent. Includes model, tools, description as trigger list, and Gotchas section.
#### `/new-skill [type]` · `HAIKU ONLY`
Generate the correct structure according to the type of skill. Types: `hub`, `reference`, `fork`.
#### `/new-hook [event]` · `HAIKU ONLY`
Generates the correct Python skeleton for the requested event. Includes try/except, re.split for first command, and the correct response JSON for that event.
#### `/debug-agent [name]` · `READ-ONLY` · `OVERLAPS /plan`
Diagnostic checklist when an agent fails, does unexpected things, or is more expensive than expected. Review description, tools, model, hooks and output format.
#### `/optimize [agent]` · `READ-ONLY` · `USE SPARINGLY`
Analyze the cost of an agent and suggest optimizations with the highest ROI. Follow the order of §23: output format → discovery calls → bash chaining → system prompt → scope.
#### `/audit-guia` · `READ-ONLY` · `HAIKU ONLY`
Validate the current project against the §13 checklist. Review CLAUDE.md, agents, skills, hooks and scope. List only violations — do not repeat what is right.
### Recipes — stacked shortcuts
> A shortcut alone is good. Two stacked in sequence are sharp. Three are a system.
#### "Run safely"
Plan before executing, execute with correct agent, capture state before closing. Order matters: without `/plan`, the agent can go in the wrong direction. Without `/handoff`, the next session starts from scratch.
#### "Improvement cycle"
First understand why it fails (symptom → cause), then reduce the cost. Doing them backwards optimizes a broken agent.
#### "Build and test"
Create the research skill, plan with it active to confirm that the scope is correct, execute.
#### "Build well from the ground up"
Generate the new agent, plan the first task to validate that the design is correct, audit against the checklist before using it in production.
### The 4 Laws — adapted to Claude Code
*(Originally from commandlib — mapped to sections of this guide)*
**Law 1 — Specificity beats shortcuts**
A prompt with scope + output + success criteria is worth more than 5 shortcuts in sequence. Shortcuts are shortcuts to the correct context, not context substitutes. → §24
**Law 2 — Constraints make Claude better**
Minimal `tools`, explicit `model`, forced output format. Each constraint you add to an agent is a token that Claude does not spend on deciding. → §5, §22
**Law 3 — Context is the advantage**
The `SessionStart` hook that injects branch + state weighs more than any shortcut. The context that arrives automatically is the one that is never forgotten. → §26
**Law 4 — Iterate, don't restart**
When something goes wrong, respond with what's wrong — don't rewrite the prompt. The thread is the accumulated context. `/handoff` before closing: the next session starts where you left off. → §27

> **[2026-06-21]** - [§29 — Own global context](#29-own-global-context--build-your-system)
## 29. Own global context — build your system
> Without a global context, Claude is a consultant who arrives every Monday without a notebook: you explain again who you are, what philosophy you follow and what he should not touch. With a global context, it is the same consultant but with his internalized rules, his tools in his pocket and his learning notebook open. The client does not explain — he works.
### The 4 layers — what each one does
| Layer | When to build it | If it does not exist |
| `CLAUDE.md` global | Always — it's the first | Claude improvises philosophy and rules in each session |
| Global skills | When CLAUDE.md has ≥5 lines explaining a procedure | You repeat the same instructions in each session |
| `UserPromptSubmit` hook | When you have a body of knowledge that Claude should automatically consult | Claude knows that the guide exists but he does not always consult it |
| `PreToolUse` hook | When there are actions that Claude should not be able to take in **any** project | A misconfigured agent can run `npm install` without stopping |
| Persistent memory | When there is feedback that you want to persist between sessions | You fix the same mistake twice |
### Construction order — decision tree
> **Scope rule:** if you doubt between global and project, it goes in the project. The global scope contaminates all contexts — a poorly calibrated global hook generates noise in projects where it does not apply.
### Separation `~/.claude/` vs `.claude/`
| Where | Applies to | Correct examples |
| `~/.claude/CLAUDE.md` | All projects | LowCost philosophy, model rules, shortcuts |
| `~/.claude/skills/` | All projects | `/plan`, `/handoff`, `/new-agent` |
| `~/.claude/hooks/` + `settings.json` | All projects | npm guard, guia_context.py, handoff hooks |
| `.claude/CLAUDE.md` | This project | Stack, agents, repo specific rules |
| `.claude/agents/` | This project | Domain Agents |
| `.claude/skills/` | This project | Project skills |
### Bootstrap from scratch — 5 steps
**Step 1 — CLAUDE.md global** (5 min)
**Step 2 — Automatic injection hook** (15 min)
Adapt `guia_context.py` (§26) with your own `KEYWORD_MAP` pointing to your docs. Register in `settings.json` under `UserPromptSubmit`.
**Step 3 — Skills for repeatable procedures** (10 min per skill)
Identify which instructions you paste more than 2 times a week. Each → `~/.claude/skills/<name>/SKILL.md` with `disable-model-invocation: true`.
**Step 4 — Guards for irreversible actions** (20 min)
A global `PreToolUse` with actions that should never happen in any project: `npm install <pkg>` without `--ignore-scripts`, direct push to protected branches, `rm -rf` without commit.
**Step 5 — Initialize memory** (5 min)
First entry: work philosophy feedback — the pattern you most frequently have to remind Claude of.
### Global context anti-patterns
| Anti-pattern | Consequence | Fix |
| Content of a specific project in `~/.claude/CLAUDE.md` | Contaminates all projects — Claude mentions a project stack in contexts where it does not apply | Move to the project's `.claude/CLAUDE.md` |
| Long global skills (> 200 lines) | Description budget is shared — one heavy skill displaces others in different projects | Split into SKILL.md + reference.md; or do project skill |
| Global `PreToolUse` too specific | Generates noise in projects where the condition does not apply | Save project in `.claude/settings.json` |
| Duplicate rules in global and project CLAUDE.md | Double cost, inconsistency when one changes and not the other | A source of truth — if always applicable → global; if it is from the project → project |
| Many global skills with `disable-model-invocation: false` | They compete with project skills, saturate the budget with descriptions | Only the hub or general knowledge skills in `false`; the rest in `true` |
### The system in this guide as a real example
Each piece has its reference section. Nothing was invented alone — everything was built from the principles documented in the guide.
### Checklist §29
