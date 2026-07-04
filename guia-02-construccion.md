# Guía del Dev Pobre — 02 · Construcción
*Parte de [guia-00-indice.md](guia-00-indice.md) — volver al índice.*

---

<!-- §5 -->
<!-- §5-quick -->
<a id="5-agentes"></a>

## 5. Agentes

> Un agente es Claude con un rol fijo, herramientas limitadas y un contexto aislado. La clave lowcost: darle solo las herramientas que necesita y el modelo más barato que pueda hacer el trabajo. Un agente mal configurado cuesta lo mismo que uno bien configurado — pero produce peores resultados.

### Template — agente

```markdown
---
name: <nombre-kebab-case>           # cómo se invoca: @nombre · único en el proyecto
description: "<Qué hace este agente>. Usar cuando <caso principal>,
  <caso secundario>, o el contexto involucra <señal de activación>."
model: <claude-haiku-4-5|claude-sonnet-5|claude-opus-4-8>   # pinear siempre — ver §25
tools: <Read, Glob, Grep>           # solo las necesarias — ver tabla de tools abajo
---

# <Nombre Legible>

<Una línea: qué HACE este agente.>
<Una línea: qué NO HACE — delimita el scope para el orchestrador.>

## Gotchas críticos
- <problema conocido del dominio>: <causa> → <fix>
- <otro gotcha>: <causa> → <fix>

## Output                           # SOLO si el agente produce output estructurado
<formato exacto — tabla, lista corta, JSON · sin prosa>

## Protocolo de fallo               # SOLO si el agente usa Bash
Si un comando falla:
1. Reportar el error exacto — no intentar resolverlo solo
2. Proponer máximo UNA alternativa
3. Si falla de nuevo → parar y reportar al usuario
```

**Ejemplo completo — security-auditor:**

```markdown
---
name: security-auditor
description: "Audit de seguridad. Usar cuando el PR modifica auth, permisos,
  storage o cualquier input de usuario. No usar para linting o code style."
model: claude-opus-4-8              # one-shot irreversible — ver §25
tools: Read, Glob, Grep             # sin Write ni Bash — solo lectura
---

# Security Auditor

Revisa cambios en busca de vulnerabilidades de seguridad.
No implementa fixes — reporta y explica, el implementador corrige.

## Gotchas críticos
- IDOR: verificar que toda operación valide ownership del recurso antes de actuar
- Timing attacks: comparaciones de tokens deben usar hmac.compare_digest, no ==
- Second-order injection: sanitizar en storage Y al leer, no solo al escribir

## Output
PASS: <descripción>
FAIL: <vulnerabilidad> — <riesgo> — <fix sugerido>
RESULTADO: PASS | FAIL
```

<!-- §5-ref -->
### Campos del frontmatter

| Campo | Obligatorio | Notas |
|---|---|---|
| `name` | **Sí** | kebab-case · invocación: `@nombre` · único en el proyecto |
| `description` | **Sí** | Trigger list — lo más importante. Claude delega cuando matchea |
| `model` | Recomendado | `haiku` · `sonnet` · `opus` · `inherit` (default). Sin esto → hereda el modelo del hilo |
| `tools` | Recomendado | Sin esto hereda todo — siempre limitar al mínimo necesario |
| `disallowedTools` | No | Denylist — complemento de `tools`. Se aplica ANTES que `tools` si ambos están |
| `skills` | No | Skills a precargar en contexto al arrancar — el inverso de `context: fork` en skills (ver §6) |
| `permissionMode` | No | `default` · `acceptEdits` · `auto` · `dontAsk` · `bypassPermissions` · `plan` |
| `maxTurns` | No | Máximo de turnos antes de que el subagente pare automáticamente |
| `memory` | No | Memoria persistente entre sesiones: `user` (`~/.claude/agent-memory/`) · `project` · `local` |
| `isolation` | No | `worktree` = corre en un checkout git aislado — los cambios no tocan el hilo principal |
| `background` | No | `true` = siempre corre en background como tarea — no bloquea el hilo |
| `hooks` | No | Hooks scoped al ciclo de vida de este agente (misma sintaxis que settings.json). **Ignorado si el agente viene de un plugin** (verificado 2026-07-04) |
| `mcpServers` | No | MCP servers disponibles para este agente — referencia por nombre a uno ya configurado, o definición inline. **Ignorado si el agente viene de un plugin** |
| `effort` | No | Override de esfuerzo: `low` · `medium` · `high` · `xhigh` · `max` |
| `color` | No | Color en la UI: `red` · `blue` · `green` · `yellow` · `purple` · `orange` · `pink` · `cyan` |

**Gotcha verificado 2026-07-04 (doc oficial de sub-agents):** `hooks`, `mcpServers` y `permissionMode` se **ignoran en silencio** cuando el agente se carga desde un plugin — sin error, sin warning. Si un agente de plugin necesita alguno de estos tres, la única forma es que el usuario copie el archivo a `.claude/agents/` o `~/.claude/agents/` locales; agregar reglas en `permissions.allow` de `settings.json` es la alternativa para permisos, pero aplica a toda la sesión, no solo a ese subagente.

### Modelo por tipo de agente

→ tabla completa en §25. Regla corta: haiku para tareas fijas, sonnet para razonamiento, opus solo si el costo del error es irreversible.

### Tools por responsabilidad

| Rol | Tools |
|---|---|
| Solo lectura (reviewer, auditor) | `Read, Glob, Grep` |
| Implementador | `Read, Write, Edit, Glob, Grep` |
| Orchestrador | `Read, Glob, Grep` — sin Bash, sin Write, sin Edit |
| Git / shell | `Bash, Read` |
| Postmortem | `Read, Write, Glob, Grep, Bash` |

El orchestrador no usa Bash, Write ni Edit — coordina y delega, no implementa. Darle Write/Edit es lo mismo que escribir "NUNCA implementes" en el prompt: el agente puede ignorarlo. Sin las tools, es una garantía física — igual que un hook vs una regla en el prompt.

**Qué significa "verificar" sin Bash:**
Después de que el especialista termina, el lead lee los archivos generados y razona:
- ¿Las conexiones entre módulos están correctas (emisores, listeners, imports)?
- ¿No hay referencias string frágiles donde debería haber tipos concretos?
- ¿Los campos y dependencias obligatorias están declarados?
Sin Bash no hay ejecución — la verificación es estática, no en runtime.

### Description — trigger list

```markdown
# ❌ Genérico — nunca se activa correctamente
description: Helps with code reviews.

# ✅ Trigger list — activa en los casos correctos
description: Convention checker. Use when reviewing, checking, auditing,
  or validating any file. Use after implementing any component or before committing.
```

### Reglas en el prompt vs hooks — cuál es garantía

Las reglas escritas en el system prompt de un agente son **sugerencias**, no garantías. Un agente puede ignorarlas si interpreta que la situación lo justifica.

```
❌ En el agente: "NUNCA: git push origin master"
   → El agente puede igual hacerlo si el usuario le dice "mergea a master"

✅ Hook PreToolUse que bloquea "git push origin master"
   → El agente físicamente no puede ejecutarlo — la herramienta es denegada
```

**Regla práctica:** si un comportamiento incorrecto tendría consecuencias reales (push a producción, borrar archivos, saltarse CI), reforzarlo con un hook, no solo con texto en el prompt.

### Protocolo de fallo bash

Agregar en todo agente con Bash:

```markdown
## Protocolo de fallo
Si un comando falla:
1. Reportar el error exacto
2. Proponer máximo UNA alternativa
3. Si falla de nuevo → parar y reportar hipótesis
Máximo 2 ciclos por problema — nunca más.
```

### Agentes base para cualquier proyecto

| Agente | Responsabilidad | Modelo |
|---|---|---|
| `lead` | Orchestrador — coordina pipeline cross-especialistas | sonnet |
| `reviewer` | Convenciones (checklist fijo) | haiku — para correctness/seguridad ver split en §25 |
| `debugger` | Diagnóstico de bugs no obvios (multi-capa, async, runtime) | sonnet |
| `git` | Ramas, commits, PRs | haiku |
| `postmortem` | Lecciones al final de sesión — captura | haiku |
| `curador` | Mantenimiento periódico de learnings — dedup, prune, promover a inline | haiku |

**Lead — tools: `Read, Glob, Grep` únicamente** — garantía física, no recomendación (ver "Tools por responsabilidad" arriba).

**Debugger — cuándo incluirlo:**
```
¿El dominio tiene bugs cuya causa no es obvia desde el síntoma?
    SÍ → debugger (hypothesis ledger)
    NO → el implementer lo resuelve inline

Incluir cuando: multi-capa (iOS, Android, web fullstack, games)
                async/concurrency (Swift 6, Coroutines, Promises)
                runtime visual (SwiftUI, Compose, juegos)
No incluir:     CLI lineal, scripts simples, plugins (no tienen runtime)
```

El `postmortem` captura sesión a sesión. El `curador` corre mensualmente (o cuando un learnings supera el límite) para eliminar duplicados, archivar entradas obsoletas y verificar que los top gotchas estén inline en el agente correcto. No correr el curador en cada sesión.

### Campos avanzados del frontmatter

**`tools` — sintaxis extendida:**
```yaml
tools: Read, Glob, Grep                # allowlist exacta
tools: Agent(worker, researcher)       # allowlist de qué subagentes puede spawnar este agente
tools: Agent                           # puede spawnar cualquier subagente sin restricción
# Si Agent está ausente de tools → el agente no puede spawnar subagentes en absoluto
```

**`disallowedTools` — denylist (se aplica antes que `tools`):**
```yaml
disallowedTools: Write, Edit           # hereda todo excepto escritura
disallowedTools: mcp__github           # bloquea todos los tools del servidor MCP "github"
disallowedTools: mcp__*               # bloquea todos los MCP tools de cualquier servidor
```

**`skills` — precargar conocimiento al arrancar (inverso de `context:fork`):**
```yaml
skills:
  - api-conventions          # inyecta el contenido COMPLETO de esta skill al inicio
  - error-handling-patterns  # útil para agentes que siempre necesitan convenciones del proyecto
```
> Solo funciona con skills que tienen `disable-model-invocation: false`. Si la skill tiene `true`, Claude Code la saltea y logea un warning.
> Ver §6 para el patrón inverso: skill con `context: fork` que elige el agente.

**`memory` — persistencia entre sesiones:**
```yaml
memory: project   # .claude/agent-memory/<nombre>/ — shareable vía git (recomendado)
memory: user      # ~/.claude/agent-memory/<nombre>/ — cross-project
memory: local     # .claude/agent-memory-local/<nombre>/ — no committed
```
El agente recibe las primeras 200 líneas de su `MEMORY.md` en cada sesión. Útil para revisores que acumulan patrones del codebase a lo largo del tiempo.

**`isolation: worktree` — checkout git aislado:**
```yaml
isolation: worktree   # el agente trabaja en un branch temporal, no toca el hilo principal
                      # limpieza automática si no hay cambios al terminar
```
Combinado con `background: true` es el patrón para agentes que modifican muchos archivos en paralelo sin conflictos.

### Dónde colocar agentes

```
~/.claude/agents/          → personal, todos tus proyectos
.claude/agents/            → local, solo este repo
plugins/mi-plugin/agents/  → plugin, donde se instale
```

### Límites de tamaño para agentes

La guía da límites para todo excepto los agentes. Un agente largo se lee completo en cada invocación — igual que CLAUDE.md, solo que en contexto aislado.

| Modelo | Límite del prompt | Por qué |
|---|---|---|
| haiku | < 60 líneas | Tareas fijas — instrucciones concretas, no razonamiento largo |
| sonnet | < 120 líneas | Razonamiento variable — más contexto es válido, pero tiene costo |
| opus | < 80 líneas | Se usa para decisiones de alto nivel, no para listas largas |

Si un agente supera su límite → hay contenido que puede ir a un learnings file o skill de referencia.

### Output format — la palanca más barata

El tamaño del agente importa, pero el **output format** es el mayor lever de tokens. Un agente sin formato forzado produce todo lo que "parece útil" — tablas, secciones, hipótesis secundarias, resúmenes. Eso puede ser 3-4x más tokens que el mismo diagnóstico en formato compacto.

```markdown
## Output — siempre este formato, nada más
Hipótesis 1 (más probable): [causa en 1 línea]
Confirmar: [acción mínima]
Fix: [cambio concreto]

Hipótesis 2: [solo si la 1 no aplica]
```

Incluir esta sección en **todo agente de diagnóstico, revisión o postmortem** (debugger, reviewer, lead, postmortem). Sin ella, el modelo decide el formato en cada invocación — y siempre elige el más verbose.

**Impacto real medido (MathVoid, 2026-05-31):**
```
Sin output format (general-purpose):                                      ~21k tokens
Con output format forzado — tarea simple  (1 bug,  ≤4 archivos):         ~6-10k tokens†
Con output format forzado — tarea compleja (2 bugs, 10 tool uses):       ~14-18k tokens✓

Ejemplo real medido: @debugger, 2 bugs, 10 tool uses → 14.5k tokens
Ahorro vs sin formato: ~30-65% — la magnitud depende de la complejidad, no solo del formato
```

Esto aplica a **cualquier agente**, no solo al debugger. El output format es el lever más barato porque:
- No cambia el modelo ni las herramientas
- No reduce el trabajo real que hace el agente
- Solo elimina la verbosidad que el modelo genera cuando no sabe qué recortar

Lo que el output format **no puede reducir**: el costo de los tool calls. Cada Read, cada Bash, cada archivo leído se acumula en el contexto aislado del agente independientemente del formato.

El output format es especialmente crítico en agentes haiku: haiku tiende a ser más conciso por naturaleza, pero sin formato explícito puede igualmente producir listas largas cuando no sabe qué recortar.

### Invocar agentes — prompts mínimos

El orchestrador (o el usuario) invoca agentes con un prompt. Ese prompt se suma al system prompt del agente en cada tool call.

```
❌ Prompt de 200 palabras con comandos sugeridos, explicación del contexto
   y repetición del flujo que ya está en el system prompt del agente
   → el agente los ignora o los usa redundantemente — tokens desperdiciados

✅ Prompt de 2-3 líneas: qué hacer + datos que el agente no puede inferir
   → "Crear rama mathvoid/X, commitear archivo Y, PR con título Z"
```

**Regla:** si el agente ya sabe cómo hacer algo (está en su system prompt), no explicarlo en el prompt de invocación. Solo dar los datos variables: nombre de rama, título de PR, archivos específicos, resultado esperado.

**Cuánto ahorra:** un prompt de invocación corto vs. largo puede ser la diferencia entre 2k y 12k tokens para haiku — 6x de diferencia en una operación simple.

**Para el reviewer en particular:** pasar SOLO los archivos directamente modificados en la sesión — nunca archivos de contexto o arquitectura. El reviewer tiene Grep/Glob disponibles y los usa para cruzar referencias; cada archivo de contexto extra añade ~3-5 tool uses. 4 archivos → ~8-10 tool uses → ~4-8k tokens. 7 archivos → ~34 tool uses → ~22k tokens (medido, 2026-05-31).

### Señales de agente mal dimensionado

| Síntoma | Diagnóstico |
|---|---|
| Hace 3+ Read calls antes de trabajar | Faltan gotchas inline — el agente busca lo que debería saber de entrada |
| Pregunta "¿qué querés hacer?" | Description demasiado genérica — no activa en los casos correctos |
| Escribe código que otro especialista debería escribir | Responsabilidades solapadas — dividir |
| Ignora sus propias reglas | Prompt demasiado largo — las reglas del final se diluyen |
| Tarda igual que el implementador en solo revisar | Está en sonnet cuando debería estar en haiku |
| Invoca herramientas que no necesita | `tools` heredado por defecto — siempre especificar al mínimo |
| Reviewer hace 25+ tool uses | Scope demasiado amplio — explora arquitectura además de convenciones. Fix: pasar solo archivos directamente modificados (≤4) + protocolo "1 Read por archivo" |

### Split de checklist — core + reference (cuando un agente crece)

> Un validator/reviewer que empieza con 4 checks y termina con 13 diluye sus propias reglas —
> el mismo síntoma de la tabla de arriba. La solución no es recortar contenido real: es el mismo
> patrón hub+reference que ya usás en skills (§6), aplicado a agentes.

```
Agente checklist crece cada vez que se agrega una feature nueva
    → separar: checks core (siempre corren) quedan en el .md del agente
    → checks condicionales (solo si TYPE=plugin, o si hay extras/features opcionales)
      se mueven a una skill reference-only (disable-model-invocation: true, allowed-tools: Read)
    → el agente instruye: "si [condición], leer [skill] y correr esos checks también"
```

**Validado (artifact-factory, 2026-07-01):** validator.md creció de 9 a 13 checks al agregar
soporte para tests/CI/local-files (§16, §19, §20, §32 de esta guía). Split a `validator.md`
(6 checks core) + `validator-checks/SKILL.md` (7 checks condicionales, cargados solo si
TYPE=plugin o hay extras) — bajó el system prompt ~30% sin perder ningún check.

### Plantilla del agente curador

```markdown
---
name: curador
description: Monthly learnings curator. Use when a learnings file exceeds 150
  lines, to deduplicate entries, prune obsolete gotchas, or promote top gotchas
  inline into the correct specialist agent. Run once a month — not every session.
tools: Read, Write, Edit, Glob, Grep
model: haiku
---

# Curador

Mantenimiento mensual de learnings. No correr en cada sesión.

## Cuándo correr
- stop.py reportó que un learnings supera 150 líneas
- Han pasado ~4 semanas desde la última revisión

## Qué hacer
1. Leer todos los archivos de learnings del proyecto
2. Eliminar entradas duplicadas o que dicen lo mismo
3. Archivar entradas obsoletas → `learnings/archive/`
4. Verificar que los top gotchas estén inline en el agente correcto
   (mapear categoría → agente: [LAYOUT]→organisms, [API][STATE]→atoms,
    [SDUI]→sdui, [TOKENS]→tokens, [GOTCHA]→debugger)
5. Si un gotcha frecuente NO está inline → agregarlo al agente
6. Máximo 10 gotchas inline por agente

## Reglas
- No eliminar entradas de las últimas 2 semanas
- No eliminar entradas marcadas [BLOCKER] o [CRÍTICO]
- Siempre archivar, nunca borrar permanentemente
```

---


<!-- §7 -->
<!-- §7-quick -->
## 7. Hooks

> Los hooks son el único mecanismo de garantía real del sistema. Una regla escrita en el prompt del agente es una sugerencia — el agente puede ignorarla. Un hook PreToolUse que bloquea una acción es física pura: el agente no puede ejecutarla aunque quiera. Úsalos para lo que importa de verdad.

### Dónde van

| Contexto | Archivo |
|---|---|
| Proyecto local | `.claude/settings.json` |
| Plugin | `hooks/hooks.json` |

### Formato — `.claude/settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [{"type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/pre_write.py\""}]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/post_bash.py\""}]
      }
    ],
    "SubagentStop": [
      {
        "matcher": "nombre-postmortem",
        "hooks": [{"type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/after_postmortem.py\""}]
      },
      {
        "hooks": [{"type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/subagent_stop.py\""}]
      }
    ],
    "Stop": [
      {
        "hooks": [{"type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/stop.py\""}]
      }
    ]
  }
}
```

Nota: `Stop` y `SubagentStop` sin `matcher` se aplican a todos los casos.

**`command` SIEMPRE con `$CLAUDE_PROJECT_DIR`** — el hook corre con el cwd actual del shell de la sesión, no con la raíz del proyecto. Un `command: "python3 .claude/hooks/x.py"` relativo funciona hasta que un Bash hace `cd` a otro directorio — desde ahí el hook revienta con "can't open file" y bloquea tool calls legítimas. Verificado en vivo 2026-07-02.

**Plugins**: `hooks/hooks.json` usa el MISMO wrapper `{"hooks": {...}}` — eventos al top level se rechazan en silencio y ningún hook se registra. Scripts con `"${CLAUDE_PLUGIN_ROOT}"` (ver §11 Trampas). El matcher de `SubagentStop` para agentes de plugin puede necesitar el nombre con namespace: `(mi-plugin:)?mi-agente`.

### Eventos — los más usados (no es la lista completa)

29 eventos existen en total (verificado 2026-07-04) — acá solo los de uso lowcost. Nicho (agent teams, MCP, worktrees) → §7-ref. `PreCompact`/`PostCompact` → §33.

**Bloqueantes** — corregido 2026-07-04: `Stop`/`SubagentStop` SÍ bloquean (la guía anterior los daba como solo observacionales) — no deniegan una acción, fuerzan que la conversación **continúe** en vez de terminar. Distinto de `PreToolUse`/`UserPromptSubmit`/`PermissionRequest`, que deniegan ANTES de que la acción ocurra:

| Evento | Tipo | Cómo bloquea | Uso típico |
|---|---|---|---|
| `PreToolUse` | Deniega acción | `permissionDecision: deny` + exit 0 | Validar paths, bloquear comandos peligrosos |
| `UserPromptSubmit` | Deniega acción | `decision: block` o exit 2 | Bloquear instrucciones peligrosas, inyectar contexto |
| `PermissionRequest` | Deniega acción | `decision.behavior: deny` | Auto-aprobar comandos seguros conocidos |
| `PostToolBatch` | Fuerza continuar | `decision: block`/exit 2 — para el loop antes del próximo model call | Pausar la próxima tanda si algo salió mal |
| `Stop` | Fuerza continuar | `decision: block`/exit 2 — Claude ignora la parada y sigue | Forzar "no termines hasta que los tests pasen" |
| `SubagentStop` | Fuerza continuar | Mismo mecanismo que `Stop`, scopeado al subagente | Encadenar agentes, exigir un paso más antes de devolver |

**Solo observacionales** — no pueden bloquear nada, solo inyectan contexto con `systemMessage` o `additionalContext`:

| Evento | Matcher | Cuándo dispara | Uso típico |
|---|---|---|---|
| `PostToolUse` | Nombre de tool | Después de que la tool tuvo éxito | Auto-formatear, encadenar acciones, notificar |
| `StopFailure` | Tipo de error | Cuando Claude para por error | Reaccionar a `rate_limit`, `overloaded`, `authentication_failed` |
| `SessionStart` | `startup\|resume\|clear\|compact` | Al iniciar o retomar sesión | Inyectar contexto inicial, `watchPaths`, `reloadSkills` |
| `FileChanged` | Nombre de archivo | Archivo vigilado cambia en disco | Recargar `.env`, disparar validaciones externas |

<!-- §7-ref -->
### Eventos de nicho — no cubiertos arriba

Verificado 2026-07-04 contra la referencia oficial de hooks — 29 eventos existen en total, estos son los que esta guía no desarrolla porque son de casos puntuales (agent teams, MCP elicitation, worktrees, config):

| Evento | Contexto |
|---|---|
| `SessionEnd` | Cleanup al terminar la sesión (no bloquea) |
| `SubagentStart` | Al spawnear un subagente (no bloquea) |
| `TaskCreated` / `TaskCompleted` | Ciclo de vida de tasks vía TaskCreate — bloquean con exit 2 |
| `TeammateIdle` | Agent teams — un teammate por quedar idle, exit 2 lo mantiene trabajando |
| `CwdChanged` | El cwd cambia (ej. un `cd` en Bash) — no bloquea |
| `ConfigChange` | Un archivo de config cambia durante la sesión — bloquea con exit 2 |
| `InstructionsLoaded` | CLAUDE.md o `.claude/rules/*.md` se cargan — no bloquea |
| `PermissionDenied` | Auto-mode deniega una tool — no bloquea, pero soporta `retry: true` |
| `PostToolUseFailure` | Una tool call falla — no bloquea |
| `Elicitation` / `ElicitationResult` | Un MCP server pide input al usuario — bloquea con `action: decline` |
| `WorktreeCreate` / `WorktreeRemove` | Ciclo de vida de worktrees (`--worktree`, isolation) |
| `Notification` / `MessageDisplay` | Solo de UI — nunca bloquean |
| `Setup` | Con flags `--init-only`/`--init`/`--maintenance` — preparación única |
| `UserPromptExpansion` | Un slash command se expande a un prompt — bloquea la expansión |

### Tipos de handler

La guía usa `"type": "command"` (Python/shell) en todos los ejemplos. Existen 3 tipos más:

| Tipo | Cuándo usarlo |
|---|---|
| `"command"` | Script local — el más flexible, cubre el 95% de los casos |
| `"http"` | POST a un servidor externo — webhooks, logging centralizado, CI |
| `"mcp_tool"` | Llama directamente una tool de un servidor MCP ya conectado |
| `"prompt"` | Claude decide sí/no con un prompt — para validaciones en lenguaje natural |

```json
// http hook — logging externo sin script local
{"type": "http", "url": "http://localhost:8080/hooks", "headers": {"Authorization": "Bearer $TOKEN"}}

// prompt hook — validación en lenguaje natural
{"type": "prompt", "prompt": "¿Este comando Bash es seguro para ejecutar en producción? $ARGUMENTS"}
```

### Campos opcionales por hook

```json
{
  "matcher": "Bash",
  "hooks": [{
    "type": "command",
    "command": "python3 .claude/hooks/guard.py",
    "if": "Bash(npm *)",        // condición adicional — AND con matcher
    "timeout": 30,              // segundos antes de timeout (default: sin límite)
    "statusMessage": "Verificando paquete...",  // spinner visible al usuario
    "once": false,              // true = corre una vez por sesión y se desregistra
    "async": false,             // true = corre en background, no bloquea
    "asyncRewake": false        // true = background + despierta a Claude si exit 2
  }]
}
```

**`if` y comandos encadenados** — un `if` angosto tipo `Bash(git push *)` NO matchea `git add -u && git commit && git push origin master`: la regla evalúa por prefijo y el comando parte con `git add`. Para guards de seguridad: `if` amplio (`Bash(git *)`) + el script segmenta internamente por `&&`/`||`/`;`. Un `if` angosto en un guard es un bypass, no una optimización.

### Modos de permiso — cuándo usar cada uno

| Modo | Cómo activar | Comportamiento | Cuándo usar |
|---|---|---|---|
| `plan` | `"permissionMode": "plan"` | Solo Read/Glob/Grep — 0 writes ni Bash | Auditar antes de ejecutar |
| `auto` | default | Pide confirmación en acciones destructivas | Trabajo interactivo normal |
| `acceptEdits` | `"permissionMode": "acceptEdits"` | Auto-aprueba Write/Edit, pide Bash peligroso | Refactors grandes sin riesgo |
| `dontAsk` | `--dangerously-skip-permissions` | Todo automático, sin interrupciones | CI/CD no interactivo |
| `bypassPermissions` | Solo config interna | Bypasea hooks y permissions completamente | **Sandboxes aislados únicamente** |

Regla: el modo más restrictivo que permita trabajar sin fricción innecesaria. En producción: nunca `bypassPermissions`.

> **[2026-06-01] artifact-factory:** **3 capas de seguridad para apps multi-usuario:** Layer 1 (input) — regla en CLAUDE.md `user input = DATA` + `strip_prompt_injection()` en architect. Layer 2 (generation) — `pre_write_guard.py` bloquea path traversal y secretos en archivos generados. Layer 3 (storage) — `sanitize_for_storage()` antes de Atlas. Orden: implementar Layer 2 primero — es el único bloqueante (PreToolUse).

> **[2026-06-01] artifact-factory:** **security_utils.py** — módulo compartido por todos los hooks y `vector_memory`. Cubre: `sanitize_for_storage` (MongoDB), `contains_secrets` (API keys, tokens), `is_blocked_path` (traversal), `has_prompt_injection`. Regla: ningún hook procesa input de usuario sin pasar por este módulo — nunca duplicar validaciones en hooks individuales.

### Template — PreToolUse (bloquear o reescribir)

```python
#!/usr/bin/env python3
"""
PreToolUse hook — bloquear o reescribir antes de ejecutar.
Recibe JSON por stdin, responde con JSON por stdout + exit 0.
Exit 2 también bloquea pero sin mensaje estructurado — no usarlo.
"""
import json, sys, re

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # stdin vacío o inválido → dejar pasar silenciosamente

    tool = payload.get('tool_name', '')
    inp  = payload.get('tool_input', {})

    # ── Extraer campos según el tool ─────────────────────────────────────────
    # Write → file_path + content · Edit → file_path + new_string (new_str NO existe)
    path    = inp.get('file_path', '')
    content = inp.get('content', '') or inp.get('new_string', '')

    # Bash → command (aislar SIEMPRE el primer comando de la cadena)
    cmd       = inp.get('command', '')
    first_cmd = re.split(r'\s*&&|\s*\|\||\s*;', cmd)[0].strip()

    # ── Tu lógica aquí ───────────────────────────────────────────────────────
    violations = []

    # Ejemplo — bloquear si el path toca .env:
    # if '.env' in path:
    #     violations.append("No escribir en archivos .env — usar variables de entorno")

    # Ejemplo — bloquear comando peligroso:
    # if re.match(r'rm\s+-rf\s+/', first_cmd):
    #     violations.append("rm -rf en ruta absoluta bloqueado")

    # ── Respuesta ─────────────────────────────────────────────────────────────
    if not violations:
        sys.exit(0)  # sin violaciones → dejar pasar

    # BLOQUEAR con mensaje visible al usuario:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",        # deny | allow | ask | defer
            "permissionDecisionReason": "\n".join(violations)
        }
    }))
    sys.exit(0)

    # ALTERNATIVA — reescribir el input en vez de bloquear:
    # print(json.dumps({
    #     "hookSpecificOutput": {
    #         "hookEventName": "PreToolUse",
    #         "updatedInput": {"command": cmd.replace("npm install", "npm ci")},
    #         "additionalContext": "Reescrito para garantizar reproducibilidad."
    #     }
    # }))
    # sys.exit(0)

if __name__ == '__main__':
    main()
```

### PostToolUse — encadenar con `systemMessage`

Para hooks que reaccionan a acciones específicas (como hacer checkout a master después de un merge):

```python
#!/usr/bin/env python3
import json, sys, subprocess

data = json.load(sys.stdin)
cmd = data.get("tool_input", {}).get("command", "")

if "gh pr merge" not in cmd:
    sys.exit(0)

subprocess.run(["git", "checkout", "master"])
subprocess.run(["git", "pull", "origin", "master"])
print(json.dumps({"systemMessage": "Cambiado a master y actualizado."}))
```

### SubagentStop — notificar con `systemMessage`

Usar JSON con `systemMessage` en vez de `echo` directo — la UI lo muestra limpiamente y el texto no contamina stdout del proceso:

```python
#!/usr/bin/env python3
import json, sys

data = json.load(sys.stdin)
# El payload de SubagentStop trae agent_type (docs oficiales) — subagent_type
# como fallback defensivo. Leer agent_name/subagent_name falla siempre.
agent = data.get("agent_type", "") or data.get("subagent_type", "")

messages = {
    "mi-scene-agent": "Escena modificada. Invocar @reviewer antes de continuar.",
    "mi-script-agent": "Script modificado. Invocar @reviewer antes de continuar.",
}

msg = messages.get(agent)
if msg:
    print(json.dumps({"systemMessage": msg}))
```

### Guard hook — bloquear comandos peligrosos

Para bloquear acciones irreversibles independientemente de lo que diga el agente:

```python
#!/usr/bin/env python3
import json, sys, re

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    cmd = payload.get("tool_input", {}).get("command", "")

    # CRÍTICO: chequear solo el primer comando de la cadena.
    # cmd puede ser "git push origin rama && gh pr create --body '...master...'"
    # Un check naive "in cmd" matchearía el texto del --body como falso positivo.
    first_cmd = re.split(r'\s*&&|\s*\|\||\s*;', cmd)[0].strip()

    blocked = (
        re.search(r'git\s+push\s+(?:[\w-]+\s+)*origin\s+master\b', first_cmd) is not None or
        re.search(r'git\s+push\s+--force\b', first_cmd) is not None or
        re.search(r'git\s+push\s+-f\b', first_cmd) is not None
    )

    if not blocked:
        sys.exit(0)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Push directo a master bloqueado.\n"
                "Flujo correcto: gh pr create → gh pr merge <N> --merge"
            )
        }
    }))
    sys.exit(0)

if __name__ == "__main__":
    main()
```

Registrar en `settings.json` con `if` para no spawnearlo en cada Bash:

```json
{
  "matcher": "Bash",
  "hooks": [{
    "type": "command",
    "command": "python3 .claude/hooks/pre_push_guard.py",
    "if": "Bash(git push *)"
  }]
}
```

### Hook de tests antes de crear un PR

Bloquear `gh pr create` si los tests fallan:

```python
#!/usr/bin/env python3
import json, sys, subprocess, os

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    cmd = payload.get("tool_input", {}).get("command", "")
    if "gh pr create" not in cmd:
        sys.exit(0)

    # No bloquear si no hay tests
    if not os.path.isdir("tests") or not os.listdir("tests"):
        sys.exit(0)

    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", "tests/", "-q", "--tb=no"],
            capture_output=True, text=True, timeout=120
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        sys.exit(0)  # Si pytest no existe o tarda mucho, no bloquear

    if result.returncode != 0:
        failures = [l for l in result.stdout.splitlines() if "FAILED" in l or "ERROR" in l]
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Tests fallaron:\n" + "\n".join(failures[:10])
            }
        }))
    sys.exit(0)

if __name__ == "__main__":
    main()
```

```json
{
  "matcher": "Bash",
  "hooks": [{
    "type": "command",
    "command": "python3 .claude/hooks/pre_pr_create.py",
    "if": "Bash(gh pr create *)",
    "timeout": 120,
    "statusMessage": "Corriendo tests antes del PR..."
  }]
}
```

**Reglas:**
- `chmod +x` en todos los scripts
- `try/except` en **todos** los hooks (PreToolUse, PostToolUse, SubagentStop, Stop) — no solo PreToolUse
- PreToolUse bloquea con JSON `permissionDecision: deny` + exit 0 — nunca `exit(2)` directo (exit 2 bloquea pero sin razón estructurada; cualquier exit distinto de 0 y 2 muestra la primera línea de stderr como error no-bloqueante y la acción continúa igual)
- SubagentStop y PostToolUse usan `systemMessage` — nunca `echo` crudo
- Checks de string en comandos Bash: usar `re.split` para aislar el primer comando — nunca `"texto" in cmd` directo (matchea argumentos como `--body`)
- Paths del proyecto: `Path(__file__).parent.parent.parent` — nunca paths absolutos hardcodeados
- SubagentStop de agentes pesados (postmortem, lead): mostrar `systemMessage` de confirmación — nunca silencio

### Paths en hooks — nunca absolutos

Los hooks viven en `.claude/hooks/`. Para referenciar la raíz del proyecto:

```python
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.parent  # hooks/ → .claude/ → repo/
```

Un path como `cwd="/Users/nombre/Desktop/proyecto"` rompe si el proyecto se mueve o se clona en otra máquina.

### Campos de payload por tool — verificar, nunca recordar

Los nombres reales de los campos (verificados 2026-07-02 — versiones anteriores de esta guía tenían `path`/`new_str`, que NO existen):

| Tool | Campos de `tool_input` |
|---|---|
| `Write` | `file_path`, `content` |
| `Edit` | `file_path`, `old_string`, `new_string` |
| `MultiEdit` (legacy) | `file_path`, `edits[].old_string`, `edits[].new_string` |
| `Bash` | `command` |

```python
if tool == 'Edit':
    path, content = inp.get('file_path', ''), inp.get('new_string', '') or ''
elif tool == 'MultiEdit':
    path = inp.get('file_path', '')
    content = '\n'.join(e.get('new_string', '') for e in inp.get('edits', []) if isinstance(e, dict))
```

Un campo equivocado no da error: `inp.get('path', '')` retorna `''`, el filtro de extensión no matchea, `sys.exit(0)` — **el hook queda muerto y se ve idéntico a uno sano**. Caso real MathVoid: el gate de convenciones GDScript estuvo semanas validando solo Write porque leía `path`/`new_str` en Edit — con tests verdes, porque los tests alimentaban el mismo shape inventado. Regla: los campos del payload se copian de la doc oficial de hooks o de un payload real capturado, nunca de memoria.

### Testing de hooks localmente

Antes de registrar un hook, testearlo manualmente para no esperar a que el agente lo dispare:

```bash
# PreToolUse — simular git push bloqueado
echo '{"tool_name": "Bash", "tool_input": {"command": "git push origin master"}}' \
  | python3 .claude/hooks/pre_push_guard.py

# SubagentStop — simular fin de agente (el campo real es agent_type, NO subagent_type)
echo '{"agent_type": "implementador"}' \
  | python3 .claude/hooks/subagent_stop_reviewer.py

# Verificar formato JSON del output
echo '{"tool_name": "Bash", "tool_input": {"command": "git push origin master"}}' \
  | python3 .claude/hooks/pre_push_guard.py | python3 -m json.tool
```

Si el hook no imprime nada → exit 0 silencioso (correcto). Si imprime JSON con `permissionDecision: deny` → bloqueo activo.

### Diagnóstico de hooks silenciosos

Un hook que falla sin error visible es difícil de debuggear. Checklist en orden de probabilidad:

```
□ ¿El script tiene permisos de ejecución?
  ls -la .claude/hooks/
  chmod +x .claude/hooks/*.py

□ ¿El matcher coincide con el tool name exacto?
  Tool names: "Bash", "Write", "Edit", "MultiEdit", "Read"
  Un matcher "bash" (minúscula) nunca dispara.

□ ¿El output JSON es válido?
  echo '{"tool_name":"Bash","tool_input":{"command":"test"}}' \
    | python3 .claude/hooks/mi_hook.py | python3 -m json.tool

□ ¿El SubagentStop matcher coincide con el `name:` del agente?
  El matcher busca el campo `name:` del frontmatter, no la `description`.
  "my-postmortem" ✅   "My Postmortem" ❌

□ ¿El script crashea silenciosamente?
  python3 .claude/hooks/mi_hook.py < /dev/null
  Si retorna exit code != 0 → hay un error que no se ve en producción.

□ ¿El `if` condition del settings.json usa el glob correcto?
  "if": "Bash(git push *)" no matchea "git add && git push" (evalúa por prefijo).
  Guards: `if` amplio + segmentar dentro del script.

□ ¿Los campos del payload existen de verdad?
  Edit → file_path/new_string (no path/new_str) · SubagentStop → agent_type (no subagent_type).
  Un .get() de campo inexistente = '' = exit 0 = hook muerto que se ve sano.
  Copiar de la doc oficial o capturar un payload real — nunca de memoria.

□ ¿El `command` usa ruta relativa?
  "python3 .claude/hooks/x.py" rompe cuando el shell hace cd.
  Siempre: python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/x.py"
```

**Los guards PreToolUse solo ven las tools de Claude.** Un subproceso lanzado por OTRO hook (ej. un Stop hook que hace `git push` vía subprocess) no pasa por ningún guard — si un hook necesita la excepción, validarla dentro del propio hook (ej. push a master permitido solo si el commit toca exclusivamente `.claude/`).

### updatedInput — reescribir en vez de bloquear

`updatedInput` es más potente que `deny`: en vez de rechazar la acción, la corrige silenciosamente antes de ejecutar. El agente no sabe que el comando cambió.

```python
# Ejemplo: npm install sin args → reescribir a npm ci automáticamente
import json, sys, re

data = json.load(sys.stdin)
cmd  = data.get("tool_input", {}).get("command", "")
first = re.split(r'\s*&&|\s*\|\||\s*;', cmd)[0].strip()

if re.match(r'npm\s+install\s*$', first):
    new_cmd = cmd.replace(first, 'npm ci', 1)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",       # updatedInput acompaña a "allow"
            "updatedInput": {"command": new_cmd},
            "additionalContext": "npm install reescrito a npm ci — usa lockfile exacto y no modifica package-lock.json."
        }
    }))
    sys.exit(0)

sys.exit(0)
```

> ⚠️ `updatedInput` es un campo hermano de `permissionDecision` — NUNCA su valor. `"permissionDecision": "updatedInput"` es inválido y el auto-fix no aplica (falla en silencio: la acción pasa sin corregir). Valores válidos: `allow | deny | ask | defer`.

### El compilador como juez — PostToolUse + parser real

Los regex de convenciones no saben si el código es válido. Un PostToolUse que corre el parser real del lenguaje sobre el archivo **ya escrito en disco** devuelve el error a Claude en el mismo turno — fix inmediato, sin round-trip por el IDE. Cero falsos positivos por definición.

```python
# post_write.py — swiftc -parse: solo sintaxis, sin type-checking ni deps (<1s)
def parse_check(path):
    if not path.endswith('.swift') or not shutil.which('swiftc'):
        return None                       # sin toolchain → skip silencioso
    try:
        r = subprocess.run(['swiftc', '-parse', path],
                           capture_output=True, text=True, timeout=15)
    except Exception:
        return None                       # el hook nunca rompe la sesión
    return None if r.returncode == 0 else '\n'.join(r.stderr.splitlines()[:15])

errors = parse_check(path)
if errors:
    print(json.dumps({"decision": "block",
                      "reason": f"⛔ swiftc -parse falló — corregir ahora:\n{errors}"}))
```

Claves: va en **Post**, no Pre (en PreToolUse solo tienes el fragmento del Edit — la sintaxis se valida sobre el archivo completo); `decision: "block"` en PostToolUse devuelve la razón a Claude; atrapa la clase de error más frecuente del modelo (braces desbalanceados, edits que cortan código a la mitad). Equivalentes: `python -m py_compile`, `node --check`, `tsc --noEmit` (este último sí es lento — medir antes).

### Gates sobre prompts del usuario — reglas de fragilidad

Un deny-gate alimentado por regex sobre lenguaje natural es plomería frágil. Tres reglas para que sobreviva:

1. **Anclar confirmaciones al inicio**: `^\s*(ok|sí|dale|...)\b` — "bien, pero antes explícame X" no debe aprobar
2. **Scope por directorios conocidos** (config tipo `design-paths.json`), no "todo archivo `.ext` del repo" — un fix de 1 línea fuera del dominio no debe exigir plan
3. **Degradar a warnings sin setup**: si falta la config de scope, informar sin bloquear — un gate que estorba se termina desactivando entero

> El agente recibe `npm ci` como si él lo hubiera escrito. `additionalContext` le explica el cambio en el próximo turno.

### SessionStart — inyectar contexto al iniciar

`SessionStart` dispara antes de que Claude procese el primer mensaje. Útil para cargar estado externo (branch actual, tickets abiertos, env activo) sin que el usuario tenga que pegarlo.

```python
#!/usr/bin/env python3
import json, sys, subprocess

data = json.load(sys.stdin)
if data.get("source") not in ("startup", "resume"):
    sys.exit(0)

try:
    branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
    status = subprocess.check_output(["git", "status", "--short"], text=True).strip()
    context = f"Branch: {branch}"
    if status:
        context += f"\nArchivos modificados:\n{status}"
except Exception:
    context = "Git no disponible en este directorio."

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": context
    }
}))
```

```json
{"SessionStart": [{"matcher": "startup|resume", "hooks": [{"type": "command", "command": "python3 .claude/hooks/session_start.py"}]}]}
```

### npm security guard — supply chain y slopsquatting

> **Analogía:** `npm install <paquete>` es como contratar a un empleado nuevo sin verificar referencias — el postinstall script puede ejecutar código arbitrario desde el momento en que llega. `npm ci` es contratar a alguien ya verificado (lockfile exacto). `npx` es dejar que el empleado traiga a sus amigos sin presentarlos.

**Riesgo específico para Claude Code — slopsquatting:** atacantes publican paquetes con nombres que los modelos de AI tienden a alucinar. Si Claude sugiere `import` de un paquete que no existe y el agente hace `npm install` directamente, el paquete malicioso ya está instalado.

```python
#!/usr/bin/env python3
import json, sys, re

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    cmd   = data.get("tool_input", {}).get("command", "")
    first = re.split(r'\s*&&|\s*\|\||\s*;', cmd)[0].strip()

    # npx desde registry = descarga + ejecuta sin verificación de integridad
    if re.match(r'npx\s+[^./]', first):
        pkg = first.split()[1]
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"npx {pkg} descarga y ejecuta código sin verificación.\n"
                "Riesgo slopsquatting: el paquete puede no existir y un atacante haberlo publicado.\n"
                f"Alternativa: npm install {pkg} --ignore-scripts && verificar con npm view {pkg}"
            )
        }}))
        sys.exit(0)

    # npm install <paquete> sin --ignore-scripts = lifecycle scripts sin control
    m = re.match(r'npm\s+(?:i|install)\s+(\S+)', first)
    if m and not m.group(1).startswith('-') and '--ignore-scripts' not in first:
        pkg = m.group(1)
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"npm install {pkg} ejecuta lifecycle scripts (postinstall) automáticamente.\n"
                "Riesgo: supply chain attack — el paquete puede exfiltrar credenciales al instalarse.\n"
                f"Alternativa: npm install {pkg} --ignore-scripts\n"
                f"Verificar antes: npm view {pkg} repository"
            )
        }}))
        sys.exit(0)

    # npm install sin args → reescribir a npm ci (reproducible, no modifica lockfile)
    if re.match(r'npm\s+(?:i|install)\s*$', first):
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
            "updatedInput": {"command": cmd.replace(first, 'npm ci', 1)},
            "additionalContext": "npm install reescrito a npm ci — garantiza reproducibilidad y no modifica package-lock.json."
        }}))
        sys.exit(0)

    sys.exit(0)

if __name__ == '__main__':
    main()
```

```json
{"PreToolUse": [{"matcher": "Bash", "if": "Bash(npm *)", "hooks": [{"type": "command",
  "command": "python3 .claude/hooks/npm_guard.py", "statusMessage": "Verificando comando npm..."}]}]}
```

**Qué cubre este hook:**

| Comando | Acción del hook | Por qué |
|---|---|---|
| `npx <paquete>` | Bloquea + explica slopsquatting | Descarga y ejecuta sin verificación |
| `npm install <pkg>` | Bloquea + sugiere `--ignore-scripts` | Lifecycle scripts pueden ser maliciosos |
| `npm install` | Reescribe a `npm ci` | Reproducible, no modifica lockfile |
| `npm ci` | Permite sin intervención | Seguro por diseño |
| `npm install <pkg> --ignore-scripts` | Permite | Usuario optó explícitamente |

### Routing por complejidad — modelo según tarea

`UserPromptSubmit` detecta complejidad en el prompt e inyecta una recomendación de modelo antes de que Claude planifique. 0 tokens si no hay match. Opera junto al hook de §26 sin conflicto — ambos usan `UserPromptSubmit` y coexisten.

```python
#!/usr/bin/env python3
import json, sys

COMPLEXITY_MAP = [
    (["typo", "rename", "format", "lint", "mover", "copiar"],
     "claude-haiku-4-5", None, "simple"),
    (["bug", "fix", "test", "feature", "añadir", "agregar", "refactor"],
     "claude-sonnet-5", "medium", "media"),
    (["arquitectura", "diseño", "migración", "seguridad", "critico", "critical"],
     "claude-sonnet-5", "xhigh", "compleja"),
    (["irreversible", "producción", "production"],
     "claude-opus-4-8", None, "crítica"),
]

try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)

p = payload.get("prompt", "").lower()
for keywords, model, effort, label in COMPLEXITY_MAP:
    if any(k in p for k in keywords):
        effort_str = f" · effort: {effort}" if effort else ""
        print(f"[Model hint — complejidad {label}] model: {model}{effort_str}")
        sys.exit(0)
```

```json
{"UserPromptSubmit": [{"hooks": [{"type": "command", "command": "python3 .claude/hooks/complexity_router.py"}]}]}
```

**Alcance:** la recomendación llega a Claude como contexto — la usa al lanzar subagentes. No cambia el modelo del CLI (para eso: `/model`).

| Keyword detectada | Modelo | Effort |
|---|---|---|
| typo, rename, format, lint | haiku | — |
| bug, fix, feature, test | sonnet | medium |
| arquitectura, diseño, seguridad | sonnet | xhigh |
| irreversible, producción | opus | — |

### Secret detection guard — credenciales en archivos

La implementación canónica es `pre_write_guard.py` + `security_utils.py` → **§18 Layer 2** (bloquea secretos Y path traversal en Write/Edit/MultiEdit con un solo hook). No duplicar un secret guard aparte: dos guards con patterns propios divergen — el de §18 es la única casa.

### PermissionRequest — auto-aprobar acciones conocidas

Reduce interrupciones aprobando herramientas y comandos read-only automáticamente, sin afectar el control sobre acciones destructivas.

```python
#!/usr/bin/env python3
import json, sys, re

AUTO_APPROVE_TOOLS = {'Read', 'Glob', 'Grep', 'LS'}

SAFE_BASH_PATTERNS = [
    r'^git\s+(status|log|diff|branch|show|fetch)',
    r'^ls\b', r'^cat\b', r'^echo\b',
    r'^python3?\s+-m\s+pytest\b',
    r'^npm\s+(test|run\s+lint|run\s+build)\b',
]

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool = data.get('tool_name', '')

    if tool in AUTO_APPROVE_TOOLS:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PermissionRequest",
            "permissionDecision": "allow"}}))
        sys.exit(0)

    if tool == 'Bash':
        cmd   = data.get('tool_input', {}).get('command', '')
        first = re.split(r'\s*&&|\s*\|\||\s*;', cmd)[0].strip()
        if any(re.match(p, first) for p in SAFE_BASH_PATTERNS):
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PermissionRequest",
                "permissionDecision": "allow"}}))
            sys.exit(0)

    sys.exit(0)  # → pedir al usuario (default)

if __name__ == '__main__':
    main()
```

```json
{"PermissionRequest": [{"hooks": [{"type": "command",
  "command": "python3 .claude/hooks/permission_request.py"}]}]}
```

Cuándo extender `AUTO_APPROVE_TOOLS`: solo cuando el comando es objetivamente read-only y se ejecuta frecuentemente. Nunca auto-aprobar `Write`, `Bash(rm *)` ni pushes.

---


<!-- §6 -->
<!-- §6-quick -->
## 6. Skills

> Una skill es un recetario: no cocina sola, pero cuando el agente la necesita la consulta. La diferencia con un agente es que no tiene contexto propio — comparte el hilo principal. Úsalas para referencia, templates y triage. Nunca para código que se ejecuta.

### Cuándo crear una skill

La pregunta no es "¿puedo hacer esto con una skill?" — es "¿dónde vive mejor este contenido?"

| Contenido | Dónde va | Por qué |
|---|---|---|
| Regla que aplica **siempre**, en toda tarea | `CLAUDE.md` | Costo fijo justificado — es el contrato del restaurante en la pared |
| Procedimiento que se carga **bajo demanda** | Skill | Gratis en tokens hasta que se invoca — el menú del día |
| Tarea con **contexto propio** o que contaminaría el hilo | Agente (`context: fork`) | El sous-chef trabaja en su cocina aparte — el hilo principal no se ensucia |

**Trigger práctico (oficial):** creá una skill cuando seguís pegando las mismas instrucciones en el chat, o cuando una sección de CLAUDE.md creció hasta ser un procedimiento en vez de un hecho.

```
CLAUDE.md tiene ≥ 5 líneas sobre cómo hacer X  →  mover X a una skill
Pegaste las mismas instrucciones más de 2 veces  →  skill de referencia
La tarea contamina el hilo con logs/diffs largos →  skill con context: fork
```

### Templates por tipo de skill

**Hub** — dispatch automático, siempre visible para Claude:
```markdown
---
name: <proyecto>-hub
description: "<Proyecto> dispatch. [caso A] → @<agente-a> | [caso B] → @<agente-b>."
disable-model-invocation: false     # Claude lo activa solo — descripción siempre en contexto
allowed-tools: Read
---

# <Proyecto> — Dispatch
| Tarea | Agente | Cuándo |
|---|---|---|
| <tarea-1> | @<agente> | <condición> |
| <tarea-2> | @<agente> | <condición> |
```
> Límite: < 40 líneas. Si CLAUDE.md ya tiene el dispatch, ocultarla del menú `/` sin tocar el SKILL.md — **`skillOverrides` va en `.claude/settings.json`, NO en el frontmatter** (corregido 2026-07-04, error fácil: escribirlo en el SKILL.md no falla, simplemente no hace nada): `{"skillOverrides": {"<proyecto>-hub": "user-invocable-only"}}`.

---

**Referencia** — conocimiento bajo demanda, invisible hasta que se invoca:
```markdown
---
name: <dominio>-conventions
description: "<Qué contiene>. Cargar cuando: <condición concreta>."
disable-model-invocation: true      # Claude no lo activa — gratis en tokens hasta que el usuario lo pide
allowed-tools: []
---

<Convenciones, patrones, API — sin prosa de relleno>
```
> Límite: < 200 líneas. Si supera → dividir en `SKILL.md` + `reference.md`.

---

**Fork** — tarea aislada en subagente, no contamina el hilo:
```markdown
---
name: <tarea>-research
description: "<Qué investiga>. Usar cuando la tarea lee > 3 archivos o produce output voluminoso."
disable-model-invocation: false
context: fork
agent: Explore                      # solo lectura, no carga CLAUDE.md — contexto limpio y económico
---

Investigar $ARGUMENTS:
1. <paso concreto con Glob/Grep>
2. <paso concreto con Read>
3. Resumir hallazgos con referencias exactas de archivo:línea
```

<!-- §6-ref -->
---

**Librería interna** — invocada solo por otra skill o agente, nunca directamente:
```markdown
---
name: <dominio>-lib
description: "<Qué contiene> — uso interno del hub, no invocar directamente."
disable-model-invocation: true   # el modelo no la ve ni la activa sola
user-invocable: false            # el usuario no puede /nombre
allowed-tools: []
---

<Contenido compartido entre skills — convenciones, mapas, constantes>
```
> Solo tiene sentido si otra skill o CLAUDE.md la menciona por nombre explícitamente. Sin esa referencia, es inalcanzable.

### Tipos y configuración

| Tipo | `disable-model-invocation` | Tamaño | Qué ve Claude en contexto |
|---|---|---|---|
| Hub / dispatch | `false` | < 40 líneas | Nombre + descripción siempre visibles — triage automático |
| Referencia | `true` | < 200 líneas | **Nada** — ni nombre ni descripción — Claude no sabe que existe hasta que el usuario la invoca |
| Template | `true` | Sin límite práctico | **Nada** — igual que referencia, nunca en contexto activo |

> **Analogía:** `disable-model-invocation: true` no es "no activar" — es quitar la etiqueta del estante. El recetario sigue ahí, pero Claude no sabe ni que existe. Un hub con `false` es el libro de recetas abierto en la cocina — visible siempre. Una skill de referencia con `true` es el manual técnico en el cajón — gratis en tokens hasta que alguien lo pide.

### Los dos ejes de visibilidad

Son flags independientes en el frontmatter — cada uno controla un eje distinto:

| Flag | Eje que controla | `true` = |
|---|---|---|
| `disable-model-invocation` | Si el **modelo** puede auto-invocarla | El modelo no ve nombre ni descripción — la skill no existe para él |
| `user-invocable` | Si el **usuario** puede `/nombre` | No aparece en autocomplete — el usuario no puede invocarla directamente |

**Las 4 combinaciones:**

| `disable-model-invocation` | `user-invocable` | Patrón | Quién la activa |
|---|---|---|---|
| `false` | `true` (omitir) | Hub / dispatch | Modelo o usuario |
| `true` | `true` (omitir) | Referencia | Solo el usuario con `/nombre` |
| `false` | `false` | Auto-cargada | Solo el modelo — el usuario no puede sobreescribir |
| `true` | `false` | Librería interna | Solo otra skill/agente que la nombre explícitamente |

> La combinación `disable-model-invocation: true` + `user-invocable: false` es el "ingrediente secreto" en la alacena: ni el cocinero principal ni el cliente lo ven en el menú. Solo el sous-chef que sabe que existe lo busca directamente.

**Cuándo usar `user-invocable: false`:** cuando la skill es un componente interno (convenciones compartidas, mapas de constantes) que no debe aparecer como comando disponible para el usuario, pero que el hub o CLAUDE.md referencian por nombre. Sin esa referencia explícita, la skill es inalcanzable.

> `skillOverrides` en `settings.json` sobreescribe estos flags en runtime sin editar el archivo — útil para desactivar una skill en un proyecto específico sin tocar el plugin.

### Controlar cuándo una skill se activa — `skillOverrides`

Por defecto, el modelo puede invocar cualquier skill según su `description`. Para controlar esto:

```json
// .claude/settings.json
{
  "skillOverrides": {
    "mi-hub": "user-invocable-only",
    "mi-referencia": "off"
  }
}
```

| Valor | Claude la ve | Usuario puede `/nombre` | Analogía |
|---|---|---|---|
| `"on"` (default) | Nombre + descripción | Sí | Recetario en la repisa con etiqueta y resumen — Claude sabe cuándo abrirlo |
| `"name-only"` | Solo el nombre | Sí | Recetario con solo el título — Claude sabe que existe pero no cuándo usarlo |
| `"user-invocable-only"` | Nada | Sí | Recetario en el cajón — el cocinero (usuario) lo busca, el modelo no lo ve |
| `"off"` | Nada | No | Recetario en el sótano — nadie lo ve, cero tokens |

**Cuándo usar `user-invocable-only` en el hub:**
Si CLAUDE.md ya contiene la tabla de dispatch completa, el hub es redundante para el modelo. Desactivar el auto-trigger evita un LLM call innecesario (~280 tokens) por cada tarea sin perder la skill para uso manual.

```json
// hub innecesario si CLAUDE.md ya tiene el dispatch
"skillOverrides": {
  "mi-hub": "user-invocable-only"
}
```

**Cuándo usar `"off"` — limpiar skills que ya no se usan:**
Una skill con `"on"` (default) consume tokens en el system prompt aunque nunca se active. Si una skill quedó obsoleta o fue reemplazada por otra, ponerla en `"off"` en vez de borrar el archivo:

```json
"skillOverrides": {
  "mi-skill-vieja": "off",        // obsoleta — invisible para todos
  "mi-skill-reemplazada": "off"   // reemplazada por mi-skill-nueva
}
```

Ventaja sobre borrar: el archivo sigue existiendo como referencia histórica, pero no consume tokens.

### Lifecycle — qué pasa después de invocar una skill

Una skill invocada entra al contexto como un mensaje y **se queda toda la sesión** — Claude no vuelve a leer el archivo. Es el pan de ajo en la mesa: una vez que llega, se queda hasta que te vas.

Auto-compaction reencuaderna las skills más recientes con un budget de **5,000 tokens por skill, 25,000 tokens compartidos**. Si invocaste muchas skills, las más antiguas se caen primero. Señal de problema: la skill "deja de funcionar" después de mucho intercambio — re-invocarla con `/nombre` la restaura.

```
□ Skill grande (> 200 líneas) → dividir en SKILL.md + reference.md cargado bajo demanda
□ Skill que "se olvidó" → re-invocar con /nombre después de auto-compact
□ Muchas skills en una sesión → usar name-only en las menos críticas para liberar budget
```

### Skill ↔ Agente — árbol de decisión

> Skill y agente usan el mismo mecanismo por debajo. La diferencia es quién dirige: si la skill elige el agente (`context: fork`), la skill controla. Si el agente precarga skills (`skills:`), el agente controla.

```
¿El trabajo contaminaría el hilo principal con output voluminoso?
├── No → Skill (comparte contexto)
│       ¿Necesita tools propias o razonamiento prolongado?
│       ├── No → Skill regular (referencia / hub / fork-ligero)
│       └── Sí → Skill con context: fork + agent: Explore
│                (skill elige el agente, su contenido = la tarea)
└── Sí → Agente (contexto propio aislado)
        ¿Siempre necesita cierto conocimiento de referencia al arrancar?
        ├── No → Agente regular
        └── Sí → Agente con skills: [skill-name]
                 (agente precarga skill content, no lo descubre en runtime)
```

**Los 4 patrones con sus casos de uso:**

| Patrón | Cuándo | Cómo |
|---|---|---|
| Skill regular | Referencia, convenciones, triage — comparte hilo | `disable-model-invocation: true/false` sin `context:` |
| Skill con `context: fork` | Trabajo pesado que ensuciaría el hilo (diffs largos, búsquedas) | `context: fork` + `agent: Explore` en SKILL.md |
| Agente regular | Tarea multi-step con contexto propio | `.claude/agents/<nombre>.md` sin `skills:` |
| Agente con `skills:` | Agente que siempre necesita convenciones al arrancar | `skills: [api-conventions, error-patterns]` en frontmatter |

**La nota clave de la doc oficial:**
> *"Con `skills:` en un agente, el agente controla el sistema prompt y carga el contenido de la skill. Con `context: fork` en una skill, el contenido de la skill se inyecta en el agente elegido. Ambos usan el mismo mecanismo subyacente."*

### Ejemplos — los 4 patrones en código

**Patrón 1 — Skill regular (referencia, comparte hilo):**
```yaml
# .claude/skills/api-conventions/SKILL.md
---
name: api-conventions
description: "Convenciones de API REST del proyecto. Cargar cuando se implementan endpoints."
disable-model-invocation: true   # Claude no la activa sola — cero tokens hasta que el usuario la pide
allowed-tools: []
---
Cuando escribas endpoints:
- Usar kebab-case en rutas: /user-profiles, no /userProfiles
- Errores siempre con {error: string, code: string}
- Paginación con ?page=&limit= (max 100)
```

**Patrón 2 — Skill con `context: fork` (tarea aislada, skill dirige):**
```yaml
# .claude/skills/audit-deps/SKILL.md
---
name: audit-deps
description: "Auditar dependencias del proyecto. Usar cuando el usuario pide revisar paquetes o seguridad de dependencias."
context: fork
agent: Explore             # solo lectura — no carga CLAUDE.md, contexto limpio
---
Auditar dependencias de $ARGUMENTS o del proyecto completo si no se especifica:
1. Leer package.json y package-lock.json
2. Identificar paquetes con versiones pinned vs ranges
3. Buscar paquetes deprecados o sin mantenimiento (último commit > 2 años)
4. Reportar: paquete · versión actual · riesgo · acción recomendada
```
> La skill dirige: elige el agente (`Explore`), su contenido se convierte en la tarea del subagente. El hilo principal recibe solo el resumen.

**Patrón 3 — Agente regular (contexto propio, sin skills precargadas):**
```yaml
# .claude/agents/implementador.md
---
name: implementador
description: "Implementa features según el scope del sistema activo. Usar cuando hay una tarea concreta de código definida."
model: sonnet
tools: Read, Write, Edit, Glob, Grep
---
Implementar la tarea recibida siguiendo las convenciones del proyecto.
Si necesitás convenciones de API → invocar /api-conventions antes de empezar.
```

**Patrón 4 — Agente con `skills:` (contexto propio + conocimiento precargado):**
```yaml
# .claude/agents/api-developer.md
---
name: api-developer
description: "Implementa endpoints REST siguiendo las convenciones del proyecto. Usar cuando el task involucra crear o modificar endpoints."
model: sonnet
tools: Read, Write, Edit, Glob, Grep
skills:
  - api-conventions        # inyectado al arrancar — el agente ya sabe las convenciones
  - error-handling-patterns
---
Implementar el endpoint descrito. Las convenciones ya están cargadas en contexto — no hace falta invocar /api-conventions.
```
> El agente dirige: controla su propio sistema prompt y precarga el contenido de las skills al iniciar. No necesita descubrirlas en runtime. Solo funciona con skills que tienen `disable-model-invocation: false`.

**¿Cuándo elegir Patrón 3 vs Patrón 4?**
- Patrón 3 si las convenciones cambian frecuentemente o el agente no siempre las necesita
- Patrón 4 si el agente **siempre** trabaja en el mismo dominio y las convenciones son estables — evita que el agente tenga que invocar la skill manualmente en cada sesión

### Frontmatter completo — todos los campos

| Campo | Default | Uso |
|---|---|---|
| `name` | nombre del directorio | Display en listado — no cambia el comando `/` |
| `description` | primer párrafo | Trigger de activación automática. **Primero el caso más importante.** |
| `when_to_use` | — | Contexto adicional — se suma a `description` hacia el límite de 1,536 chars |
| `argument-hint` | — | Hint en autocompletado: `[issue-number]`, `[archivo] [formato]` |
| `arguments` | — | Nombres para `$name` substitution: `arguments: [issue, branch]` |
| `disable-model-invocation` | `false` | `true` = quita la etiqueta del estante — Claude no sabe que existe |
| `user-invocable` | `true` | `false` = oculta del menú `/` — Claude puede invocarla, el usuario no |
| `allowed-tools` | — | Tools sin prompt de permiso mientras la skill está activa |
| `disallowed-tools` | — | Tools bloqueadas mientras la skill está activa (se limpia al próximo mensaje) |
| `model` | hereda sesión | Override de modelo **solo para este turno** |
| `effort` | hereda sesión | Override de esfuerzo: `low\|medium\|high\|xhigh\|max` |
| `context` | — | `fork` = corre en subagente aislado |
| `agent` | `general-purpose` | Qué subagente usa `context: fork` (`Explore`, `Plan`, o custom) |
| `hooks` | — | Hooks scoped al ciclo de vida de la skill |
| `paths` | — | Glob — skill se activa solo cuando se trabaja con archivos que coinciden |
| `shell` | `bash` | Shell para comandos `!`: `bash` o `powershell` |

### String substitutions

```markdown
$ARGUMENTS          → todos los args como string ("123 --verbose")
$ARGUMENTS[N]/$N   → arg por posición 0-based ($0 = primero)
$nombre             → arg nombrado (con arguments: [issue, branch] → $issue, $branch)
${CLAUDE_SESSION_ID} → ID de sesión actual (para logs, archivos por sesión)
${CLAUDE_EFFORT}    → nivel de esfuerzo activo en este momento
${CLAUDE_SKILL_DIR} → directorio de la skill — para referenciar scripts bundleados
```

**Ejemplo con args nombrados:**
```yaml
---
name: fix-issue
arguments: [issue, branch]
disable-model-invocation: true
---
Fixear issue $issue en la branch $branch siguiendo nuestros estándares.
```
Invocación: `/fix-issue 42 feat/auth` → `$issue=42`, `$branch=feat/auth`.

### context: fork — skill aislada en subagente

Usá `context: fork` cuando la skill haría trabajo pesado que contaminaría el hilo principal (diffs largos, búsquedas exhaustivas, análisis de archivos). El contenido de SKILL.md se vuelve el prompt del subagente — el hilo principal solo recibe el resumen.

```yaml
---
name: deep-research
description: Investigar un tema en el codebase. Usar cuando el usuario pide análisis profundo de código.
context: fork
agent: Explore       # solo lectura, no carga CLAUDE.md — contexto limpio y económico
---

Investigar $ARGUMENTS:
1. Encontrar archivos relevantes con Glob y Grep
2. Leer y analizar el código
3. Resumir hallazgos con referencias exactas de archivo:línea
```

> **Regla:** Si la skill busca o lee más de 3 archivos, considerar `context: fork`. El subagente paga su propio contexto — el hilo principal no se ensucia con los resultados intermedios.

`agent: Explore` es el más económico para lectura: no carga CLAUDE.md ni git status. `agent: general-purpose` cuando necesitás más capacidad.

### Supporting files — skill como directorio

Una skill puede ser un directorio con archivos de soporte. SKILL.md es el entrypoint; el resto solo se carga cuando se referencia explícitamente:

```
mi-skill/
├── SKILL.md          # < 500 líneas — entrypoint y navegación
├── reference.md      # docs detalladas — no carga sola, Claude la lee cuando la necesita
├── examples/
│   └── sample.md     # output esperado — útil para few-shot en el body
└── scripts/
    └── helper.py     # script ejecutable — no se lee, se corre con !
```

Referenciar desde SKILL.md:
```markdown
Para especificación completa de la API → ver [reference.md](reference.md)
Para ejemplos de output → ver [examples/sample.md](examples/sample.md)
```

**Cuándo usar:** cuando SKILL.md supera 200 líneas. La regla es la misma que para cualquier archivo en el sistema: un archivo de 500 líneas siempre se lee completo; dividido en partes se lee solo lo que aplica.

### Hub — qué va y qué no

```
✅ Tabla de triage por tipo de tarea
✅ Reglas de una línea que aplican a TODO
❌ Tablas de datos o nomenclatura → van en skills de referencia
❌ Ejemplos de código → van en docs de referencia
❌ Contenido que ya está en CLAUDE.md  ← duplicación silenciosa de tokens
```

Si el hub supera 40 líneas → hay contenido que no le pertenece.
Si CLAUDE.md ya tiene el dispatch → usar `user-invocable-only` y eliminar el hub del flujo automático.

### Patrón: scaffold-questions skill

Cuando un tool-specific project tiene un flujo de `AskUserQuestion` definido (onboarding, scaffold, configuración), formalizar las preguntas exactas en una skill de referencia en lugar de improvisar en cada sesión.

```markdown
---
name: scaffold-questions
description: Exact AskUserQuestion format for [flow name]. Load before Call 1/2/3.
disable-model-invocation: true
allowed-tools: []
---
# [Flow] Questions
## Call 1 — [Pregunta] (×1)
question: "…"
header: "…"
options:
  - [Label] | [description]
  - [Label] | [description]
## Call 2 — … (×4)
…
```

**Por qué:** sin este skill, el modelo improvisa opciones distintas en cada sesión — inconsistente y difícil de testear. Con el skill cargado, las preguntas son idénticas siempre.

**Cuándo usar:** cualquier flujo que tenga `AskUserQuestion` repetibles (onboarding, scaffold, configuración inicial).

**Validado:** eliminó 3 iteraciones de preguntas incorrectas en la misma sesión.

> **Anti-pattern "in notes":** opciones con label `"type X in notes"` confunden — el usuario no ve ningún campo llamado "notes". Usar siempre `"Other" field (option 3 below)` para que apunte al campo visible de la UI. Validado en prueba de flujo 2026-06-02.

### Dynamic context injection

Prefix `!` ejecuta un comando y pega el output en el contexto **antes** de que Claude lea la skill — Claude recibe datos reales, no el comando:

```markdown
## Estado actual
!`git diff HEAD --stat`
!`git log --oneline -3`
```

Usar solo cuando el output es esencial — cada línea cuesta tokens. Para comandos multi-línea:

````markdown
```!
node --version
npm --version
git status --short
```
````

**`ultrathink` — razonamiento extendido en una palabra:** incluir `ultrathink` en cualquier parte del body activa pensamiento profundo para esa invocación. Usar en skills de auditoría o decisiones de arquitectura donde el costo del error justifica el costo del reasoning.

**Gotcha — skill invisible:** si una skill con `disable-model-invocation: true` no aparece en la lista de usuario, diagnosticar en orden: (1) `user-invocable: true` declarado explícitamente — algunos combos de flags la silencian sin error visible; (2) `argument-hint` presente si recibe argumentos; (3) `/reload-plugins` ejecutado post-cambio. La declaración explícita es más confiable que depender del default.

---


<!-- §8 -->
## 8. Scope del proyecto

> Sin scope, cada agente empieza desde cero — lee 5 archivos para entender qué existe antes de poder hacer algo. Con scope bien escrito, va directo al trabajo. El ROI de escribir un scope es inmediato.

El scope captura el estado real del proyecto: qué existe, qué falta, qué está decidido.
Fragmentado por dominio — cada agente lee solo lo que necesita.

### Estructura

```
.claude/scope/
├── scope-index.md        → resumen de 20 líneas — todos lo leen
├── scope-[sistema-a].md  → detalle de un sistema específico
└── scope-[sistema-b].md
```

### Template — scope-index.md

```markdown
# <Proyecto> — Scope Index
Última actualización: <YYYY-MM-DD>

## Estado                                  # REQUIRED — una línea del estado actual
<Qué se está construyendo o dónde está el proyecto ahora mismo.>

## Lo que existe                           # REQUIRED — sistemas ya construidos
- <Sistema A>
- <Sistema B>

## Próximo sistema                         # REQUIRED si hay algo planificado
<Sistema C> → ver `scope-<sistema-c>.md`

## Backlog                                 # OPTIONAL
1. <Lo más prioritario>
2. <Siguiente>

## Archivos de scope                       # REQUIRED — uno por sistema
- `scope-<a>.md` — <descripción en una línea>
- `scope-<b>.md` — <descripción en una línea>
```

### Template — scope-\<sistema\>.md

```markdown
# <Proyecto> — Scope: <Sistema>
Última actualización: <YYYY-MM-DD>
Leer cuando: <condición específica — ej: "implementando features del sistema de auth">

## Qué hace                                # REQUIRED — una línea
<Responsabilidad única de este sistema.>

## Orden de implementación                 # REQUIRED si hay dependencias entre pasos
1. <Paso concreto — lo que debe existir primero>
2. <Paso siguiente>

## Flujo                                   # OPTIONAL — solo si la secuencia no es obvia
<diagrama en texto ASCII si aplica>

## Dependencias                            # OPTIONAL
- <Sistema X> debe estar completo antes de empezar <parte Y>

## API existente relevante                 # REQUIRED cuando este sistema integra otros
# Listar solo lo que el agente implementador necesita conocer — no todo el código
<NombreClase>  <ruta/al/archivo.ext>
  <metodo>(<param>: <Tipo>) → <efecto o señal emitida>
  señal: <nombre_señal>(<param>: <Tipo>)

## Decisiones (ADR)                        # OPTIONAL — solo decisiones no obvias
# Las entradas ADR son INMUTABLES — nunca editar, solo agregar
- <YYYY-MM-DD>: <decisión tomada>. Alternativas descartadas: <X, Y>. Razón: <por qué esta>.
```

**Por qué la sección API importa para los tokens:**
Cuando un agente implementa algo nuevo que integra sistemas existentes, su primer trabajo es leer esos archivos para entender la API. Si el scope ya tiene esa información resumida, el agente va directo a implementar. Sin API en el scope → 5-10 Read calls extra (~5-8k tokens) por feature compleja que integra sistemas existentes.

Las entradas ADR son inmutables — nunca se editan, solo se agregan. Permiten entender meses después por qué se descartó una alternativa. Si no hay decisiones no obvias, omitir la sección.

### Quién lee qué

- **CLAUDE.md** → apunta solo a `scope-index.md`
- **Lead / orchestrador** → index + scope del sistema a planificar
- **Especialistas** → ninguno (reciben contexto del lead)
- **Postmortem** → index (para actualizar estado)

### Cuándo actualizar

- Durante la sesión: si se toma una decisión de diseño → anotar en el scope correspondiente
- Al terminar: el postmortem marca checkboxes y actualiza estado
- Nuevo sistema: crear `scope-[sistema].md` y referenciar en index

---


<!-- §9 -->
<!-- §9-quick -->
## 9. Learnings

> El sistema de learnings es la memoria del proyecto. Sin él, cada sesión repite los mismos errores. Con él, el agente ya sabe que "grab_focus() en _ready() no funciona" antes de intentarlo. Es la inversión de tiempo que más rentabilidad da a largo plazo.

Lecciones capturadas por sesión, fragmentadas por dominio.

### Estructura

```
.claude/learnings/
├── learnings-[dominio-a].md   → < 150 líneas
├── learnings-[dominio-b].md
└── learnings-general.md       → patrones que aplican a todo
```

### Formato de entry

```markdown
- [YYYY-MM-DD] [CATEGORÍA] descripción concreta del problema.
  Causa: por qué ocurre.
  Solución: fix exacto o patrón correcto.
```

**Vago — inútil:**
```
- El sistema de autenticación puede ser complicado.
```

**Concreto — accionable:**
```
- [2026-05-15] [GOTCHA] JWT expirado retorna null, no lanza excepción.
  Causa: comportamiento por diseño de la librería X.
  Solución: verificar if token is None antes de decodificar.
```

### Cuándo inlinear vs cuándo mantener en archivo

No todo learning tiene que estar en el archivo. Los más críticos deben vivir inline en el agente:

```
¿El agente necesita este gotcha en TODA tarea, sin excepción?
    SÍ → inline en el agente (sección ## Gotchas críticos)
    NO → mantener en learnings file, leer bajo demanda

¿El gotcha cambió o se actualizó esta semana?
    SÍ → actualizar el archivo (el postmortem lo gestiona)
         luego actualizar también el inline si aplica
    NO → el inline y el archivo deberían coincidir
```

**Ejemplo de inline en agente:**
```markdown
## Gotchas críticos
- JWT expirado retorna null, no exception. Fix: verificar before decode.
- reload_scene() desde callback → call_deferred("reload_current_scene").
- grab_focus() en _ready() no funciona → grab_focus.call_deferred().
```

El archivo de learnings es la **fuente de verdad histórica** — contiene todas las entradas con fecha y causa. El inline es un **subconjunto activo** — los top 5-10 gotchas que no deben olvidarse en ninguna tarea.

### Learnings en plugins distribuibles

Si usas un plugin distribuible, los learnings viven en el **proyecto que instaló el plugin**, no en el repo del plugin:

```
proyecto-nebula/
└── .claude/
    └── learnings/          ← aquí, no en el repo del plugin
        ├── learnings-api.md
        └── learnings-general.md
```

Esto significa que:
- `claude plugin sync` nunca sobreescribe los learnings del dev
- Cada proyecto tiene su propia historia — los errores de Nebula no aparecen en otro proyecto
- El curador (`@design-curador`) corre localmente con `Path.cwd() / ".claude" / "learnings"` como base
- Un CCR **no puede** curar estos learnings — viven en el filesystem local, no en el repo

<!-- §9-ref -->
### Template — learnings-\<dominio\>.md

No arrancar con archivos vacíos — poblar con lecciones conocidas del stack desde el día 1:

```markdown
# Learnings — <Dominio>
Última revisión: <YYYY-MM-DD>
Agente curador: @<nombre-curador>

## Lo que funciona                         # patrones confirmados del stack
- <YYYY-MM-DD> <patrón>: <por qué funciona — contexto mínimo para entender>

## Lo que no funciona                      # errores con causa conocida
- <YYYY-MM-DD> <problema>: <causa raíz> → <fix o workaround>

## Patrones del proyecto                   # decisiones de arquitectura ya tomadas
- <YYYY-MM-DD> <patrón>: <razón — alternativa descartada si aplica>

## Errores recurrentes                     # gotchas que aparecen más de una vez
- <YYYY-MM-DD> <error>: <causa> → <fix>
```

**Cómo arrancar con un stack conocido:**
```markdown
## Errores recurrentes
- <hoy> Async sin await en JS: silencioso, retorna Promise no resuelta → siempre await o .catch()
- <hoy> CORS en dev: credentials require explicit origin, not * → Access-Control-Allow-Origin: http://localhost:3000
```

### Mantenimiento

- Mensual: eliminar entries obsoletas
- > 150 líneas: dividir por subdominio
- Obsoleto: mover a `.claude/learnings/archive/`
- Inline en agentes: revisar cuando el archivo cambia

### Hook de aviso de tamaño (en `stop.py`)

Usar `Path(__file__)` para navegar desde el hook hasta la carpeta de learnings — nunca paths absolutos:

```python
from pathlib import Path
import json

CLAUDE_DIR = Path(__file__).parent.parent   # .claude/hooks/ → .claude/ (proyecto local)
# En un PLUGIN esto apuntaría al plugin instalado, no al proyecto — usar
# Path.cwd() / ".claude" como base (ver §11 Trampas)
LIMIT = 150

for path in CLAUDE_DIR.glob("learnings/learnings-*.md"):
    try:
        lines = len(path.read_text().splitlines())
        if lines > LIMIT:
            print(json.dumps({"systemMessage":
                f"⚠️ {path.name}: {lines} líneas — ejecutar @curador"}))
    except Exception:
        pass
```

Integrar en el mismo `stop.py` junto con el recordatorio de postmortem — un solo hook para los dos avisos.

### Flujo postmortem → learnings → curador

El flujo correcto conecta tres piezas en orden:

```
Sesión de trabajo
    ↓
@postmortem  →  escribe entries en learnings/learnings-[dominio].md
                (NO en el hub — el hub es costo fijo por sesión)
    ↓
stop.py      →  avisa si algún learnings supera 150 líneas
    ↓
@curador     →  mensual: dedup + prune + promueve gotchas críticos
                inline en el agente correspondiente
```

> **¿El proyecto tiene > 1.000 learnings totales o buscas cosas por significado semántico?**
> El sistema de markdown tiene un techo natural — ver **§16 — Vector Memory** para el upgrade.

**Por qué el postmortem NO debe escribir en el hub:**
El hub tiene `disable-model-invocation: false` — está siempre en contexto. Cada lección que acumula ahí se paga en tokens en TODA tarea, aunque no sea relevante. Los learnings files tienen `disable-model-invocation: true` — se cargan solo cuando el agente los necesita.

**Fragmentación por dominio — cuándo hacerla:**
Empezar con un solo `learnings-general.md`. Fragmentar cuando supere 150 líneas:

```
learnings/
├── learnings-layout.md    → [LAYOUT] [BUTTONSTYLE]
├── learnings-api.md       → [API] [STATE]
├── learnings-sdui.md      → [SDUI]
└── learnings-general.md   → [TOKENS] [GOTCHA] y lo que no encaja en otro
```

**Mapeo categoría → agente (para el curador):**

| Categoría | Agente que recibe el gotcha inline |
|---|---|
| `[LAYOUT]` `[BUTTONSTYLE]` | agente de organisms / layer más cercano al bug |
| `[API]` `[STATE]` | agente de atoms (init rules, fluent modifiers) |
| `[SDUI]` | agente sdui |
| `[TOKENS]` | agente tokens |
| `[GOTCHA]` | agente debugger (sección ## Hipótesis comunes) |

---


<!-- §10 -->
<!-- §10-quick -->
## 10. Arquitectura multi-agente

> Aquí es donde el sistema se vuelve poderoso de verdad. Múltiples agentes especializados trabajando en secuencia, cada uno en su propio contexto aislado, sin contaminar el hilo principal. El secreto: el lead coordina sin implementar, los especialistas implementan sin coordinar.

### Patrón sin hub redundante

Si CLAUDE.md ya tiene la tabla de dispatch, el hub no aporta — agrega un LLM call innecesario. El patrón eficiente es dispatch directo:

```
CLAUDE.md (dispatch completo)
├── Tarea simple    → especialista directo
├── Tarea compleja  → lead → especialistas
├── Bug             → debugger
├── Git             → git agent
└── Fin de sesión   → postmortem
```

Si el hub agrega lógica que CLAUDE.md no puede tener (por límite de líneas), usarlo con `skillOverrides: user-invocable-only` para que el modelo lo consulte solo cuando lo necesite, no automáticamente.

### Flujo de trabajo recomendado

```
1. Commitear pendientes        → @git
2. Nueva rama                  → @git
3. Implementación              → especialista o @lead
4. Revisión                    → @reviewer
5. PR + merge                  → @git  (hook auto-checkout master)
6. Fin de sesión               → @postmortem
```

### Física del subagente — lo que un lead NO puede hacer

Un subagente corre de una pasada hasta terminar. Tres imposibles que aparecen una y otra vez en prompts de leads mal diseñados:

1. **No puede pausar** a "esperar confirmación del usuario antes del siguiente paso" — termina y devuelve su output; los checkpoints con el usuario son del hilo principal
2. **No puede delegar** sin la tool `Agent` en su lista — un lead con `tools: Read, Glob, Grep` que dice "delego a @especialista" produce texto, no invocaciones
3. **Solo puede cargar skills si `Skill` está en su lista de tools** — los subagentes sin `tools:` restringido SÍ la tienen (verificado 2026-07-02); un especialista típico con `tools: Read, Write, Edit, Glob, Grep` NO. Regla lowcost: no contar con ella — pasar la template en el prompt de invocación e inline el patrón esencial como fallback

Dos diseños válidos de lead — elegir uno, no mezclar:

| Diseño | Tools | Checkpoints con el usuario |
|---|---|---|
| **Planner (Advisor §31)** — devuelve el plan de delegación, el hilo principal lo ejecuta | Read, Glob, Grep | ✅ entre cada paso |
| **Orchestrator real** — spawnea especialistas él mismo | + `Agent(especialistas)` | ❌ corre completo sin parar |

> **[2026-07-02] design-ios:** el lead tenía instrucciones de "esperar confirmación antes de continuar" y "delegar a @agente" con `tools: Read, Glob, Grep` — ambas físicamente imposibles. Reescrito como planner de una pasada. Un prompt que pide lo imposible no falla ruidosamente: el modelo improvisa una aproximación y el output se degrada en silencio.

### La pregunta clave para el lead

> ¿Una sola tarea del usuario se descompone en ≥2 especialistas trabajando en secuencia?
> → SÍ → lead + hub. → NO → dispatch directo desde CLAUDE.md, sin lead.

Tener múltiples agentes **no** requiere lead. El lead es solo para pipelines cross-especialistas.

| Patrón | Lead? | Hub? | Por qué |
|---|---|---|---|
| Design system: "add component" → atoms→molecules→organisms | ✅ | ✅ | pipeline secuencial |
| iOS: "add feature" → domain→data→presentation→DI→coordinator | ✅ | ✅ | pipeline secuencial |
| Game: "fix bug" → debugger→implementer→reviewer→git | ✅ | ✅ | pipeline secuencial |
| swifttesting-plugin: "generate tests" → test-generator | ❌ | ❌ | tarea independiente |
| CLI con git+reviewer | ❌ | ❌ | tareas independientes |
| Plugin de migración: tareas separadas por módulo | ❌ | ❌ | cada tarea va a un especialista |

**Hub — cuándo añadirlo:**
Si hay lead → el hub es casi siempre necesario para triage. Sin hub, CLAUDE.md debe contener
la lógica de dispatch completa — si eso supera 30 líneas, hub > CLAUDE.md inline.

<!-- §10-ref -->
### Reglas de diseño

**Agentes = contextos aislados** — lo que lee un agente no contamina el hilo principal.

**No nesting:**
```
✅ Lead → instrucciones → Specialist A completa
✅ Lead → instrucciones → Specialist B completa
❌ Lead → Specialist A → invoca Specialist B (imposible)
```

**Verificación post-implementación:**
```
✅ Headless run + grep de errores
✅ Leer logs de output
✅ Leer el código y razonar
❌ Screenshots — nunca
❌ UI automation — nunca
```

**Commitear antes de crear rama** — si hay cambios sin commit y se crea una rama, los cambios se mezclan.

### Checkpoint de delegación — estado sin Write tool

El lead coordina sin implementar (§10). Tentación: darle `Write` para escribir un archivo JSON de estado cuando el contexto se comprime. Incorrecto: `Write` es implementación.

Solución de protocolo — una línea en el output format después de cada delegación:

```
Checkpoint: [N/M completado] · Pendiente: [ComponentB] · Bloqueadores: [ninguno]
```

Si el contexto se comprime, Claude puede grep el historial por `Checkpoint:` para reconstruir el estado sin `Write`. El estado vive en la conversación, no en el filesystem.

> Si la tarea del lead requiere más de ~20 turnos para completarse, el problema no es falta de estado — es que la tarea era demasiado grande. Dividir en sub-tareas atómicas, no parchar con archivos de estado.

### Worktrees — aislamiento git para agentes paralelos

Cuando dos agentes trabajan sobre el mismo repo simultáneamente, el problema no es el contexto — es el filesystem compartido: un agente modifica un archivo mientras el otro lo lee. `git worktree` le da a cada agente su propia copia del repo en una rama distinta, sin conflictos.

```bash
# Crear worktree manual para un agente paralelo
git worktree add ../repo-feature-b feature-b
# El agente trabaja en ../repo-feature-b — filesystem completamente aislado
```

**Cuándo usar worktrees:**

| Escenario | Sin worktree | Con worktree |
|---|---|---|
| 2 agentes modificando archivos distintos | Race condition posible | Cada uno en su rama — sin conflicto |
| Feature A y feature B en paralelo | 1 espera al otro | Aislamiento completo |
| Agent tool en Claude Code | Default (shared) | `isolation: "worktree"` — automático |

**Con el Agent tool:**
```python
Agent({
    isolation="worktree",   # el harness crea worktree temporal y lo limpia al terminar
    ...
})
```
Si el agente no hace cambios → el worktree se limpia solo. Si hace cambios → el path y la rama se devuelven en el resultado para merge manual.

**Anti-patrón:** worktrees para agentes que deben ir en secuencia (A termina → B empieza). Si no hay paralelismo real, el worktree es overhead sin beneficio — usar flujo estándar.

### Pre-layer opcional — validar antes del dispatch

Para proyectos con inputs inconsistentes o tareas que llegan mal definidas, una capa previa al dispatch puede filtrar ambigüedad antes de que llegue al especialista.

```
CLAUDE.md (dispatch)
   ↑
[preflight]  ← capa opcional — evalúa atomicidad y claridad
   ↑
usuario
```

Agente `preflight` mínimo:

```markdown
---
name: preflight
description: Evaluar atomicidad y claridad del input antes del dispatch.
  Usar cuando una tarea parece ambigua, involucra múltiples features
  sin relación, o el scope no está definido.
tools: Read
model: haiku
---

# Preflight

## Checks
1. ¿La tarea involucra ≥2 features no relacionadas? → pedir dividir
2. ¿El scope está definido? → si no, hacer 1 pregunta concreta
3. ¿La tarea es atómica y entregable en 1 sesión? → si no, proponer división

## Output
✅ Input claro y atómico → "continuar con dispatch"
⚠️  Ambiguo → 1 pregunta concreta de aclaración
❌ Demasiado grande → listar sub-tareas ordenadas
```

Activar solo cuando se necesite — no en cada tarea. En proyectos personales con un solo dev, el dispatch directo desde CLAUDE.md es suficiente. El pre-layer agrega valor cuando el input al sistema es ruidoso.

### Templates — los dos diseños de lead

La sección "Física del subagente" define los dos diseños válidos. Estos son sus templates — elegir UNO por proyecto, nunca mezclar.

**Diseño A — `lead-planner.md`** (Advisor §31 — checkpoints con el usuario entre pasos):

```markdown
---
name: lead-planner
description: "Planifica la delegación de tareas cross-especialistas. Usar cuando
  una tarea toca ≥2 sistemas o requiere ≥2 especialistas en secuencia.
  NO implementa ni delega — devuelve el plan y el hilo principal lo ejecuta."
model: claude-sonnet-5
tools: Read, Glob, Grep
---

# Lead Planner

Planifica de una pasada. No implementa ni invoca agentes — no tiene la tool Agent.

## Qué hacer
1. Leer `.claude/scope/scope-index.md` + el scope del sistema afectado
2. Descomponer la tarea en pasos atómicos, uno por especialista
3. Devolver el plan en el formato exacto — el hilo principal invoca cada paso

## Output — siempre este formato, nada más
PLAN: [tarea]
1. @[especialista] — TASK: [una línea] · FILES: [rutas] · DEPENDE DE: [paso N o "—"]
2. ...
Riesgo: [1 línea o "ninguno"]
Checkpoint: [0/N completado] · Pendiente: [todos los pasos]
```

**Diseño B — `lead-orchestrator.md`** (spawnea él mismo — corre completo sin parar):

```markdown
---
name: lead-orchestrator
description: "Ejecuta pipelines cross-especialistas de una pasada, sin checkpoints
  con el usuario. Usar SOLO cuando la secuencia está pre-aprobada
  (/plan corrió y el usuario dio el ok)."
model: claude-sonnet-5
tools: Read, Glob, Grep, Agent(implementador, reviewer)
---

# Lead Orchestrator

Corre completo sin parar — los checkpoints con el usuario son del hilo principal.

## Protocolo
1. Leer el scope del sistema afectado — NO leer código de implementación
2. Invocar especialistas en secuencia con formato mínimo: TASK · FILES · CONTEXT
3. Tras cada uno: verificación estática (leer archivos generados, razonar conexiones)
4. Si un especialista falla 2 veces → parar y reportar — NUNCA implementar directamente

## Output
Checkpoint: [N/M completado] · Pendiente: [X] · Bloqueadores: [ninguno|detalle]
```

### Árbol de referencia — proyecto multi-agente completo

Lo mínimo que las secciones §2-§9 asumen, en un solo lugar:

```
proyecto/
├── CLAUDE.md                     # < 30 líneas — dispatch + reglas duras (§2)
└── .claude/
    ├── agents/
    │   ├── lead.md               # planner O orchestrator — uno, no ambos
    │   ├── implementador.md      # sonnet · Read, Write, Edit, Glob, Grep
    │   ├── reviewer.md           # haiku · Read, Glob, Grep
    │   ├── debugger.md           # sonnet — solo si el dominio lo amerita (§5)
    │   ├── git.md                # haiku · Bash, Read
    │   ├── postmortem.md         # haiku — always-YES (§14)
    │   └── curador.md            # haiku — mensual (§5)
    ├── skills/
    │   └── plan/SKILL.md         # /plan (§17) — always-YES (§14)
    ├── scope/
    │   ├── scope-index.md        # < 20 líneas (§8)
    │   └── scope-<sistema>.md    # < 50 líneas c/u
    ├── learnings/
    │   └── learnings-general.md  # bootstrap con lecciones del stack día 1 (§9)
    ├── hooks/
    │   ├── pre_write_guard.py    # always-YES (§14/§18)
    │   ├── pre_push_guard.py     # bloquea push directo a master (§7)
    │   └── stop.py               # aviso learnings > 150 líneas (§9)
    └── settings.json             # registra los hooks (§7)
```

### Flujo end-to-end con budgets — feature mediana (2 sistemas)

```
usuario: "añade rate limiting al login"
  → /plan                 haiku    ~600t          usuario aprueba
  → @lead-planner         sonnet   ~10-18k (aislado) → plan de 2 pasos
  → @implementador A      sonnet   ~8-14k  (aislado)
  → @implementador B      sonnet   ~8-14k  (aislado)
  → @reviewer             haiku    ~4-8k   (aislado — solo archivos modificados, ≤4)
  → @git  BRANCH+COMMIT+PR · VALIDADO: sí   haiku   ~6-7k
  → @postmortem           haiku    ~5-10k

Contexto principal acumulado: ~1.4k extra (§3) — el resto es Capa 3 aislada.
Los números por arquetipo están en §3; los techos en §23.
```

---


<!-- §11 -->
<!-- §11-quick -->
## 11. Plugin distribuible

> Llegaste aquí porque tus agentes locales funcionan bien y quieres llevarlos a otro proyecto sin copiar archivos. El plugin es exactamente eso: tu cocina empaquetada. Una línea de `claude plugin add` y está lista en cualquier repo.

Solo cuando necesitas reutilizar en múltiples proyectos o compartir con el equipo.

### Estructura

```
mi-repo/
├── .claude-plugin/
│   └── marketplace.json  ← REQUERIDO para "Browse plugins" en desktop app
├── plugins/
│   └── mi-plugin/
│       ├── .claude-plugin/
│       │   └── plugin.json   ← REQUERIDO
│       ├── agents/
│       ├── skills/
│       ├── commands/         ← slash commands (está en la whitelist — §27 lo usa)
│       ├── hooks/
│       │   └── hooks.json    ← REQUERIDO si usas hooks — wrapper {"hooks":{...}} + ${CLAUDE_PLUGIN_ROOT}
│       └── README.md         ← REQUERIDO para distribución
```

### Validar SIEMPRE antes de distribuir

```bash
claude plugin validate ./plugins/mi-plugin
```

Atrapa las tres clases de error que fallan **en silencio** en runtime: manifest con campos inválidos, frontmatter YAML roto (skill carga sin metadata), y `hooks.json` con formato incorrecto (ningún hook se registra). Correrlo en pre-commit o CI (§20) — un plugin con enforcement muerto se ve idéntico a uno funcionando.

### Componentes soportados — whitelist cerrada

`skills/` · `commands/` · `agents/` · `hooks/` · `.mcp.json` · `output-styles/` · `lspServers` · `themes` · `monitors`. Nada más:

- **`rules/` NO es componente de plugin** — `.claude/rules/*.md` con glob es feature de proyecto local. En un plugin, las reglas universales van en la skill hub o inline en los agentes.
- **`output-styles/` de plugin aplica a TODA la conversación principal** mientras el plugin esté activo — no por-agente. Un `swift-only.md` global silencia la prose de toda la sesión. Reglas de output por agente → inline en el agente (son 3-6 líneas).
- **`plugin.json` no tiene campo `components`** — los componentes se descubren por convención de directorios; el campo se ignora.

> **[2026-06-02] design-ios:** `marketplace.json` en la raíz es REQUERIDO para el flujo "Browse plugins" del desktop app — no es un archivo opcional ni de metadata. Eliminarlo rompe la instalación UI para todos los usuarios del equipo. Error: confundirlo con dead weight porque la guía no lo mencionaba.

<!-- §11-ref -->
### Template — marketplace.json

Raíz del repo. El desktop app lo lee en **Browse plugins → Add marketplace** — sin él el repo no aparece como fuente de plugins.

```json
{
  "name": "<nombre-del-marketplace>",
  "owner": {"name": "<Tu Nombre>"},
  "description": "<Una línea de qué colección de plugins contiene.>",
  "plugins": [
    {
      "name": "<nombre-del-plugin>",
      "source": "./plugins/<nombre-del-plugin>",
      "description": "<Una línea de qué hace este plugin.>"
    }
  ]
}
```

### Template — plugin.json

```json
{
  "name": "<nombre-del-plugin>",         // REQUIRED — kebab-case, único en el marketplace
  "version": "1.0.0",                   // REQUIRED — semver
  "description": "<Qué hace en una línea.>", // REQUIRED
  "author": {"name": "<Tu Nombre>"},    // REQUIRED
  "repository": "https://github.com/<usuario>/<repo>", // RECOMMENDED
  "license": "MIT"                      // OPTIONAL
}
```

### Instalación — Desktop app (Claude Code)

1. Code → **Customize**
2. Click **+** junto a "Personal plugins"
3. **Browse plugins** → **Add marketplace**
4. Ingresar `usuario/mi-repo` → **Sync**
5. Instalar el plugin desde el marketplace

### Instalación — CLI

```bash
claude plugin add github:usuario/mi-repo
```

### Probar localmente

```bash
claude --plugin-dir ./plugins/mi-plugin   # cargar sin instalar
/reload-plugins                           # recargar cambios
/hooks                                    # verificar hooks registrados
```

### Plugin mínimo completo — 5 archivos coherentes

Los templates sueltos de arriba no muestran cómo encajan. Este es un plugin funcional entero (nombres consistentes entre sí) — copiar, renombrar, `claude plugin validate`:

````
plugins/revisor/
├── .claude-plugin/plugin.json
├── agents/revisor.md
├── skills/revisor-hub/SKILL.md
├── hooks/hooks.json
└── README.md
````

```json
// .claude-plugin/plugin.json
{
  "name": "revisor",
  "version": "1.0.0",
  "description": "Reviewer de convenciones con hook de confirmación.",
  "author": {"name": "Tu Nombre"}
}
```

```markdown
<!-- agents/revisor.md -->
---
name: revisor
description: "Convention checker. Use when reviewing, checking or validating
  any file, after implementing a component, or before committing."
model: claude-haiku-4-5
tools: Read, Glob, Grep
---
Revisa SOLO los archivos recibidos (≤4, 1 Read por archivo).
## Output — siempre este formato, nada más
PASS|FAIL: [archivo] — [razón en ≤8 palabras]
RESULTADO: PASS | FAIL
```

```markdown
<!-- skills/revisor-hub/SKILL.md -->
---
name: revisor-hub
description: "Dispatch del plugin revisor. Revisión de código → @revisor."
disable-model-invocation: false
allowed-tools: Read
---
| Tarea | Agente | Cuándo |
|---|---|---|
| Revisar convenciones | @revisor | post-implementación, pre-commit |
```

```json
// hooks/hooks.json — wrapper {"hooks":{...}} SIEMPRE (ver Trampas)
{
  "hooks": {
    "SubagentStop": [
      {
        "matcher": "(revisor:)?revisor",
        "hooks": [{"type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}\"/hooks/notify.py"}]
      }
    ]
  }
}
```

### Template — README.md del plugin

Es REQUERIDO para distribución y ningún template lo mostraba:

```markdown
# <nombre-plugin>

<Una línea: qué hace y para quién.>

## Instalación
`claude plugin add github:<usuario>/<repo>` — o desktop: Browse plugins → Add marketplace → `<usuario>/<repo>`

## Componentes
| Componente | Qué hace | Modelo |
|---|---|---|
| @<agente> | <una línea> | haiku |
| /<skill> | <una línea> | — |
| hook <evento> | <qué garantiza> | — |

## Uso mínimo
<2-3 líneas: el flujo típico de invocación.>

## Requisitos
<Python 3.x / toolchain — solo si los hooks lo necesitan.>
```

### Checklist de release

```
□ claude plugin validate ./plugins/<plugin> pasa limpio
□ Tests de hooks pasan (subprocess con payloads reales — §19)
□ Bump semver en plugin.json (fix → patch · componente nuevo → minor · breaking → major)
□ marketplace.json actualizado si cambió nombre/description
□ README.md refleja los componentes actuales
□ Tag git: <plugin>-vX.Y.Z — el consumidor puede pinear
□ Probar instalación limpia: claude --plugin-dir en un repo vacío
```

### Trampas de distribución

**`hooks.json` de plugin requiere el wrapper `{"hooks": {...}}`.**
Eventos al top level (como en algunos ejemplos viejos) → el archivo se rechaza en silencio y NINGÚN hook se registra. Mismo formato que settings.json:
```json
{"hooks": {"PreToolUse": [{"matcher": "Write|Edit", "hooks": [...]}]}}
```

**Scripts del plugin usan `${CLAUDE_PLUGIN_ROOT}`, nunca `$CLAUDE_PROJECT_DIR`.**
`CLAUDE_PROJECT_DIR` apunta al repo del consumidor — instalado, el hook busca `<repo-destino>/hooks/*.py` y falla siempre. En shell-form, entre comillas:
```json
{"type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}\"/hooks/guard.py"}
```
`$CLAUDE_PROJECT_DIR` se reserva para los archivos que SÍ viven en el proyecto destino (learnings, design-paths.json, flags).

**Frontmatter YAML: dos puntos sin comillas mata la skill en silencio.**
`description: Use for slots: A, B` → YAML no parsea → la skill carga con metadata vacía (sin nombre, sin slash command, sin triggers). Quotear cualquier description con `:` — `claude plugin validate` lo detecta.

**`user-invocable: false` + `disable-model-invocation: true` = skill inalcanzable.**
Nadie puede cargarla — ni usuario ni modelo. Las skills de referencia (templates, convenciones) que un flujo del modelo debe cargar necesitan `disable-model-invocation: false` (el costo es solo la description en contexto).

**Agentes de plugin: `hooks`, `mcpServers` y `permissionMode` en el frontmatter se ignoran en silencio.**
Verificado 2026-07-04 contra la doc oficial de sub-agents: por seguridad, estos 3 campos NO se aplican cuando el agente se carga desde un plugin — ni error ni warning, el agente simplemente corre sin ellos. Si el autor del plugin escribió `hooks:` esperando scoping por-agente, no pasa nada — mismo patrón de fallo silencioso que `rules/` en plugins (arriba en esta sección). Fix: si el consumidor necesita esos campos, debe copiar el archivo del agente a `.claude/agents/` o `~/.claude/agents/` locales — ahí sí se respetan.

**Los subagentes con `tools:` restringido NO pueden cargar skills.**
La tool `Skill` existe en subagentes sin restricción de tools (verificado 2026-07-02), pero los agentes de plugin bien diseñados restringen `tools:` al mínimo — y ahí `Skill` no está. Un agente restringido que dice "Cargar skill X" es una instrucción imposible. Patrón correcto: el hilo principal (la skill de creación) carga la template y o bien escribe los archivos él mismo, o pasa el contenido en el prompt de invocación del agente. El agente lleva su patrón esencial inline como fallback.

**Skills ejecutadas vía Skill tool NO pasan por UserPromptSubmit.**
Un gate de flags que se abre solo cuando el usuario tipea `/plugin:plan` entra en deadlock si otra skill ejecuta el plan como paso interno — el hook nunca ve el prompt. Los slash commands de creación también deben abrir el gate:
```python
_PLAN_TRIGGER = re.compile(r'mi-plugin:(plan|new-\w+)\b')
```

**Learnings no van en el repo del plugin.**
Si los learnings están en git dentro del plugin, `claude plugin sync` los sobreescribe en todos los repos que lo usan. Los learnings deben vivir en `.claude/learnings/` del **proyecto que instaló el plugin**.

En hooks, reemplazar:
```python
PLUGIN_ROOT = Path(__file__).parent.parent          # ❌ apunta al plugin
PLUGIN_ROOT.glob("learnings/learnings-*.md")
```
Por:
```python
LEARNINGS_DIR = Path.cwd() / ".claude" / "learnings" # ✅ proyecto destino
LEARNINGS_DIR.glob("learnings-*.md")
```

**Plan flags deben scopearse por proyecto.**
`~/.claude/design-plan-approved.flag` es global — si hay dos proyectos abiertos, el plan de uno habilita el gate del otro. Scopear con hash del CWD:
```python
_proj = hashlib.md5(str(Path.cwd()).encode()).hexdigest()[:8]
_PLAN_FLAG = Path.home() / ".claude" / f"design-plan-approved-{_proj}.flag"
```

**Los CCR no pueden curar learnings per-project.**
Un cloud agent clona el repo desde GitHub — no tiene acceso a `.claude/learnings/` local del dev. Si los learnings son per-project, el curador debe correr localmente (hook de SessionStart con aviso por fecha) o invocarse manualmente.

**Agentes leen archivos innecesarios sin constraint explícito.**
Sin instrucción de "no leas componentes existentes", el modelo lee 2-4 archivos de referencia antes de crear uno nuevo — aunque la template ya contenga el patrón. Fix: añadir sección `## Archivos a leer (y nada más)` en cada agente especialista.

> **[2026-06-27] design-ios:** `PLUGIN_ROOT = Path(__file__).parent.parent` en hooks apunta al directorio del plugin instalado, no al proyecto destino. Todos los paths que deben ser per-project (learnings, plan flags) necesitan usar `Path.cwd()` como base.

> **[2026-07-02] design-ios (auditoría 2.4.0):** los 6 defectos P0 del plugin eran de infraestructura, no de contenido — hooks.json sin wrapper, `$CLAUDE_PROJECT_DIR` en vez de `${CLAUDE_PLUGIN_ROOT}`, YAML sin quotear, valor inválido de `permissionDecision`, campo inexistente en payload de SubagentStop, gate en deadlock. Ninguno era detectable usándolo: los hooks fallan invisibles. Moraleja: **cada pieza de automatización necesita una forma de avisar que murió** — `claude plugin validate` + tests subprocess (§19) son obligatorios, no opcionales. Y verificar los API shapes de hooks/plugins contra docs oficiales, nunca de memoria.

---


<!-- §31 -->
<!-- §31-quick -->
## 31. Advisor Pattern — validación sin subir de modelo

> Como un sous-chef que revisa el plato antes de que salga a la mesa: no cocina — solo dice si algo está mal. El chef sigue siendo sonnet; el revisor es haiku. El plato mejora sin cambiar al chef Michelin.

El patrón resuelve el dilema "sonnet comete errores, pero no quiero pagar Opus" (~1.7× por token — §25). La solución no es subir de modelo — es agregar un segundo agente barato que revisa el output del primero.

### Cuándo aplicar

| Síntoma | Sin advisor | Con advisor |
|---|---|---|
| Sonnet genera output que incumple un criterio fijo (schema, formato, campos obligatorios) | Iterar con sonnet hasta que funcione | haiku detecta y reporta el fallo en un turno |
| El output de un agente es input del siguiente (pipeline) | Error se propaga silenciosamente | Advisor corta la cadena antes de que escale |
| Subir a opus parece la única solución | ~1.7× costo por token | Sonnet + haiku advisor (~1.15× costo) |

**No aplicar cuando:** ya existe un agente reviewer explícito en el sistema. Dos revisores para lo mismo = costo duplicado sin beneficio.

**Límite del advisor en haiku:** solo detecta lo que puede verificar contra un criterio explícito (¿tiene los campos obligatorios? ¿sigue el schema? ¿el formato es el pedido?). No reemplaza un reviewer de correctness — un bug lógico o de seguridad requiere razonar sobre qué hace el código, no solo comparar contra una lista. Para eso, sonnet mínimo (→ split reviewer en §25).

### Implementación

Dos agentes en secuencia: generator → advisor. El advisor tiene tools mínimas — si puede escribir, ya no es un advisor.

```yaml
# .claude/agents/advisor.md
---
name: advisor
description: Revisa el output del agente anterior y emite veredicto PASS/FAIL con razón.
  Invocar después de cualquier generator cuando el output va a ser usado por otro sistema.
model: claude-haiku-4-5
tools: Read
---

Tu único trabajo: revisar el output recibido y emitir un veredicto binario.

Responder SOLO con:
PASS — [razón en una línea]
o
FAIL — [problema específico] — [corrección mínima necesaria]

No generar código. No proponer mejoras. Solo veredicto.
```

### Flujo en arquitectura multi-agente

```
@generator → produce output
@advisor   → PASS o FAIL con razón
  PASS → continuar al siguiente agente
  FAIL → reinvocar @generator con el feedback (1 retry máximo)
         Si vuelve a fallar → el problema es el generator, no el output
```

El advisor no itera — emite veredicto. Si hacés más de 1 retry, el problema es el design del generator.

### Costo comparado

| Estrategia | Costo relativo (por token, pricing 2026-07) | Cuándo |
|---|---|---|
| Sonnet solo | 1× | Output predecible, stack conocido |
| Sonnet + haiku advisor | ~1.15× | Output con consecuencias si está mal |
| Opus solo | ~1.7× | Si sonnet + advisor sigue fallando |
| Opus + advisor | ~1.85× | Security/one-shot donde el error es irreversible |

---


<!-- §32 -->
<!-- §32-quick -->
## 32. Archivos que nadie documenta — el resto del .claude/

> La imagen del .claude/ siempre muestra agents/, skills/ y hooks/. Nadie habla de los otros cuatro. Pero CLAUDE.local.md, output-styles/, rules/ y settings.local.json resuelven problemas reales que sin ellos se parchean con prompts repetidos o CLAUDE.md inflado.

### Árbol de decisión — cuándo usar cada uno

```
¿Instrucciones que NO deben subir al repo (rutas locales, tokens, prefs personales)?
  → CLAUDE.local.md

¿Quieres que Claude cambie el formato de respuesta sin repetirlo en cada prompt?
  → output-styles/

¿Tienes reglas que solo aplican a un subdirectorio (src/api/, tests/, migrations/)?
  → rules/

¿Permissions personales que no aplican a todo el equipo?
  → settings.local.json
```

---

### 1. CLAUDE.local.md — tu override personal

Variante gitignored de CLAUDE.md. Claude carga ambos; .local.md gana en conflicto.

| | `CLAUDE.md` | `CLAUDE.local.md` |
|---|---|---|
| Se commitea | ✅ | ❌ gitignored |
| Lo ve el equipo | ✅ | Solo vos |
| Propósito | Reglas del proyecto | Overrides personales de máquina |

**En `.gitignore`:**
```
CLAUDE.local.md
.claude/settings.local.json
```

**Qué va aquí:**
```markdown
# CLAUDE.local.md

## Paths de esta máquina
- Python: /opt/homebrew/bin/python3
- DB local: postgresql://localhost:5432/myapp_dev

## Preferencias personales
- Al terminar tarea larga: notificar con terminal-notifier
- No usar npm audit en este repo — rompe mi hook de postinstall
```

**Nunca en CLAUDE.local.md:** reglas de arquitectura del proyecto (→ `CLAUDE.md`) ni secrets reales (→ `.env`).

**En plugins:** no existe — es personal por definición. Si el plugin necesita config por-usuario, usar `settings.local.json`.

<!-- §32-ref -->
---

### 2. output-styles/ — formato de respuesta on tap

Archivos Markdown que definen la forma del output. Claude los aplica cuando un agente los referencia o el usuario los menciona.

```
.claude/output-styles/
├── terse.md      ← código only, sin prose
├── verbose.md    ← explicaciones + código
└── report.md     ← tabla de hallazgos estructurada
```

**Template — `terse.md`:**
```markdown
# Estilo: terse
- Solo código, sin explicaciones
- Sin encabezados salvo que haya más de 3 archivos
- Sin "aquí está el fix" ni resumen al final
- Si el cambio es obvio por el diff, no comentar
```

**Template — `verbose.md`:**
```markdown
# Estilo: verbose
- Explicar el porqué antes del código
- Un párrafo de contexto por cada decisión no obvia
- Incluir alternativas descartadas con razón
```

**Cómo invocar desde el chat:**
```
Seguí output-styles/terse.md para esta respuesta.
```

**Desde un agente:**
```yaml
---
name: code-fixer
description: Arregla bugs. Responde siempre en estilo terse.
---
Seguí siempre .claude/output-styles/terse.md para tus respuestas.
```

**LowCost:** `terse.md` en agentes de code-only ahorra 30-50% de tokens de output en runs largos sin cambiar el modelo.

**Patrón de auditoría — agents existentes:** antes de distribuir, revisar cada agente por reglas universales duplicadas (idioma, compilación, constantes de tamaño). Cada regla en el agente se paga en cada tool call. En **proyecto local**, moverlas a `rules/` con el glob apropiado — solo se pagan cuando se tocan archivos del dominio. En **plugin**, `rules/` no existe (ver abajo): las reglas universales van en la skill hub y el subset crítico inline por agente.

**En plugins:** ✅ sí es componente de plugin — verificado en la referencia oficial (`output-styles/` en el árbol de componentes + campo `outputStyles` en el manifest). ⚠️ Pero cuidado con el alcance: un output style NO es por-agente — aplica a la conversación principal (§11). Los subagentes tampoco pueden leerlo (§13). Reglas de output para code-writer agents → inline en el agente (3-6 líneas), no en `output-styles/`.

---

### 3. rules/ — instrucciones glob-scoped

Archivos que Claude carga automáticamente cuando trabaja en archivos que hacen match con el glob. No tenés que pedirlo — carga solo.

```
.claude/rules/
├── api.md         ← carga al tocar src/api/**
├── tests.md       ← carga al tocar **/*.test.ts
└── migrations.md  ← carga al tocar db/migrations/**
```

**Diferencia con CLAUDE.md:**

| | `CLAUDE.md` | `rules/api.md` |
|---|---|---|
| Cuándo carga | Siempre, cada turno | Solo al tocar `src/api/**` |
| Tokens gastados | Fijo — siempre | Solo cuando es relevante |
| Propósito | Reglas universales | Reglas de dominio específico |

**Cuándo usar rules/ en vez de CLAUDE.md:**
- Instrucciones de un subsistema que no aplican al resto del repo
- CLAUDE.md ya pasa las 30 líneas (§2) y no todo es siempre relevante
- Distintos devs trabajan en distintos dominios — rules/ los mantiene aislados

**Ejemplo práctico — `rules/api.md`**

```markdown
---
glob: src/api/**
---
# Reglas — src/api/

## Autenticación
- Toda ruta nueva requiere middleware `authGuard` — sin excepción
- Tokens en headers, nunca en query params

## Formato de respuesta
- Siempre `ApiResponse<T>` como wrapper
- Errores: `{ error: string, code: HTTP_STATUS }`

## Imports
- No importar desde `../db/` directamente — usar el repo layer
- No lanzar excepciones crudas — usar `ApiError`

## Tests requeridos por endpoint
- Test de auth (401) + happy path (200) como mínimo
```

**Ejemplo práctico — `rules/tests.md`**

```markdown
---
glob: "**/*.test.ts"
---
# Reglas — archivos de test

- No mockear la DB — usar instancia de test real (Q1 2025: mocks pasaban pero prod fallaba)
- Cada test independiente: arrange → act → assert, sin estado compartido
- Naming: `describe('NombreClase') > it('debería [comportamiento] cuando [condición]')`
- No usar `test.only` — bloquea CI sin error visible
```

**En plugins:** ❌ NO es componente de plugin — la whitelist es cerrada (§11: skills · commands · agents · hooks · .mcp.json · output-styles · lspServers · themes · monitors). Verificado 2026-07-03 contra la referencia oficial de plugins: `rules/` solo aparece como feature de `.claude/rules/` del proyecto local, nunca como directorio de plugin. Un `rules/` dentro de un plugin es **dead weight silencioso**: no falla, simplemente nada lo carga — el autor cree que sus reglas se inyectan y el enforcement está muerto (así nacieron `rules/swift.md` y `output-styles/swift-only.md` muertos en design-ios).

En un plugin, el equivalente es: reglas universales → skill hub · subset crítico → inline en cada agente · reglas mecanizables → hook PreToolUse.

---

### 4. settings.local.json — permissions personales

Hermano gitignored de `settings.json`. Misma estructura, solo aplica a tu máquina.

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run dev:*)",
      "Bash(psql:*)"
    ]
  }
}
```

**Qué va aquí:** comandos que solo existen en tu entorno local, permissions de tu flujo personal que serían ruido en el settings.json compartido.

**Qué NO va aquí:** permissions que todo el equipo necesita (→ `settings.json`), hooks (→ `hooks/` + `settings.json`).

**En plugins:** no se distribuye — es local por diseño. El plugin incluye `settings.json` con permissions base que el equipo comparte; cada dev agrega las suyas en `settings.local.json`.

---

### Resumen — qué distribuir en un plugin

| Archivo | ¿Va en plugin? | Razón |
|---|---|---|
| `CLAUDE.local.md` | ❌ | Personal — no tiene sentido distribuirlo |
| `output-styles/` | ✅ con cuidado | Es componente oficial, pero aplica a la conversación principal — no por-agente (§11) |
| `rules/` | ❌ | NO es componente de plugin (whitelist cerrada §11) — en plugin: hub + inline + hooks |
| `settings.json` | ✅ parcial | Solo permissions que el equipo comparte |
| `settings.local.json` | ❌ | Personal — gitignored por diseño |

**Estructura de plugin con los archivos correctos:**
```
plugins/mi-plugin/
├── .claude-plugin/
│   └── plugin.json
├── agents/             ← reglas universales: subset crítico inline aquí
├── skills/             ← reglas universales: fuente canónica en la skill hub
├── hooks/
│   └── hooks.json      ← reglas mecanizables: enforcement real
├── output-styles/      ← ✅ pero ámbito = conversación principal, no por-agente
└── settings.json       ← ✅ permissions base del equipo
```
> `rules/` NO va aquí — se ignora en silencio (§11). Es feature de `.claude/rules/` del proyecto local.

---


<!-- §17 -->
<!-- §17-quick -->
## 17. Plan + Invocation Templates — Eficiencia máxima de prompts

> Dos problemas distintos, dos soluciones distintas. El `/plan` evita gastar tokens en la dirección equivocada. Las templates eliminan la variabilidad de los prompts de invocación.

---

### Parte A — Skill `/plan`: preview antes de ejecutar

#### El problema

Invocar un agente sin saber exactamente qué va a tocar cuesta 10-20k tokens si va en la dirección equivocada. Un plan previo cuesta ~500-800 tokens en haiku y evita ese riesgo.

#### La solución: skill de solo lectura

```
.claude/skills/plan/SKILL.md
```

```markdown
---
name: plan
description: Preview de implementación antes de ejecutar cualquier agente. Invocar
  con /plan [tarea] ANTES de @especialista o @lead. Muestra archivos a tocar,
  approach, riesgo y agente recomendado. No modifica nada — solo planifica.
disable-model-invocation: false
allowed-tools: Read, Glob, Grep
---

# Plan — Preview antes de ejecutar

No modificar archivos. No escribir código. Solo planificar y reportar.

## Qué hacer
1. Leer `.claude/scope/scope-index.md` — entender estado actual
2. Usar Glob/Grep para confirmar paths reales que la tarea involucra
3. Producir el output en el formato exacto de abajo — nada más

## Output — siempre este formato, nada más

​```
PLAN: [nombre de la tarea]

Archivos a tocar:
  - [ruta/exacta.ext]   — [qué cambia en ≤8 palabras]

Approach: [1-2 líneas — qué patrón, qué señal, qué nodo]
Riesgo: [1 línea — o "ninguno"]
Agente(s): [@agente — razón en 3 palabras]
Tokens estimados: ~Xk
​```

## Reglas de estimación
- 1 agente · ≤3 archivos · sin debugging     → ~4-8k
- 1-2 agentes · 3-5 archivos                 → ~8-16k
- lead + especialistas · ≥5 archivos         → ~16-28k

## Reglas duras
- Nunca inventar rutas — confirmar con Glob antes de listar
- Si un archivo no existe todavía → marcarlo como "(nuevo)"
- Si la tarea es ambigua → UNA pregunta antes del plan, nunca asumir
```

#### Alcance del template — cuándo NO alcanza con haiku

El template de arriba (Read/Glob/Grep, formato fijo) es para el caso **mecánico**: confirmar rutas y estimar tokens de una tarea ya acotada. Es un lookup, no un juicio — por eso haiku alcanza.

Cuando la tarea tiene ambigüedad real, trade-offs (¿Redis o in-memory? ¿qué pasa si falla?), o toca un sistema nuevo sin precedente en el repo, el plan deja de ser lookup y pasa a ser **arquitectónico** — evaluar approach y riesgo requiere razonamiento, no solo confirmar que un archivo existe. Ahí el modelo correcto es sonnet, no haiku (→ criterio completo en §25).

En este entorno, esa distinción ya existe como dos herramientas separadas: la skill `/plan` (haiku, mecánica, la de este template) y el agente `Plan` — "Software architect agent for designing implementation plans... considers architectural trade-offs" — que es el caso pesado. Regla práctica: si el plan que necesitás incluye evaluar más de un approach posible, no es la skill `/plan` — es el agente `Plan`.

<!-- §17-ref -->
#### Flujo de uso

```
usuario: /plan añadir rate limiting al endpoint de login

[plan skill — ~600 tokens haiku]

PLAN: rate limiting en login

Archivos a tocar:
  - src/auth/login.ts           — agregar middleware de rate limit
  - src/middleware/rateLimit.ts — (nuevo) implementación con sliding window
  - config/limits.ts            — constantes MAX_ATTEMPTS, WINDOW_MS

Approach: middleware antes del handler, estado en Redis con TTL
Riesgo: si Redis no está disponible, definir fallback (in-memory)
Agente(s): @implementador — 3 archivos, 1 sistema
Tokens estimados: ~10k

usuario: ok

→ recién aquí se invoca @implementador
```

#### `/plan` es la norma — no la excepción

> No consume más tokens en la tarea — los **ahorra** al evitar el loop ejecutar→corregir→reejecutar. Un plan cuesta ~500-800t en haiku; una corrección de dirección cuesta 10-20k.

**Regla:** usar `/plan` por defecto. Saltarlo es la excepción que requiere justificación.

```
✅ Usar /plan (default)          ❌ Saltarse /plan (excepción)
Tarea nueva o no obvia           Fix de 1 línea ya identificado
≥2 archivos involucrados         Tarea ya planificada en sesión anterior
Riesgo de efectos secundarios    Cambio cosmético / typo / comentario
Primera vez tocando un sistema
```

#### Añadir `/plan` al dispatch de CLAUDE.md

Una sola línea al inicio del dispatch, antes que cualquier agente:

```markdown
## Dispatch
/plan [tarea] — NORMA antes de ejecutar (omitir solo para fixes triviales de 1 línea)
¿≥2 sistemas o ≥3 archivos? → @lead
...
```

No consume tokens cuando no se usa — `disable-model-invocation: false` pero solo se activa cuando el usuario lo invoca con `/plan`.

---

### Parte B — Disciplina de invocación: trabajo de Claude, no del usuario

#### El problema real

Los prompts de invocación verbosos son la principal fuente de variabilidad de tokens — pero el error no es del usuario, es del orquestador (Claude en el contexto principal).

```
❌ Claude invoca con prosa larga: explica contexto que el agente
   ya tiene en su system prompt, repite el flujo, sugiere approaches
   → el agente ignora lo redundante — tokens desperdiciados

✅ Claude invoca con formato mínimo: solo lo que el agente
   NO puede inferir del scope y los learnings
```

**El usuario habla natural. Claude comprime. El agente ejecuta.**

#### La regla — una línea en CLAUDE.md

```markdown
## Reglas duras
- Invocar agentes con formato mínimo: TASK · FILES · CONTEXT solo si no es obvio
```

Con esa regla, cuando el usuario dice *"añade rate limiting al login"*, Claude traduce internamente:

```
@lead
TASK: rate limiting — auth middleware
FILES: src/auth/login.ts, src/middleware/rateLimit.ts
```

No un párrafo. No historial. No sugerencias de approach que el agente ya conoce.

#### Qué incluir — qué omitir

| Incluir siempre | Omitir siempre |
|---|---|
| Qué construir (1 línea) | Cómo hacerlo (el agente lo sabe) |
| Archivos directamente involucrados | Archivos de contexto o arquitectura |
| Restricciones no obvias | Reglas que ya están en el system prompt |
| Resultado esperado si es ambiguo | Historial de la sesión |

#### Patrón git — el caso más optimizable

El agente git tiene un anti-pattern clásico: invocarlo varias veces por sesión. Cada invocación separada paga el cold start del agente. El patrón óptimo es **dos invocaciones fijas por sesión**:

```
Inicio de sesión:
  @git BRANCH: user/feature-nombre          → ~2-4k tokens

  [trabajo de implementación]

Fin de sesión (postmortem ya hecho):
  @git
  BRANCH: user/feature-nombre · COMMIT: tipo: desc · PR: título · VALIDADO: sí
                                                              → ~8-12k tokens
```

El flag `VALIDADO: sí` le indica al agente que saltee la confirmación y el postmortem — ya fueron hechos. Sin él, el agente para a mitad y requiere una segunda invocación, lo que duplica el costo.

| Patrón | Tokens | Cuándo |
|---|---|---|
| 2 invocaciones separadas (anti-pattern) | ~22k medido | Commit y merge en turnos distintos |
| Invocación única al final con VALIDADO | ~10-12k | Todo en un solo bloque al cerrar sesión |
| Invocación única + commit explícito en prompt | ~6-7k✓ | Medido: 7k · 5 tool calls (2026-06-02) — piso real de haiku |
| Solo merge de PR ya abierto | ~6-7k medido | `MERGE: PR #N · VALIDADO: sí` |

**Regla (2026-06-02, medido):** El piso real de haiku es **5 tool calls**. Haiku divide chains largas de `&&` para error handling — no se puede bajar a 3-4 con instrucciones. Lo optimizable son los calls de discovery (git status, git log, git diff) que no aportan nada cuando el commit viene en el prompt. Eliminarlos con sección `## PROHIBIDO` en el agente.

#### Impacto real

| Invocación | Tokens prompt | Tokens totales del agente |
|---|---|---|
| Prosa larga (15 líneas) | ~400t | ~12-20k |
| Formato mínimo (3-4 líneas) | ~80t | ~6-10k |
| Ahorro típico | ~320t overhead | ~30-50% por run |

La mayor ganancia no es el overhead del prompt — es que el agente recibe contexto limpio y no gasta Read calls extras para entender qué quiere el orquestador.

---

### Checklist §17

```
/plan skill
□ .claude/skills/plan/SKILL.md creado
□ allowed-tools: Read, Glob, Grep — sin Write ni Edit
□ disable-model-invocation: false — se activa con /plan
□ Línea en CLAUDE.md dispatch: "¿Ver plan antes?" → /plan [tarea]
□ Plan con trade-offs/ambigüedad/multi-sistema → agente Plan (sonnet), no la skill /plan (haiku)

Disciplina de invocación (Claude, no el usuario)
□ Regla en CLAUDE.md: "Invocar agentes con formato mínimo: TASK · FILES · CONTEXT solo si no es obvio"
□ Claude nunca repite en el prompt lo que ya está en el system prompt del agente
□ Reviewer recibe solo archivos directamente modificados (≤4)
□ Git: 2 invocaciones por sesión — rama al inicio, commit+push+PR+merge al final
□ Git final siempre con "VALIDADO: sí" si postmortem ya corrió — evita segunda invocación
```

---


<!-- §26 -->
<!-- §26-quick -->
<a id="26-hook-global-de-contexto"></a>

## 26. Hook global de contexto

> CLAUDE.md indica dónde buscar en la guía, pero no cuándo. Este hook inyecta automáticamente la sección relevante antes de que Claude responda — 0 tokens extra si el prompt no es relevante.

### Por qué

El problema: Claude sabe que la guía existe pero necesita inferir cuándo consultarla. A veces no lo hace. El hook detecta keywords en el prompt y extrae la sección correcta de forma automática.

| Sin hook | Con hook |
|---|---|
| Claude infiere cuándo consultar la guía | La sección relevante llega automáticamente |
| Puede omitir consulta cuando debería hacerla | 0 tokens extra si el prompt no es relevante |

`UserPromptSubmit` se ejecuta **antes** de que Claude procese el prompt. El stdout del hook se inyecta como contexto en la sesión.

<!-- §26-ref -->
### Instalación en 3 pasos

**1. Script** → `~/.claude/hooks/guia_context.py`

````python
#!/usr/bin/env python3
import json, sys, re
from pathlib import Path

# ← Ajustar con la ruta donde clonaste este repo
GUIA = Path("~/ruta/a/guia-agentes-plugins-claude-code.md").expanduser()
MAX_SECTIONS = 2    # máximo de secciones a inyectar por prompt
LINES_BUDGET = 80   # presupuesto total — se divide entre secciones encontradas
                    # (los <!-- §N-quick --> deben caber en este budget — ver §13)

# Orden importa: más específico primero.
# Se recorren TODOS los entries y se acumulan hasta MAX_SECTIONS matches.
KEYWORD_MAP = [
    # §26 — Hook global (específico — antes de §7)
    (["guia_context", "keyword_map", "inyección automática",
      "hook global", "context hook"],                                    26),
    # §29 — Contexto global propio (específico — antes de §7)
    (["contexto global", "~/.claude", "sistema propio",
      "bootstrap", "capas del contexto", "global context"],             29),
    # §5 — Agentes
    (["agente", "agent", "subagent", "disallowedtools", "maxturns",
      "memory: project", "skills:", "context:fork"],                     5),
    # §6 — Skills
    (["skill", "lifecycle", "context: fork", "ultrathink",
      "supporting files", "disable-model-invocation"],                   6),
    # §7 — Hooks (incluye permission modes y security guards)
    (["hook", "pretooluse", "posttooluse", "npm", "npx",
      "slopsquatting", "supply chain", "updatedinput",
      "sessionstart", "filechanged", "permissionrequest",
      "permiso", "permission", "guard", "credencial", "secret guard",
      "complexity router", "secret detection"],                          7),
    # §8 — Scope
    (["scope"],                                                           8),
    # §9 — Learnings
    (["learning", "curator", "postmortem"],                              9),
    # §10 — Multi-agente y worktrees
    (["multi-agente", "lead", "arquitectura", "worktree"],              10),
    # §11 — Plugin
    (["plugin", "distribuible"],                                        11),
    # §14 — Anti-overkill
    (["overkill"],                                                      14),
    # §12 — Errores comunes
    (["error común", "errores comunes", "falla silenciosa",
      "falla en silencio", "tabla de errores"],                        12),
    # §13 — Checklist de calidad
    (["checklist", "lista de verificación", "quality check"],          13),
    # §23 — Techos reales — cuándo parar de optimizar
    (["cuándo parar", "techo real", "techo de tokens",
      "parar de optimizar", "piso real"],                              23),
    # §16 — Vector Memory
    (["vector memory", "semántica"],                                    16),
    # §18 — Seguridad
    (["seguridad", "security", "injection", "traversal"],               18),
    # §19 — Testing de agentes y hooks
    (["testear", "testing", "pytest", "test de hook", "tests de hooks",
      "payload real", "subprocess test"],                              19),
    # §20 — CI/CD + Claude-en-CI
    (["ci/cd", "github action", "pipeline", "claude-code-action",
      "@claude", "pr review", "workflow yml"],                          20),
    # §21 — Observabilidad y debugging
    (["observabilidad", "observability", "stderr", "logging",
      "--debug", "traza", "session file"],                             21),
    # §24 — Factor humano
    (["factor humano", "invocar", "contexto antes"],                    24),
    # §25 — Modelo correcto
    (["haiku", "sonnet", "opus", "modelo", "effort",
      "xhigh", "security-auditor", "fable", "fast mode",
      "extended context"],                                              25),
    # §27 — Handoff + auto-compaction
    (["handoff", "snapshot", "retomar sesión", "contexto sesión",
      "compaction", "auto-compaction"],                                 27),
    # §28 — Prompt Library
    (["shortcut", "recipe", "prompt library", "/plan",
      "/nuevo-agente", "/nueva-skill", "/nuevo-hook",
      "/debug-agente", "/optimizar", "/audit-guia",
      "4 leyes", "las leyes"],                                         28),
    # §30 — Cloud Agents
    (["schedule", "cron", "routine", "cloud agent",
      "/web-setup", "ccr"],                                            30),
    # §31 — Advisor Pattern
    (["advisor pattern", "patron advisor", "sous-chef",
      "validar sin subir", "validación sin subir", "advisor"],         31),
    # §32 — Archivos no documentados (.local.md, output-styles, rules, settings.local)
    (["claude.local", "output-styles", "output styles", "rules/",
      "glob-scoped", "settings.local", "archivos que nadie",
      "domain rules", "formato de respuesta", ".local.md",
      "nadie documenta"],                                              32),
    # §22 — Prompt engineering avanzado
    (["few-shot", "enforce format", "format contract",
      "prompt engineering", "anti-alucinación",
      "system prompt budget", "output contract"],                      22),
    # §3 — Estimados + caching
    (["presupuesto", "tokens", "costo", "cache", "caching",
      "ttl", "estimado", "consumo"],                                    3),
    # §17 — Plan / Templates
    (["invocation template", "/plan skill", "plan skill"],             17),
    # §2 — Límites de tamaño
    (["presupuesto de", "límites de tamaño", "150 líneas"],             2),
    # §33 — Comandos nativos (rewind/clear/compact/fork) + integración hooks
    (["/rewind", "/clear", "/compact", "/fork", "/branch",
      "precompact", "postcompact", "checkpoint", "comandos nativos",
      "slash command"],                                                33),
]

def detect_sections(prompt: str) -> list:
    p = prompt.lower()
    seen, results = set(), []
    for keywords, n in KEYWORD_MAP:
        if n not in seen and any(k in p for k in keywords):
            results.append(n)
            seen.add(n)
            if len(results) >= MAX_SECTIONS:
                break
    return results

def extract_section(n: int, max_lines: int) -> str:
    lines = GUIA.read_text().splitlines()
    for anchor in [f"<!-- §{n}-quick -->", f"<!-- §{n} -->"]:
        try:
            start = next(i for i, l in enumerate(lines) if anchor in l) + 1
        except StopIteration:
            continue
        result = []
        for line in lines[start:]:
            if re.match(r"<!-- §\d", line):
                break
            result.append(line)
        if len(result) > 3:
            return "\n".join(result[:max_lines]).strip()
    return ""

try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)

sid = payload.get("session_id") or payload.get("transcript_path", "").split("/")[-1].replace(".jsonl", "")
seen_file = Path(f"/tmp/guia_seen_{sid}.json") if sid else None
already_seen = set(json.loads(seen_file.read_text())) if seen_file and seen_file.exists() else set()

sections = [n for n in detect_sections(payload.get("prompt", "")) if n not in already_seen]
if not sections:
    sys.exit(0)

max_lines = LINES_BUDGET // len(sections)
parts = []
for n in sections:
    content = extract_section(n, max_lines)
    if content:
        parts.append(f"[Guía §{n}]\n{content}")

if parts:
    print("\n\n".join(parts))
    if seen_file:
        seen_file.write_text(json.dumps(list(already_seen | set(sections))))
````

**2. Permisos**

```
chmod +x ~/.claude/hooks/guia_context.py
```

**3. Registrar en `~/.claude/settings.json`**

```json
"UserPromptSubmit": [
  {
    "hooks": [{
      "type": "command",
      "command": "python3 ~/.claude/hooks/guia_context.py"
    }]
  }
]
```

### Mantenimiento del KEYWORD_MAP

> **Fuente de verdad: el hook instalado** (`~/.claude/hooks/guia_context.py`). La copia embebida arriba existe para instalar desde cero — diverge en silencio si no se actualizan ambas en el mismo commit (pasó: la copia estuvo semanas con `LINES_BUDGET=120` y sin §32/§33 mientras el hook real tenía 80 y ambas secciones). `tools/audit_guia.py` verifica la sincronía en pre-commit.

El KEYWORD_MAP no se actualiza solo — cada sección nueva que no tenga entry queda fuera del sistema de inyección. El §13 (Checklist de calidad) ya incluye el recordatorio, pero el protocolo es:

**Al crear §N nuevo:**
1. Identificar 3-5 keywords que un usuario escribiría naturalmente al preguntar sobre ese tema
2. Agregar el entry en orden de especificidad (más específico arriba):
```python
# §N — Nombre sección
(["keyword1", "keyword2", "keyword3"], N),
```
3. Testear con `echo '{"prompt": "frase con keyword"}' | python3 ~/.claude/hooks/guia_context.py | head -1`

**Qué hace un buen keyword:**
- Lo que el usuario escribe, no el título de la sección (`"caching"` > `"prompt caching"` > `"estimados de consumo"`)
- Específico al tema para evitar falsos positivos (`"advisor pattern"` > `"advisor"` si el término es ambiguo)
- En el idioma del usuario (si mezclan ES/EN, incluir ambos)

**Budget adaptativo — cómo funciona:**
```python
LINES_BUDGET = 80   # presupuesto total fijo
# 1 sección encontrada → 80 líneas (máximo detalle)
# 2 secciones encontradas → 40 líneas cada una (80 total)
```

Si una sección quick tiene < 40 líneas, se sirve completa. El budget solo limita secciones largas — no trunca lo que ya es conciso.

### Deduplicación por sesión

Sin deduplicación, un tema recurrente (ej. "handoff") inyecta la misma sección en cada turno — ~1,500 tokens desperdiciados por mensaje. El hook trackea qué secciones ya se inyectaron en `/tmp/guia_seen_{session_id}.json`.

| Situación | Comportamiento |
|---|---|
| §27 pedido, sesión nueva | Inyecta §27, guarda en seen |
| §27 pedido, ya en seen | `sys.exit(0)` — 0 bytes, 0 tokens |
| Falla al leer archivo temp | `already_seen = set()` — funciona como antes |

**Impacto en sesión de 15 turnos sobre handoff:**
- Antes: 15 × ~1,500 tokens = ~22,500 tokens extra
- Después: 1 × ~1,500 tokens = ~1,500 tokens extra

El archivo temp se elimina automáticamente al reiniciar el sistema. No requiere limpieza manual.

### Checklist §26

```
□ guia_context.py creado en ~/.claude/hooks/
□ chmod +x aplicado
□ UserPromptSubmit registrado en ~/.claude/settings.json
□ Prompt con "agente" → §5 inyectado como contexto
□ Prompt cruzado ("agente" + "hook") → §5 + §7 inyectados
□ Prompt sin keywords → sin inyección (0 bytes stdout)
□ Misma keyword en turno 2+ → sin inyección (deduplicación por sesión)
□ Nueva sección → entry en KEYWORD_MAP + test de smoke
```

### Plugin-level UserPromptSubmit — dos tiers de keywords

Cuando el hook de contexto es para un **dominio específico** (no general como guia_context.py), los keywords genéricos (`new`, `view`, `component`) disparan en cualquier conversación y generan ruido. Patrón correcto: detección en dos tiers.

**Tier 1 — símbolos exclusivos del dominio** (fire siempre que aparezcan):
```python
_DOMAIN_SYMBOLS = re.compile(
    r'ExclusiveTerm1|ExclusiveTerm2|...'
    # ← Solo términos que NO aparecen fuera del dominio
    # DesignSystemKit: @CatalogElementMacro, ShimmerView, NaturalHeightLayout...
)
```

**Tier 2 — acción + término de dominio en proximidad** (≤50 chars entre ellos):
```python
_DOMAIN_CONTEXT = re.compile(
    r'(crea[r]?|nuevo|new|add|implement).{0,50}(domainTerm)|'
    r'(domainTerm).{0,50}(crea[r]?|nuevo|new|add|es\s+un)',
    re.IGNORECASE | re.DOTALL
)
```

Si ningún tier matchea → no inyectar (silencio es correcto). Output: **plain stdout**, no `json.dumps({"systemMessage": ...})`. La doc oficial confirma que stdout de `UserPromptSubmit` va a `additionalContext` del contexto de Claude — sin mostrarse al usuario como mensaje separado.

```python
# ✅ Plain stdout — va a additionalContext silenciosamente
print(f"[Dominio context]\n{content}")

# ❌ systemMessage — se muestra al usuario como mensaje visible
print(json.dumps({"systemMessage": content}))
```

> **[2026-06-22] design-ios:** Keywords genéricos (`new`, `view`, `component`, `swift`) en hub hook inyectaban el triage de capas en conversaciones de git, docs y cualquier cosa con esas palabras. Fix: Tier 1 con nombres exclusivos del sistema (`@CatalogElementMacro`, `ShimmerView`, `AppTabView`...) + Tier 2 con proximidad acción+capa (`"crea un atom"`, `"nuevo molecule"`). Ahora solo dispara cuando el dominio es inequívoco.

---


<!-- §27 -->
<!-- §27-quick -->
<a id="27-handoff-protocol"></a>

## 27. Handoff Protocol — Preservar contexto entre sesiones

> Sesiones largas degradan la calidad de razonamiento. Este protocolo preserva el estado exacto en un snapshot estructurado y lo retoma en sesión nueva sin fricción — cero llamadas de API extra, cero overhead por turno.

### El problema

Claude Code no tiene memoria entre sesiones. A medida que el contexto se llena, la calidad del razonamiento baja antes de que el usuario lo note. El degradado es silencioso.

### Por qué es LowCost

La trampa obvia es llamar `/v1/messages/count_tokens` para saber cuándo avisar. Eso es gratis en dinero pero agrega una llamada de API por turno — latencia real.

La solución: Claude Code **ya calcula** `context_window.used_percentage` y lo entrega al comando `statusLine` en el JSON de stdin. Leer ese número es una operación de archivo. Costo = 0.

| Enfoque | Overhead |
|---|---|
| Token counting API por turno | 1 HTTP call/turno (~200ms latencia) |
| `statusLine` + archivo local | Lectura de archivo — cero |

### Arquitectura

```
statusLine (cada evento)
  → lee context_window.used_percentage del JSON de Claude Code
  → escribe ~/.claude/ctx_pct.txt
  → muestra barra de progreso en la UI

Stop hook (cada respuesta de Claude)
  → lee ctx_pct.txt
  → si ≥ 70%: dialog nativo del OS (una sola vez por sesión)
    → No: continúa normalmente
    → Sí: emite {"decision": "block", "reason": "HANDOFF REQUESTED + contexto git"}
          Claude recibe el reason en el mismo turno e invoca el skill /handoff

/handoff skill
  → Claude compone snapshot internamente (no se muestra en chat)
  → Bash escribe a ~/.claude/handoffs/{repo}/YYYY-MM-DD_HHmm.md + latest.md
  → .gitignore actualizado automáticamente
  → snapshot copiado al clipboard
  → Claude imprime una línea de confirmación en el chat
```

<!-- §27-ref -->
### Componentes

| Archivo | Rol |
|---|---|
| `CLAUDE.md` | Triggers manuales (`handoff`, `snapshot`, `pausa`) + resume behavior |
| `commands/handoff.md` | Skill `/handoff` — compone snapshot internamente, escribe a disco vía Bash, imprime una línea de confirmación |
| `hooks/statusline-context.sh` | Barra de progreso con niveles y mensajes |
| `hooks/handoff-monitor.sh` | Detecta 70%, muestra dialog cross-platform; en confirmación emite `decision: block` con "HANDOFF REQUESTED" para disparar el skill en el mismo turno |

### Dialog cross-platform

El Stop hook detecta el OS y usa la herramienta nativa:

```bash
case "$OSTYPE" in
  darwin*)   osascript     ;;   # macOS — built-in
  linux*)    zenity/kdialog;;   # GNOME / KDE
  msys*|cygwin*) powershell;;  # Windows Git Bash / WSL
  *)         systemMessage ;;  # fallback en el chat
esac
```

### Barra de progreso

El `statusLine` muestra un indicador visual con escalada de urgencia:

```
🥬 [██░░░░░░░░] 20% — fresco como lechuga
😎 [███░░░░░░░] 35% — tranqui
🔥 [█████░░░░░] 52% — se calienta la cosa
👻 [██████░░░░] 63% — en cualquier momento me voy en la vola'
🔪 [███████░░░] 74% — me pase po          ← dialog dispara aquí
💀 [████████░░] 83% — ¿qué hacíamos?
🆘 [█████████░] 92% — handoff altiro weón
```

Los colores ANSI (verde/amarillo/rojo) coinciden con el nivel de urgencia.

### Snapshot template

```markdown
## Snapshot de Handoff
**Fecha:** [YYYY-MM-DD HH:MM]
**Repo / Proyecto:** [nombre]
## Objetivo
## Completado
## En Progreso
## Próximos Pasos
## Decisiones Técnicas
## Blockers
## Contexto Técnico
```

Para retomar: pega el snapshot al inicio de sesión nueva. Claude confirma el objetivo antes de continuar.

### Instalación

```bash
git clone https://github.com/f3kpclon/claude-code-handoff handoff-project
cd handoff-project
bash install.sh   # idempotente — seguro de re-ejecutar
# Reiniciar Claude Code
```

### Seguridad y CI

Este proyecto instala hooks que corren en **cada sesión de Claude de cada usuario**. Un PR malicioso en `hooks/` o `install.sh` es un supply chain attack real.

**GitHub Actions** (`.github/workflows/ci.yml`) — corre en cada PR hacia `main`:

| Job | Qué hace |
|---|---|
| `ShellCheck` | Lint de todos los `.sh` — errores y patrones inseguros |
| `Tests` | `bash test.sh` — 16 aserciones, falla si install.sh aborta |
| `Security Scan` | Detecta patrones peligrosos nuevos en `hooks/`, `install.sh`, `commands/`: `curl`, `wget`, `base64 -d`, `/dev/tcp`, `nc`, `python3 -c.*exec` |

**Nota:** `set -euo pipefail` en `install.sh` hace que los tests fallen si el atacante inyecta un `curl` que no responde — doble protección sin código extra.

**Branch protection** configurada vía API:
- PRs obligatorios con aprobación del codeowner
- Los 3 checks deben pasar antes de mergear
- `enforce_admins: false` — el owner puede hacer push directo
- `CODEOWNERS` en `.github/CODEOWNERS` — auto-request de review al owner

```bash
# Configurar branch protection vía gh CLI (para forks)
gh api repos/{owner}/{repo}/branches/main/protection \
  --method PUT --input - <<'EOF'
{
  "required_status_checks": {"strict": true, "contexts": ["ShellCheck","Tests","Security Scan"]},
  "enforce_admins": false,
  "required_pull_request_reviews": {"required_approving_review_count": 1, "require_code_owner_reviews": true, "dismiss_stale_reviews": true},
  "restrictions": null
}
EOF
```

### Auto-compaction — qué resume, qué pierde

Claude Code comprime automáticamente el historial cuando el contexto se acerca al límite. Ocurre **sin aviso visual** — la calidad del razonamiento baja antes de que el usuario lo note.

**Qué hace la compaction:** resume el historial previo en un bloque comprimido y mantiene los mensajes recientes sin comprimir. El bloque comprimido es menos detallado que el original.

**Qué sobrevive (y qué no):**

| Tipo de información | ¿Sobrevive? | Por qué |
|---|---|---|
| El objetivo principal de la sesión | ✅ | Suficientemente prominente en el resumen |
| Código escrito en disco | ✅ | No depende del contexto — está en el filesystem |
| Decisiones de arquitectura mencionadas una vez | ❌ | Se resume a nivel alto, el detalle se pierde |
| Gotchas y constraints del proyecto | ❌ | Se pierde si no está en CLAUDE.md |
| Errores y sus fixes | ⚠️ | Solo si fueron recientes (no en la parte comprimida) |

**Preparar el contexto para sobrevivir la compaction:**
1. Constraints críticos → CLAUDE.md, no solo en el chat
2. Decisiones one-shot → checkpoint explícito en el output del agente: `Checkpoint: [decisión] · Razón: [por qué]`
3. Contexto ≥ 70% → activar `/handoff` antes de que la compaction ocurra sola

**Señal de que ya ocurrió:** Claude "olvida" algo mencionado hace más de ~20 mensajes. No es alucinación — el dato quedó en la parte comprimida y no sobrevivió el resumen. Fix: reinjectar explícitamente o hacer handoff.

### Regla LowCost

> Si Claude Code ya calcula el dato que necesitas, léelo — no lo recalcules. El `statusLine` JSON tiene `context_window.used_percentage` listo. Úsalo.

### Checklist §27

```
□ bash install.sh ejecutado
□ Claude Code reiniciado
□ statusLine visible en la barra inferior con barra de progreso
□ /handoff escribe snapshot a disco sin mostrarlo en chat
□ /handoff imprime una línea de confirmación en el chat
□ Snapshots en ~/.claude/handoffs/{repo}/ (lo crea la skill — coincide con el comando de resume del CLAUDE.md global)
□ latest.md siempre disponible para retomar rápido
□ Al llegar a 70%: dialog nativo aparece
□ "Sí" en dialog → próximo mensaje genera snapshot automático
□ Snapshot pegado en sesión nueva → Claude confirma objetivo
□ CI pasa en main (ShellCheck + Tests + Security Scan)
□ Branch protection activa — PRs obligatorios para colaboradores
□ CODEOWNERS configurado — owner recibe auto-request en cada PR
```

---


<!-- §28 -->
<!-- §28-quick -->
## 28. Prompt Library — shortcuts para Claude Code

> Estos no son comandos mágicos. Funcionan porque Claude lee lenguaje natural. El `/` es convención de consistencia — la misma razón por la que un chef tiene nombres fijos para sus técnicas aunque podría describirlas con otras palabras. Cuando están registrados como skills (`SKILL.md`), ganan `allowed-tools`, contexto dinámico y control de invocación. Como texto plano, funcionan igual pero sin esas garantías.

**Tags usados en esta sección:**

| Tag | Significado |
|---|---|
| `READ-ONLY` | No modifica archivos — seguro sin `/plan` previo |
| `HAIKU ONLY` | Optimizado para haiku — no gastar sonnet en esto |
| `SESSION ONLY` | El output es para esta sesión, no persiste entre sesiones |
| `OVERLAPS /X` | Se superpone con otro shortcut — elegir el más específico |
| `USE SPARINGLY` | Costoso en tokens — usar con criterio |

---

### Shortcuts

#### `/plan` · `READ-ONLY` · `HAIKU ONLY`

Preview de implementación antes de ejecutar cualquier agente. Muestra archivos a tocar, approach, riesgo, agente recomendado y tokens estimados. No modifica nada.

```
/plan añadir rate limiting al endpoint de login
```

> Skill completa en §17. Regla: usarlo por defecto — saltarlo requiere justificación.

---

#### `/handoff` · `SESSION ONLY`

Genera un snapshot de la sesión actual y lo guarda en disco silenciosamente. Usar antes de cerrar o cuando el contexto se acerca al límite.

```
/handoff
```

> Skill completa en §27. El snapshot en `.claude/handoffs/latest.md` permite retomar sin preguntas.

---

#### `/nuevo-agente [nombre]` · `HAIKU ONLY`

Genera el frontmatter completo + estructura mínima para un agente nuevo. Incluye model, tools, description como trigger list, y sección de Gotchas.

```
/nuevo-agente security-auditor
Tarea: audit de seguridad en PRs con cambios de auth
Modelo: opus (one-shot, costo de error alto)
Tools: Read, Glob, Grep
```

---

#### `/nueva-skill [tipo]` · `HAIKU ONLY`

Genera la estructura correcta según el tipo de skill. Tipos: `hub`, `referencia`, `fork`.

```
/nueva-skill referencia
Nombre: api-conventions
Propósito: patrones de endpoints REST para este codebase
```

```
/nueva-skill fork
Nombre: deep-research
Propósito: investigar un tema en el codebase sin contaminar el hilo
```

<!-- §28-ref -->
---

#### `/nuevo-hook [evento]` · `HAIKU ONLY`

Genera el Python skeleton correcto para el evento pedido. Incluye try/except, re.split para primer comando, y el JSON de respuesta correcto para ese evento.

```
/nuevo-hook PreToolUse
Bloquear: npm install con paquetes nuevos sin --ignore-scripts
```

```
/nuevo-hook SessionStart
Inyectar: branch actual y archivos modificados al iniciar
```

---

#### `/debug-agente [nombre]` · `READ-ONLY` · `OVERLAPS /plan`

Checklist de diagnóstico cuando un agente falla, hace cosas inesperadas o es más caro de lo esperado. Revisa description, tools, model, hooks y output format.

```
/debug-agente reviewer
Síntoma: aprueba PRs sin revisar los archivos de test
```

---

#### `/optimizar [agente]` · `READ-ONLY` · `USE SPARINGLY`

Analiza el costo de un agente y sugiere las optimizaciones con mayor ROI. Sigue el orden de §23: output format → discovery calls → bash chaining → system prompt → scope.

```
/optimizar lead
Costo actual: ~28k tokens por sesión
Esperado: ~14k
```

---

#### `/audit-guia` · `READ-ONLY` · `HAIKU ONLY`

Valida el proyecto actual contra el checklist §13. Revisa CLAUDE.md, agentes, skills, hooks y scope. Lista solo las violaciones — no repite lo que está bien.

```
/audit-guia
```

---

### Recipes — shortcuts apilados

> Un shortcut solo es bueno. Dos apilados en secuencia son afilados. Tres son un sistema.

#### "Ejecutar con seguridad"
```
/plan → @agente → /handoff
```
Planificar antes de ejecutar, ejecutar con agente correcto, capturar estado antes de cerrar. El orden importa: sin `/plan`, el agente puede ir en la dirección equivocada. Sin `/handoff`, la próxima sesión empieza desde cero.

#### "Ciclo de mejora"
```
/debug-agente → /optimizar
```
Primero entender por qué falla (síntoma → causa), luego reducir el costo. Hacerlos al revés optimiza un agente roto.

#### "Crear y testear"
```
/nueva-skill fork → /plan → @agente
```
Crear la skill de investigación, planificar con ella activa para confirmar que el scope es correcto, ejecutar.

#### "Construir bien desde el arranque"
```
/nuevo-agente → /plan → /audit-guia
```
Generar el agente nuevo, planificar la primera tarea para validar que el design es correcto, auditar contra el checklist antes de usarlo en producción.

---

### Las 4 Leyes — adaptadas a Claude Code

*(Originalmente de commandlib — mapeadas a secciones de esta guía)*

**Ley 1 — Especificidad gana a shortcuts**
Un prompt con scope + output + criterio de éxito vale más que 5 shortcuts en secuencia. Los shortcuts son atajos para llegar al contexto correcto, no sustitutos del contexto. → §24

**Ley 2 — Los constraints hacen mejor a Claude**
`tools` mínimas, `model` explícito, output format forzado. Cada constraint que agregás a un agente es un token que Claude no gasta en decidir. → §5, §22

**Ley 3 — El contexto es la ventaja**
El hook de `SessionStart` que inyecta branch + estado pesa más que cualquier shortcut. El contexto que llega automáticamente es el que nunca se olvida. → §26

**Ley 4 — Iterar, no reiniciar**
Cuando algo sale mal, responder con lo que está incorrecto — no reescribir el prompt. El hilo es el contexto acumulado. `/handoff` antes de cerrar: la próxima sesión arranca donde dejaste. → §27

---


<!-- §29 -->
<!-- §29-quick -->
## 29. Contexto global propio — construir tu sistema

> Sin contexto global, Claude es un consultor que llega cada lunes sin cuaderno: vos explicás de nuevo quién sos, qué filosofía seguís y qué no debe tocar. Con contexto global, es el mismo consultor pero con sus reglas interiorizadas, sus herramientas en el bolsillo y su cuaderno de aprendizajes abierto. El cliente no explica — trabaja.

### Las 4 capas — qué hace cada una

```
~/.claude/CLAUDE.md          ← reglas que aplican siempre (costo fijo justificado)
~/.claude/skills/            ← procedimientos bajo demanda (0 tokens hasta invocar)
~/.claude/settings.json      ← automatizaciones y guards por evento
memory/                      ← aprendizajes acumulados entre sesiones
```

| Capa | Cuándo construirla | Si no existe |
|---|---|---|
| `CLAUDE.md` global | Siempre — es la primera | Claude improvisa filosofía y reglas en cada sesión |
| Skills globales | Cuando CLAUDE.md tiene ≥5 líneas explicando un procedimiento | Repetís las mismas instrucciones en cada sesión |
| `UserPromptSubmit` hook | Cuando tenés un cuerpo de conocimiento que Claude debería consultar automáticamente | Claude sabe que la guía existe pero no siempre la consulta |
| `PreToolUse` hook | Cuando hay acciones que Claude no debe poder tomar en **ningún** proyecto | Un agente mal configurado puede ejecutar `npm install` sin freno |
| Memoria persistente | Cuando hay feedback que querés que persista entre sesiones | Corregís el mismo error dos veces |

### Orden de construcción — árbol de decisión

```
¿Primera vez configurando? → Empezar con CLAUDE.md global (5 minutos)

¿Tenés conocimiento específico que Claude debería consultar sin pedírselo?
  Sí → UserPromptSubmit hook (guia_context.py o equivalente) — §26
  No → saltear por ahora

¿Hay procedimientos que pegás repetidamente en el chat?
  Sí → Skills globales en ~/.claude/skills/ — §6
  No → saltear

¿Hay acciones irreversibles que Claude no debe tomar en ningún proyecto?
  Sí → PreToolUse hook global (npm guard, git push guard) — §7
  No → saltear

¿Hay patrones de feedback que querés recordar en futuras sesiones?
  Sí → Memoria persistente — inicializar MEMORY.md
  No → saltear
```

> **Regla de scope:** si dudás entre global y proyecto, va en el proyecto. El scope global contamina todos los contextos — un hook global mal calibrado genera ruido en proyectos donde no aplica.

### Separación `~/.claude/` vs `.claude/`

| Dónde | Aplica a | Ejemplos correctos |
|---|---|---|
| `~/.claude/CLAUDE.md` | Todos los proyectos | Filosofía LowCost, reglas de modelo, shortcuts |
| `~/.claude/skills/` | Todos los proyectos | `/plan`, `/handoff`, `/nuevo-agente` |
| `~/.claude/hooks/` + `settings.json` | Todos los proyectos | npm guard, guia_context.py, handoff hooks |
| `.claude/CLAUDE.md` | Este proyecto | Stack, agentes, reglas específicas del repo |
| `.claude/agents/` | Este proyecto | Agentes del dominio |
| `.claude/skills/` | Este proyecto | Skills del proyecto |

<!-- §29-ref -->

### Bootstrap desde cero — 5 pasos

**Paso 1 — CLAUDE.md global** (5 min)

```markdown
# Tu nombre — Reglas globales

## Filosofía
[tu filosofía de trabajo — 3-5 líneas máximo]

## Conocimiento de referencia
`/ruta/a/tu/guia-o-docs.md`
Solo la sección relevante: sed -n '/<!-- §N -->/,/<!-- §[0-9]/p' <archivo>

## Principios de operación
- [principio 1]
- [principio 2]
```

**Paso 2 — Hook de inyección automática** (15 min)

Adaptar `guia_context.py` (§26) con tu propio `KEYWORD_MAP` apuntando a tus docs. Registrar en `settings.json` bajo `UserPromptSubmit`.

**Paso 3 — Skills para procedimientos repetibles** (10 min por skill)

Identificar qué instrucciones pegás más de 2 veces por semana. Cada una → `~/.claude/skills/<nombre>/SKILL.md` con `disable-model-invocation: true`.

**Paso 4 — Guards para acciones irreversibles** (20 min)

Un `PreToolUse` global con las acciones que nunca deberían ocurrir en ningún proyecto: `npm install <pkg>` sin `--ignore-scripts`, push directo a ramas protegidas, `rm -rf` sin confirmación.

**Paso 5 — Inicializar memoria** (5 min)

```bash
mkdir -p ~/.claude/projects/<proyecto>/memory
echo "# Memory Index" > ~/.claude/projects/<proyecto>/memory/MEMORY.md
```

Primera entry: feedback de la filosofía de trabajo — el patrón que más frecuentemente tenés que recordarle a Claude.

---

### Anti-patrones del contexto global

| Anti-patrón | Consecuencia | Fix |
|---|---|---|
| Contenido de un proyecto específico en `~/.claude/CLAUDE.md` | Contamina todos los proyectos — Claude menciona el stack de un proyecto en contextos donde no aplica | Mover al `.claude/CLAUDE.md` del proyecto |
| Skills globales largas (> 200 líneas) | El budget de descripciones se comparte — una skill pesada desplaza a otras en proyectos distintos | Dividir en SKILL.md + reference.md; o hacer skill de proyecto |
| `PreToolUse` global demasiado específico | Genera ruido en proyectos donde la condición no aplica | Guard de proyecto en `.claude/settings.json` |
| Duplicar reglas en CLAUDE.md global y de proyecto | Costo doble, inconsistencia cuando cambia una y no la otra | Una fuente de verdad — si aplica siempre → global; si es del proyecto → proyecto |
| Muchas skills globales con `disable-model-invocation: false` | Compiten con skills del proyecto, saturan el budget de descripciones | Solo el hub o skills de conocimiento general en `false`; el resto en `true` |

### El sistema de esta guía como ejemplo real

```
~/.claude/
├── CLAUDE.md                    # filosofía + índice de la guía + principios de operación
├── settings.json                # hooks: SessionStart / UserPromptSubmit / PreToolUse / Stop / PostToolUse
├── skills/
│   ├── handoff-protocol/        # formato del snapshot (§27) — disable:false, Claude lo carga solo
│   ├── handoff/                 # genera el snapshot (§28) — disable:true, el usuario lo invoca
│   ├── plan/                    # preview antes de ejecutar (§17/§28) — haiku
│   ├── nuevo-agente/            # scaffold de agentes (§28) — haiku
│   ├── nueva-skill/             # scaffold de skills (§28) — haiku
│   ├── nuevo-hook/              # scaffold de hooks (§28) — haiku
│   └── audit-guia/              # valida contra §13 (§28) — haiku
└── hooks/
    ├── guia_context.py          # UserPromptSubmit → inyección automática de §N (§26)
    ├── npm_guard.py             # PreToolUse → supply chain + slopsquatting (§7)
    ├── handoff-inject.sh        # UserPromptSubmit → inyecta handoff pendiente (§27)
    ├── handoff-monitor.sh       # Stop → monitorea necesidad de handoff (§27)
    └── inject-index.sh          # SessionStart → índice del codebase
```

Cada pieza tiene su sección de referencia. Nada se inventó solo — todo se construyó desde los principios documentados en la guía.

### Checklist §29

```
□ ~/.claude/CLAUDE.md existe con filosofía + índice de conocimiento
□ UserPromptSubmit hook conecta CLAUDE.md con el conocimiento específico
□ Skills en disable-model-invocation: true — el usuario controla cuándo se invocan
□ PreToolUse guards solo para acciones verdaderamente globales
□ Nada de contenido de proyecto específico en el scope global
□ Memoria inicializada con al menos una entry de filosofía
□ Separación clara: regla siempre activa → CLAUDE.md; procedimiento → skill; garantía → hook
```

---


<!-- §30 -->
<!-- §30-quick -->
## 30. Cloud Agents programados — /schedule y /web-setup

> Un hook local corre en tu máquina. Un cloud agent corre en la nube de Anthropic con un checkout limpio del repo — sin acceso a tu filesystem, sin tus variables de entorno, sin tus plugins instalados. Son dos cosas distintas. Úsalos para cosas distintas.

### Las 3 reglas

1. **Cloud agents ≠ hooks locales** — los CCR (Claude Code Routines) tienen acceso al repo GitHub, no a `/Users/`. Si la tarea necesita tu filesystem → hook local. Si puede correr desde un clone fresco → CCR.
2. **GitHub primero** — sin `/web-setup` el checkout falla silenciosamente. Conectar GitHub es el paso 0 antes de crear cualquier routine.
3. **Prompt self-contained** — el agente arranca sin contexto, sin tu CLAUDE.md, sin tus plugins. El prompt debe incluir todo lo que necesita saber.

### Cuándo usar cloud agents vs alternativas

| Caso | Solución correcta |
|---|---|
| Tarea periódica sobre el repo (health check, análisis de código) | CCR — `/schedule` |
| Curar learnings per-project (en `.claude/learnings/`) | Hook local — CCR no tiene acceso al filesystem local |
| Curar learnings en el repo (si están en git) | CCR — clona el repo y los lee directamente |
| Acción automática en respuesta a un evento del usuario | Hook local `UserPromptSubmit`/`PostToolUse` |
| Tarea única programada ("mañana a las 9am") | CCR con `run_once_at` |
| Acción que necesita acceso al filesystem local | Hook local — los CCR no tienen acceso |
| Monitor de CI/CD o builds externos | CCR — corre en nube, no bloquea tu sesión |

### Modelos recomendados para CCR

| Tarea | Modelo |
|---|---|
| Mantenimiento / curation / deduplicación | `claude-haiku-4-5` |
| Análisis de código / PR review automático | `claude-sonnet-5` |
| Tareas complejas multi-step | `claude-sonnet-5` |

### /web-setup — conectar servicios OAuth

Necesario una vez antes de crear routines que accedan a repos privados:

```
/web-setup          # en el prompt de Claude Code — abre flujo OAuth
```

Conecta: GitHub (para checkout del repo), Google Drive, y otros servicios MCP disponibles.
Sin GitHub conectado → el campo `sources: [{git_repository: {url: ...}}]` del CCR falla al clonar.

<!-- §30-ref -->

### Estructura de un routine (create body)

```json
{
  "name": "nombre-descriptivo",
  "cron_expression": "0 0 1 * *",
  "enabled": true,
  "job_config": {
    "ccr": {
      "environment_id": "env_XXXXX",
      "session_context": {
        "model": "claude-haiku-4-5",
        "sources": [
          {"git_repository": {"url": "https://github.com/org/repo"}}
        ],
        "allowed_tools": ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]
      },
      "events": [{
        "data": {
          "uuid": "<lowercase v4 uuid generado>",
          "session_id": "",
          "type": "user",
          "parent_tool_use_id": null,
          "message": {"role": "user", "content": "PROMPT SELF-CONTAINED AQUÍ"}
        }
      }]
    }
  }
}
```

**Cron expresiones útiles:**

| Cuándo | Expresión (UTC) |
|---|---|
| Diario a medianoche | `0 0 * * *` |
| Primer día del mes | `0 0 1 * *` |
| Cada lunes 9am UTC | `0 9 * * 1` |
| Cada 2 horas | `0 */2 * * *` |

Mínimo intervalo: 1 hora. `/30 * * * *` es rechazado.

### Cómo invocar desde Claude Code

```
/schedule    # skill — Claude guía la creación de la routine
```

Internamente usa `RemoteTrigger` (tool deferred — cargar con `ToolSearch select:RemoteTrigger`):

```
RemoteTrigger {action: "list"}               # listar routines
RemoteTrigger {action: "create", body: {...}} # crear
RemoteTrigger {action: "run", trigger_id: "trig_XXX"} # ejecutar ahora
```

Ver/gestionar routines: https://claude.ai/code/routines

### Checklist de prompt para CCR

Un prompt de CCR debe responder estas preguntas sin asumir contexto externo:

```
□ ¿Qué archivos leer? (rutas relativas al repo clonado)
□ ¿Qué condición activa la acción? (ej: si líneas > 150)
□ ¿Qué hacer exactamente? (no "curar" — describir los pasos concretos)
□ ¿Qué hacer si la condición NO se cumple? (output esperado + stop)
□ ¿Cómo terminar? (commit + mensaje concreto / output a stdout)
□ ¿Conservador o agresivo? (cuando hay duda, ¿mantener o eliminar?)
```

### Anti-patrones de CCR

| Anti-patrón | Consecuencia | Fix |
|---|---|---|
| Prompt que asume plugins instalados (`@design-curador`) | El CCR no tiene los plugins del usuario | Describir la tarea directamente en el prompt |
| Rutas absolutas (`/Users/felix/...`) | El CCR clona en `/tmp/...` — ruta no existe | Usar rutas relativas al repo |
| Sin GitHub conectado | Checkout falla sin mensaje claro | Correr `/web-setup` antes de crear el routine |
| Routine en sonnet para tareas simples | Costo 5× innecesario | Haiku para mantenimiento, sonnet para análisis |
| Prompt vago ("mejora el código") | El agente improvisa → resultado impredecible | Criterios explícitos: condición + acción + stop |

### Checklist §30

```
□ /web-setup corrido — GitHub (u otro servicio) conectado
□ Repo es público o GitHub App instalada en él
□ Modelo elegido según complejidad (haiku para mantenimiento)
□ Prompt incluye: qué leer, condición, acción concreta, condición de stop
□ Rutas en el prompt son relativas al repo (no absolutas)
□ Cron expression en UTC — confirmada conversión desde timezone local
□ Routine visible en https://claude.ai/code/routines
□ `run_once_at` para tareas únicas en lugar de `cron_expression`
```


<!-- §33 -->
## 33. Comandos nativos — rewind, clear, compact, fork y su integración con agentes/hooks

> `/rewind`, `/clear` y `/compact` no tienen API — son CLI-only, atados a que un humano (o Claude decidiendo escribirlos como respuesta) los tipee. Pero otro grupo de comandos nativos SÍ está diseñado para orquestar agentes (`/fork`, `/branch`, `/goal`, `/batch`, `/loop`) y los hooks SÍ tienen puntos de integración reales alrededor de sesión y compactación (`SessionStart`, `PreCompact`, `PostCompact`). Esta sección separa lo uno de lo otro — verificado contra doc oficial, no supuesto.

### Tabla — comandos que importan cuando construís

| Comando | Qué hace | Cuándo usarlo |
|---|---|---|
| `/rewind` (alias `/checkpoint`, `/undo`) | Revierte código y/o conversación a un punto anterior, o resume desde ahí | Un agente rompió algo y querés volver sin perder el resto de la sesión |
| `/clear` (alias `/reset`, `/new`) | Contexto vacío nuevo; la conversación anterior queda disponible en `/resume` | Cambiar de tarea sin arrastrar contexto irrelevante |
| `/compact [instructions]` | Resume la conversación actual para liberar espacio, sin abandonarla | Contexto largo pero seguís en la misma tarea — podés darle foco: `/compact enfocate en los cambios de auth` |
| `/resume [session]` (alias `/continue`) | Retoma una sesión anterior por ID o nombre | Volver a un `/branch` o a una sesión pausada |
| `/branch [name]` | Copia la conversación en este punto y cambia a ella; el original queda intacto | Probar una dirección distinta sin arriesgar el estado actual |
| `/fork <directive>` | Spawnea un subagente en background que **hereda toda la conversación** y trabaja la directiva mientras vos seguís | Delegar una tarea lateral sin cambiar de contexto vos — el resultado vuelve solo al hilo principal |
| `/goal [condition]` | Claude sigue trabajando entre turnos hasta cumplir la condición | Loop autónomo acotado, sin montar `/loop` externo |
| `/context [all]` | Visualiza uso de contexto por bloque | Diagnóstico antes de decidir `/compact` vs `/clear` |
| `/batch <instruction>` | Descompone un cambio grande en 5-30 unidades, un subagente por unidad, cada uno en su propio worktree | Cambios cross-codebase demasiado grandes para un agente — ver §10 |
| `/loop [interval] [prompt]` | Corre un prompt repetidamente, con pacing propio si se omite el intervalo | Polling o tareas recurrentes dentro de la sesión — ver skill `loop` |
| `/agents` | Gestiona subagentes configurados | Alta/baja de subagentes del proyecto |
| `/schedule` (alias `/routines`) | Rutinas cloud con cron, fuera de la sesión interactiva | Automatización que no depende de la sesión abierta — ver §30 |

### Lo que SÍ se integra con agentes/skills/hooks (documentado)

**`/fork` y `/branch` SON la forma nativa de "comando como agente".** No hace falta inventar nada: `/fork` literalmente spawnea un subagente en background con el checkpoint completo de la conversación heredado — es la respuesta real a "quiero que un agente parta de este punto exacto".

**Hook `PreCompact`** — se dispara antes de compactar (matcher `manual` o `auto`), recibe `compaction_trigger` en el input, y **puede bloquear** (`decision: block`) o simplemente correr un script antes de que el contexto se pierda:

```json
{
  "hooks": {
    "PreCompact": [
      {
        "matcher": "auto",
        "hooks": [{ "type": "command", "command": "./scripts/archive-context.sh" }]
      }
    ]
  }
}
```
Patrón real: archivar el estado de un agente largo (checkpoints de delegación, ver §9) antes de que `/compact` automático los resuma y se pierda detalle.

**Hook `SessionStart`** — matcher `startup|resume|clear|compact` distingue **cómo** arrancó la sesión. Sirve para inyectar contexto distinto según el caso: después de un `/clear` no hace falta re-explicar el proyecto (ya está en CLAUDE.md), pero después de un `/compact` puede convenir reinyectar un gotcha que se resumió de más.

**Skills** — un skill es texto que Claude lee, así que puede *recomendar* terminar con `/compact` o `/fork` como parte del flujo ("una vez migrado esto, corré `/compact` antes de seguir"), pero es Claude quien decide emitirlo — no hay forma de forzarlo desde el frontmatter.

### Lo que NO se puede (verificado contra doc oficial)

- Ningún hook, skill o llamada del SDK puede **forzar** `/rewind`, `/clear` o `/compact` — son CLI-only, requieren que un humano los tipee o que Claude decida escribirlos como respuesta.
- No existe evento de hook para `/rewind`/checkpoint — no hay `PreRewind` ni equivalente.
- El SDK (`--continue`, `--resume <id>`) continúa procesos, pero no expone `session.rewind()` ni `session.fork()` a nivel de código.

**Fuentes:** [Commands](https://code.claude.com/docs/en/commands.md) · [Hooks](https://code.claude.com/docs/en/hooks.md) · [Checkpointing](https://code.claude.com/docs/en/checkpointing.md) · [Sub-agents](https://code.claude.com/docs/en/sub-agents.md)
