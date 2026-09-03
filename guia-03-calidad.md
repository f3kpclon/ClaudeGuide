# Guía del Dev Pobre — 03 · Calidad y eficiencia
*Parte de [guia-00-indice.md](guia-00-indice.md) — volver al índice.*

---

<!-- §14 -->
## 14. Guía anti-overkill

> El dev pobre tiene un superpoder que el dev rico no tiene: no puede darse el lujo de construir cosas innecesarias. Cada componente que agregas tiene un costo fijo por sesión — aunque nunca se use. Esta sección es el antídoto al instinto de sobre-ingenierizar.

El sistema de agentes es potente. Eso lo hace tentador de sobre-usar. Cada componente que agregás tiene un costo fijo por sesión — aunque nunca se use.

### La pregunta que frena el overkill

Antes de construir cualquier cosa, una pregunta:

> **¿Qué pasa si NO lo hago?**

Si la respuesta es "nada, funciona igual" → no lo construyas.

### Árbol de decisiones

```
¿Necesito esto?
│
├── ¿Ya ocurrió el problema que esto resuelve?
│   NO → esperar. No diseñar para hipotéticos.
│   SÍ → continuar.
│
├── ¿Se va a repetir más de 3 veces?
│   NO → resolver inline. No abstraer.
│   SÍ → continuar.
│
├── ¿Existe algo que ya lo resuelve?
│   SÍ → usarlo.
│   NO → construir.
│
└── ¿La abstracción es más compleja que lo que abstrae?
    SÍ → overkill. Hacerlo más simple o no hacerlo.
    NO → adelante.
```

### Always-YES — exentos del filtro anti-overkill

Estos componentes se crean **siempre**, sin pasar por el árbol de decisiones:

| Componente | Por qué es always-YES |
|---|---|
| `postmortem` | Necesario desde la primera sesión. Anti-overkill no aplica: no esperás a que ocurra para tenerlo. |
| `learnings-general.md` | Siempre generar. Split por dominio solo cuando supera 150 líneas. |
| `pre_write_guard` | Cualquier proyecto con file writes. Consecuencia real si se omite. |
| `plan` skill (local) | Todo proyecto local. Stack-agnostic, zero overhead, evita ejecutar agentes sin revisar. |
| `plan` skill (plugin + sequential) | Plugin con workflow secuencial → plan domain-specific (conoce las capas). |

### Cuándo NO construir cada componente

| Componente | Overkill cuando... | Alternativa |
|---|---|---|
| Agente nuevo | La tarea ocurre < 3 veces o la puede hacer el agente existente | Agregar una sección al agente existente |
| Hook | La regla no tiene consecuencias reales si se ignora | Regla en el prompt del agente |
| Pre-layer (preflight) | Solo dev con inputs claros | Dispatch directo desde CLAUDE.md |
| Plugin | El código se usa en un solo proyecto | Agente/skill local |
| Curador | Proyecto corto (< 1 mes esperado) Y < 3 agentes en spec | Learnings file sin agente — curar manualmente si hace falta |
| Learnings file nuevo | Hay < 5 entries que justifiquen el archivo | Agregarlas a `learnings-general.md` |
| Scope file nuevo | El sistema tiene < 3 decisiones de diseño | Agregarlas al scope-index.md |
| Hub skill | CLAUDE.md ya tiene el dispatch completo y ≤5 agentes | `skillOverrides: user-invocable-only` |
| Verificación de compilación en plugin | Runner externo (xcodebuild, jest) es env-specific: scheme names, workspace paths, versiones — rompe en cualquier clone distinto | Documentar como limitación conocida; compilar en el IDE antes del PR |
| Opus | La tarea es implementación, checklist o git | haiku o sonnet |
| Lead | Una sola tarea NO se descompone en pipeline cross-especialistas | Especialista directo |
| Agente especialista | La tarea es copiar un patrón existente con ≤3 cambios y ≤2 archivos | Hacerlo directo en contexto principal — overhead del agente (~3-4k tokens arranque en frío) supera el riesgo de violar convenciones |
| Debugger | CLI lineal, script simple, plugin (sin runtime) | Implementer lo resuelve inline |

### Señales de sobre-ingeniería activa

Estas señales indican que el sistema ya tiene demasiado:

```
⚠️  CLAUDE.md supera 30 líneas
    → Hay reglas que deberían estar en los agentes, no en el CLAUDE.md global.

⚠️  Un agente tiene más de 3 secciones con listas largas
    → El agente hace demasiado o tiene contenido que debería estar en learnings.

⚠️  Hay un hook para cada tipo de Bash command
    → Los hooks deberían cubrir acciones irreversibles, no validar todo.

⚠️  Cada tarea arranca leyendo 3+ archivos de learnings
    → Los gotchas frecuentes deberían estar inline. Solo leer bajo demanda.

⚠️  El lead implementa código directamente
    → El lead coordina. Si implementa, es señal de que falta un especialista
      o de que la tarea no era suficientemente grande para necesitar lead.

⚠️  Hay agentes que nadie invocó en el último mes
    → Candidatos a archivar o fusionar con otro agente.

⚠️  El curador corre en cada sesión
    → Debe correr mensualmente. Si corre siempre, algo en el flujo está mal.

⚠️  Un agente tiene secciones ## Catalog con API shapes completas (params, tipos, overloads)
    → Las API shapes divergen del source sin que nadie lo note — el agente trabaja
      con una API que ya no existe. Catalog = lista de nombres de existencia.
      API shapes viven en el source; el agente los lee cuando los necesita.
```

### Regla de los tres usos

> Hasta el tercer uso, no abstraer. Al tercero, considerar. Al cuarto, hacerlo.

- Primera vez: resolver inline, sin abstraer.
- Segunda vez: copiar. Está bien. No es el momento.
- Tercera vez: evaluar si vale la pena abstraer.
- Cuarta vez: abstraer — ya se demostró que se repite.

Esta regla aplica a agentes, skills, hooks y scope files por igual.

### El costo del "por si acaso"

Cada componente "por si acaso" tiene un costo real:

```
Un agente que nunca se invoca:        ~40t en system prompt por sesión
Una skill con auto-trigger innecesaria: ~280t por tarea (LLM call)
Un hook que corre en cada Bash:        ~50ms de latencia por comando
Un learnings de 200 líneas:           ~1,400t cuando se carga (vs 700t en < 100 líneas)
Un CLAUDE.md de 60 líneas:            ~400t re-inyectados en CADA tool call
```

El "por si acaso" se paga siempre. El "cuando lo necesite" se paga solo cuando ocurre.

---


<!-- §12 -->
## 12. Errores comunes

> Esta tabla existe porque alguien (yo) los cometió todos. Algunos cuestan tokens, otros cuestan tiempo, los peores cuestan los dos. Leerla antes de construir vale más que cualquier tutorial.

### 🔴 Críticos — fallan en silencio, costo alto o consecuencias irreversibles

| Error | Síntoma | Fix |
|---|---|---|
| CLAUDE.md largo | Cada tool call consume tokens antes de trabajar | < 30 líneas. Convenciones → skills |
| Hub auto-trigger con dispatch en CLAUDE.md | ~280t extra por tarea sin beneficio | `skillOverrides: {"hub": "user-invocable-only"}` |
| Sin model en agente | Todos usan el mismo modelo caro | Especificar siempre. haiku para tareas fijas |
| Reviewer con sonnet | Costo de implementador para checklist | Si compara contra lista fija → haiku |
| Bash en orchestrador | El lead ejecuta en vez de delegar | Sacar Bash. Solo `Read, Glob, Grep` |
| Write/Edit en orchestrador | El lead implementa directamente aunque el prompt diga que no — la regla es sugerencia | Sacar Write y Edit. Sin tools, la delegación es garantía física — igual que un hook vs una regla en el prompt |
| Postmortem escribe en el hub | Costo fijo que crece con cada sesión — se paga en TODA tarea | Escribir en `learnings/learnings-[dominio].md` — nunca en el hub |
| Tablas markdown en agente haiku | Una tabla de 7 filas ocupa ~9 líneas — empuja sobre el límite de 60 | Formato inline: `` `feat` nuevo · `fix` bug · `refactor` sin cambio API `` |
| Matcher `str_replace` en hooks.json | El hook NUNCA dispara — falla en silencio | Usar `MultiEdit`. Tool names válidos: `Bash`, `Write`, `Edit`, `MultiEdit`, `Read` |
| Campo de payload inventado (`path`, `new_str`, `subagent_type`) | `.get()` retorna `''` → exit 0 → hook muerto que se ve sano, tests verdes si comparten el shape | Campos reales: Edit → `file_path`/`new_string` · MultiEdit → `edits[].new_string` · SubagentStop → `agent_type`. Copiar de la doc oficial, nunca de memoria (§7) |
| PreToolUse con exit 2 | Bloquea pero sin razón visible para el usuario | Retornar JSON `permissionDecision: deny` + exit 0 — el campo acepta `deny\|allow\|ask\|defer` |
| SubagentStop con `echo` crudo | Texto sin formato contamina el contexto como stdout | `{"systemMessage": "..."}` |
| PostToolUse con `print()` crudo | Mismo problema — texto contamina stdout | `{"systemMessage": "..."}` |
| `try/except` solo en PreToolUse | SubagentStop, PostToolUse y Stop crashean si stdin viene vacío | try/except en **todos** los hooks |
| `"texto" in cmd` en hook Bash | Falso positivo si el texto aparece en `--body` | `re.split(r'\s*&&\|\s*\|\|', cmd)[0]` para aislar el primer comando |
| Path absoluto en hook | Hook rompe al mover o clonar el proyecto | `Path(__file__).parent.parent.parent` |
| Agente git hace push directo a master | El agente lo interpreta literalmente — irreversible | Hook PreToolUse que bloquea `git push origin master` |
| Reviewer con scope inflado (≥7 archivos) | 34 tool uses → 22.7k tokens (medido) vs ~4-8k esperado | Solo archivos directamente modificados (≤4); "1 Read por archivo, máx 1 Grep/Glob" |
| Postmortem con prompt de contexto completo | 24.2k tokens (medido) vs ~5-10k esperado | Prompt corto: solo insights no visibles en git diff. El agente descubre el resto. |
| "Leer learnings antes de empezar" incondicional | 1 Read call extra por agente por tarea | Inlinear los 5-10 gotchas críticos en el agente |
| Git en múltiples invocaciones separadas | 22k tokens (medido) vs ~10-12k esperado | Una sola invocación al final: BRANCH+COMMIT+PR+MERGE · VALIDADO: sí |
| `git add -p` en agente git | Interactivo — el agente entra en loop esperando stdin, infla tool calls | Usar `git add -u` (todos los modificados) + `git status --short` previo |
| Commit message no pasado en el prompt al agente git | El agente usa 1-2 tool calls extra para inferir qué cambió | Pasar mensaje explícito: `COMMIT: tipo: descripción` — el agente no explora |
| `subagent_type` con nombre que no está en la lista de agent types de la sesión | Error "agent type not found" — falla inmediata, no silent | Built-ins reales: `general-purpose`, `Explore`, `Plan`, `claude`. En versiones actuales los agentes de `.claude/agents/` y `~/.claude/agents/` TAMBIÉN aparecen como agent types invocables (verificado 2026-07-02) — la restricción a built-ins era de versiones anteriores. Fallback si el agente no aparece: `subagent_type: claude` + `"Read .claude/agents/X.md and follow it. TARGET: …"` en el prompt. |
| `\|\| return` en función bash con `set -e` | Script muere silenciosamente sin output cuando el archivo no está en el diff | `grep -qF "$file" \|\| return 0` — `return` sin código propaga el exit code 1 de grep; `set -e` mata el script antes del primer `echo`. Aplica a cualquier función de validación en CI/hooks. |
| AskUserQuestion option con `"in notes"` | Usuario no sabe dónde escribir — confusión en cada uso real | Referenciar explícitamente: `"Other" field (option 3 below)` en la etiqueta de la opción. Validado en artifact-factory 2026-06-02. |
| Validator invocado con `subagent_type: claude` sin instrucciones Grep-first | 23 tool uses (medido) vs 10 esperado — el agente lee archivos completos | Pasar las instrucciones Grep-first explícitas + `TYPE: local\|plugin` en el prompt. Nunca leer lo que Grep puede responder. |
| Invocar agente sin arquitectura/scope definidos | El agente asume, genera loops de corrección, tokens ×3-5 respecto a tarea bien acotada | `/plan` primero; si no hay scope → escribirlo antes de invocar. Ver §24. |

### 🟡 Frecuentes — mal diseño y malas prácticas

| Error | Síntoma | Fix |
|---|---|---|
| `hooks.json` faltante | Scripts Python nunca se ejecutan | Crear `hooks/hooks.json` o declarar en `settings.json` |
| `disable-model-invocation: true` en hub | Triage nunca se activa | Cambiar a `false` en el hub |
| Doc monolítico | Agente lee 500 líneas innecesarias | Dividir por dominio, máx 100 líneas c/u |
| Contenido duplicado | Se paga dos veces en tokens | Un solo lugar. El hub referencia, no copia |
| `disable-model-invocation: false` en skill `user-invocable-only` | El usuario llama `/hub` y gasta un LLM call en contenido estático | Si la skill es referencia pura → `disable-model-invocation: true` |
| Sin protocolo de fallo bash | Loop de workarounds infinito | Máximo 2 ciclos. Reportar y parar |
| Learnings monolítico | 500+ líneas se cargan siempre | Fragmentar en dominios < 150 líneas |
| Rama sin commitear pendientes | Cambios se mezclan entre features | Commitear siempre antes de `git checkout -b` |
| Scope monolítico | Agentes cargan contexto irrelevante | Fragmentar. Cada agente lee solo su dominio |
| Hook auto-checkout no dispara tras push directo | `after_pr_merge` espera `gh pr merge` — push directo lo bypasea | Hook guard (bloquea push) + flujo via PR obligatorio |
| Agente de diagnóstico sin output format | 3-4x más tokens en la respuesta | Agregar `## Output — siempre este formato` con template compacto |
| Scope sin API de sistemas existentes | Lead lee 5-10 archivos de contexto (~5-8k tokens extra por feature) | Agregar `## API existente relevante` al scope |
| Prompt de invocación largo | 6-12x más tokens — el agente repite lo que ya sabe | Solo datos variables: rama, título, archivos |
| Hub de plugin > 40 líneas | Hub auto-load consume tokens en cada tarea | Proyecto con CLAUDE.md: 40 líneas. Plugin sin CLAUDE.md: ~60 líneas |
| Hub description incoherente con skillOverrides | El modelo puede intentar activarla incorrectamente | Sincronizar description con el comportamiento real |
| SubagentStop no-op silencioso tras agente pesado | El usuario no sabe si el agente terminó o falló | Mostrar `systemMessage` de confirmación |

---


<!-- §13 -->
## 13. Checklist de calidad

> Automatizable — con una salvedad: las skills globales `/audit-guia` (proyecto con CLAUDE.md) y `/audit-plugin` (plugin distribuible) **no corren este checklist**: validan contra las secciones fuente (§5, §6, §7, §11, §25, §32, §35) precisamente porque este §13 es una copia derivada que puede quedar atrás. Si las dos divergen, gana la sección fuente — ver §29.

```
CLAUDE.md
□ < 30 líneas
□ Solo triage y reglas críticas
□ Referencia a scope-index.md
□ Referencia a learnings por dominio
□ Sin tablas ni ejemplos de código

Guía (al actualizar guia-agentes-plugins-claude-code.md)
□ §N en el Índice si se agregó
□ Sección > 150 líneas → agregar <!-- §N-quick --> (reglas) y <!-- §N-ref --> (código/ejemplos)
□ Inyección del hook fence-safe: `-quick` completo (curado, balanceado, ≤5500 chars) o cápsula del head sin quick — `audit_guia.py` verifica que ninguna sección quede vacía o con fence impar (§26)
□ Ningún marker <!-- §N... --> dentro de un code fence — la inyección corta el fence sin cerrar
□ NUNCA renumerar §N — son IDs estables (KEYWORD_MAP, anchors, CLAUDE.md global dependen de ellos); el orden físico es append-only, el Índice define el orden temático
□ Cada concepto tiene UNA casa — otras secciones enlazan con → §N, nunca copian (las copias divergen)
□ Nueva sección tiene anchor <!-- §N --> y entrada en Índice
□ Nueva sección → entry en KEYWORD_MAP del hook INSTALADO (~/.claude/hooks/guia_context.py) Y en la copia embebida de §26 — mismo commit
□ tools/audit_guia.py pasa limpio antes de commitear

Agentes
□ description como trigger list
□ model especificado (haiku/sonnet/opus)
□ tools al mínimo necesario
□ orchestrador sin Bash, Write ni Edit
□ reviewer con haiku
□ agentes con Bash tienen protocolo de fallo (máx 2 ciclos)
□ una sola responsabilidad por agente
□ gotchas críticos inline (sección ## Gotchas críticos)
□ agentes de diagnóstico/revisión tienen sección ## Output con formato compacto forzado
□ sin "Leer antes de empezar" incondicional para learnings frecuentes
□ sin contenido duplicado con skills o docs
□ Contexto definido antes de invocar: output esperado + scope + criterio de éxito (ver §24)

Skills
□ Hub: disable-model-invocation: false, user-invocable: false, < 40 líneas (proyecto con CLAUDE.md) / < 60 líneas (plugin sin CLAUDE.md — §2/§6)
□ Hub con dispatch duplicado en CLAUDE.md → skillOverrides: user-invocable-only
□ Plugin con gate de implementación: skills de creación (`plan`/`new-X`) con disable-model-invocation: true + el hub instruye explícitamente esperar al usuario (§6)
□ Referencias que solo el usuario pide: disable-model-invocation: true
□ Referencias que un flujo del modelo debe cargar (templates, convenciones): disable-model-invocation: false — con user-invocable: false + disable-model-invocation: true la skill es INALCANZABLE
□ Frontmatter con ":" dentro de description → quotear (YAML roto = metadata vacía en silencio)
□ description < 1,536 chars (combined description + when_to_use; configurable con skillListingMaxDescChars)
□ Sin contenido duplicado
□ Skill con trabajo pesado (> 3 archivos / logs largos) → context: fork con agent: Explore
□ SKILL.md > 200 líneas → dividir en SKILL.md + reference.md (el directorio como soporte)
□ Skill invocada en sesión larga → re-invocar con /nombre si "se olvidó" post-compact
□ model / effort solo cuando el override está justificado (no usar sonnet donde haiku alcanza)
□ user-invocable: false para background knowledge que no es acción del usuario
□ Reglas de output de code-writer agents INLINE en el agente (3-6 líneas) — subagentes no pueden leer output-styles/ del plugin; un output-style de plugin aplica a TODA la conversación principal
□ Reglas universales del dominio: proyecto local → `.claude/rules/` con glob · plugin → skill hub o inline en agentes (`rules/` NO es componente de plugin)
□ Agentes con tools: restringido NUNCA instruidos a "cargar skill X" — sin la tool Skill en su lista es imposible; el hilo principal carga la template y el agente lleva el patrón inline

Scope
□ scope-index.md < 20 líneas
□ Un archivo por sistema, < 50 líneas
□ Sección `## API existente relevante` con métodos y señales de sistemas integrados
□ Solo decisiones tomadas y pasos concretos
□ Postmortem lo actualiza al terminar sesión
□ Decisiones no obvias tienen entrada ADR con alternativas descartadas y razón

Learnings
□ Un archivo por dominio, < 150 líneas
□ CLAUDE.md apunta al correcto
□ Entries concretas: problema + causa + solución
□ Bootstrap con lecciones iniciales
□ Top 5-10 gotchas críticos inline en el agente correspondiente
□ Agente curador definido para mantenimiento mensual (no en cada sesión)
□ Postmortem escribe en learnings/ — NUNCA en el hub (hub = costo fijo)
□ stop.py avisa cuando learnings supera 150 líneas con systemMessage JSON
□ Curador tiene mapeo categoría → agente para saber dónde promover inline

Agentes haiku (< 60 líneas)
□ Tablas de Types/Scopes → formato inline (1 línea en vez de 9)
□ Sección de categorías del postmortem → eliminar si ya están en learnings files
□ "Cuándo no invocar" → condensar a 1 línea si aplica

Hooks
□ settings.json declara todos los hooks
□ Scripts con chmod +x
□ PreToolUse usa JSON permissionDecision (deny|allow|ask|defer) + exit 0 — nunca exit 2
□ SubagentStop y PostToolUse usan systemMessage (no echo)
□ try/except en TODOS los hooks (no solo PreToolUse), sys.exit(0) como fallback
□ Checks de string Bash usan re.split para aislar primer comando (no "texto" in cmd)
□ Acciones irreversibles tienen hook guard — no solo regla en el prompt del agente
□ Agente git tiene pre_push_guard bloqueando push directo a master
□ Sin paths absolutos — usar Path(__file__).parent.parent.parent
□ command en settings.json con "$CLAUDE_PROJECT_DIR" — ruta relativa rompe tras cd
□ Campos de payload reales: Edit → file_path/new_string · MultiEdit → edits[].new_string
□ Tests de hooks con payloads del shape real del tool — no del shape que asume el hook
□ if de guards amplio (Bash(git *)) — un if angosto no matchea comandos encadenados
□ Matcher en hooks.json usa nombres exactos: Write, Edit, MultiEdit, Bash, Read — nunca str_replace
□ PostToolUse usa systemMessage JSON — igual que SubagentStop, nunca print() crudo
□ Hub description coherente con skillOverrides (no decir "Auto-load" si es user-invocable-only)
□ SubagentStop de agentes pesados muestra systemMessage de confirmación
□ SubagentStop lee agent_type del payload (con subagent_type como fallback) — agent_name/subagent_name no existen
□ Proyectos Node.js tienen npm_guard.py bloqueando npx y npm install <pkg> sin --ignore-scripts
□ updatedInput siempre junto a permissionDecision: "allow" — nunca como valor de permissionDecision
□ Plugin: hooks.json con wrapper {"hooks": {...}} y scripts con "${CLAUDE_PLUGIN_ROOT}"
□ Plugin: claude plugin validate pasa limpio en pre-commit/CI antes de cada release
□ Cada hook nuevo tiene test subprocess (§19) — un hook sin test es un hook que puede estar muerto sin que lo sepas
□ updatedInput en vez de deny cuando la corrección es mecánica (ej: npm install → npm ci)
□ SessionStart con matcher "startup|resume" para inyectar contexto de branch/estado al iniciar

Plugin (si aplica)
□ plugin.json con campos del spec
□ README.md con instalación y uso
□ hooks/hooks.json existe
```

**Gotcha — validator Grep-first:** pasar `TYPE: local|plugin` + instrucciones Grep explícitas en el prompt. Sin esto: 23 tool uses. Con esto: 10 (medido). Agentes locales del proyecto no pueden invocarse con `subagent_type` — usar `subagent_type: claude` + instrucciones inline.

---


<!-- §23 -->
## 23. Techos reales de tokens — cuándo parar de optimizar

> Reducir tool calls y reducir tokens son dos problemas distintos. Confundirlos lleva a optimizar lo incorrecto. Esta sección define el piso de tokens de cada tipo de agente para saber cuándo llegaste al límite.

### El principio

Los tokens de un agente se componen de:

```
tokens totales = (system_prompt × N_tool_calls) + Σ(tool_outputs)
```

- **system_prompt × N_tool_calls**: el system prompt se re-inyecta en cada tool call. Reducir tool calls baja este costo linealmente.
- **Σ(tool_outputs)**: la suma de los outputs de todos los tool calls (bash outputs, contenido de archivos leídos, resultados de grep). Este costo **no se reduce eliminando discovery calls** — está determinado por los outputs de las operaciones necesarias.

**La consecuencia práctica:** reducir discovery calls (git log, git status innecesario) ahorra tool calls pero no ahorra proporcionalmente tokens, porque los outputs de los comandos necesarios (git commit, gh pr create, gh pr merge) dominan el costo.

### El techo por tipo de agente

| Tipo de agente | Qué domina el costo | Techo real | Cuándo llegaste al límite |
|---|---|---|---|
| **Bash-heavy** (git, postmortem) | Output de comandos bash | ~5-7k | Cuando tool calls = mínimo necesario para la operación |
| **Read-heavy** (reviewer, debugger) | Contenido de archivos leídos | ~4-8k por archivo | Cuando lee solo los archivos directamente involucrados |
| **Write-heavy** (implementador) | Archivos leídos + escritos + razonamiento | ~8-14k | Cuando no hace reads de contexto innecesarios |
| **Orchestrador** (lead) | Scope + delegación | ~10-18k | Cuando no implementa directamente |

### Ejemplo medido — agente git (bash-heavy, haiku)

```
Antes (13 tool calls):  8.3k tokens
Después (4 tool calls): 7.3k tokens
Diferencia:             1.0k tokens (~12%)

¿Por qué tan poca diferencia?
  Los 9 calls eliminados eran calls de discovery cortos (~100-200t cada uno).
  Los 4 calls que quedaron tienen outputs pesados:
    git commit output:     ~300t
    git push output:       ~200t
    gh pr create output:   ~400t
    gh pr merge output:    ~300t
    system prompt (×4):  ~1,400t
    overhead de contexto: ~1,500t
  ─────────────────────────
  Techo real estimado:   ~4,100-5,000t
  Medido con 4 calls:     7,300t ← ~2k sobre el techo teórico (razonamiento del agente)
```

El 1k ahorrado vino de eliminar los calls, pero el verdadero valor fue la **latencia** (30s se mantiene, pero sin loops) y la **confiabilidad** (sin calls interactivos que bloquean).

### Cuándo seguir optimizando vs cuándo parar

```
¿Los tool calls superan el mínimo necesario para la operación?
    SÍ → seguir optimizando (hay discovery innecesario)
    NO → el costo restante son outputs inevitables

¿Los tokens están más del doble del techo real?
    SÍ → hay algo mal: output format sin forzar, archivos de contexto extra, prompt largo
    NO → estás en el rango normal del agente

¿Reducir tool calls ahorraría > 30% de tokens?
    NO → el costo lo dominan los outputs, no los calls
    SÍ → hay calls muy pesados que pueden evitarse
```

### Palancas por orden de impacto

1. **Output format forzado** — la más barata: no cambia tool calls, reduce el razonamiento verbose en 30-65%
2. **Eliminar discovery calls** — baja tool calls y latencia; el ahorro de tokens es modesto (~10-20%)
3. **Encadenar comandos bash con `&&`** — reduce N_tool_calls directamente, baja el costo del system prompt re-inyectado
4. **Acortar el system prompt del agente** — cada línea menos = ahorro en cada tool call del agente
5. **Reducir archivos pasados al reviewer** — cada archivo extra = ~700-1,400t en outputs de Read

### Anti-overkill

Cuando un agente está en su techo real, no hay más que optimizar desde el agente — el costo restante es el precio mínimo de la operación. Intentar bajarlo más requiere:
- Cambiar el modelo (haiku → más barato, pero no existe nivel inferior)
- Reducir el scope de la operación (hacer menos cosas, no hacerlas más eficientemente)
- Aceptar que ese es el costo y enfocarse en otra cosa

**Señal de que llegaste al techo:** optimizas el agente y los tokens bajan menos del 15%. El resto lo fija la operación misma, no el agente.

### Checklist §23

```
□ Para cada agente con costo inesperado: identificar qué domina (bash outputs vs Read outputs vs razonamiento)
□ Comparar tool calls actuales con el mínimo necesario para la operación
□ Si tool calls = mínimo y tokens siguen altos → el costo es el techo real, no un problema de diseño
□ Output format forzado antes de cualquier otra optimización
□ Encadenar comandos bash con && para reducir N_tool_calls × system_prompt_cost
□ No seguir optimizando cuando tokens < 2× el techo real estimado
```



<!-- §3 -->
<!-- §3-quick -->
## 3. Estimados de consumo

> Antes de arrancar cualquier tarea, el dev pobre hace una estimación. Estos números son aproximados pero suficientes para saber si vas a gastar $0.02 o $0.50 antes de escribir una línea.

### Costo fijo por sesión

| Componente | Tokens | Notas |
|---|---|---|
| CLAUDE.md (~30 líneas) | ~200 | Se re-inyecta en cada tool call |
| Hub skill (~40 líneas) | ~280 | Solo si auto-trigger está activo |
| Agent descriptions (×10) | ~400 | ~40t por agente registrado |
| scope-index.md (~20 líneas) | ~120 | Si está en CLAUDE.md |
| **Total fijo mínimo** | **~1,000** | Por sesión, antes de cualquier tarea |

Si el hub tiene `skillOverrides: user-invocable-only`, los ~280 tokens no se gastan.

### Costo por tipo de tarea

| Tarea | Agentes | Tokens extra (contexto principal) | Tokens subagente (aislado) |
|---|---|---|---|
| Bug simple (1 bug, ≤3 archivos) | debugger + reviewer | ~600 | ~6-10k |
| Bug complejo (2+ bugs, 5+ archivos) | debugger + reviewer | ~800 | ~14-18k |
| Feature simple (1 sistema) | especialista + reviewer | ~800 | ~4-8k |
| Feature mediana (2 sistemas) | lead + 2 especialistas + reviewer | ~1,400 | ~10-16k |
| Feature compleja (3+ sistemas) | lead + 3 especialistas + reviewer | ~2,200 | ~18-28k |
| Refactor cross-cutting | lead + todos los especialistas | ~3,000 | ~30-40k |
| Fin de sesión | postmortem + git | ~500 | ~2-4k |

"Tokens subagente (aislado)" = consumo interno del agente — no se acumula en el hilo principal (Capa 3).

### Impacto del modelo

Precios oficiales por 1M tokens (input/output, verificados 2026-09-02):

| Modelo | Precio | Costo relativo | Cuándo |
|---|---|---|---|
| haiku 4.5 | $1 / $5 | 1× | Tareas fijas: git, postmortem, reviewer de checklist |
| sonnet 5 | $2 / $10 | 2× | Implementación, debugging |
| opus 5 | $5 / $25 | 5× | Arquitectura con trade-offs complejos, security |
| fable 5.1 | $10 / $50 | 10× | Solo si tus evals con Opus 5 a effort alto se quedan cortos |

Un reviewer en sonnet cuesta 2× más que en haiku — mismo resultado. Opus ya NO es 15× haiku ni 5× sonnet (pricing retirado): es **2.5× sonnet**, y ese ratio es estable — la suba de Sonnet 5 a $3/$15 agendada para el 01/09/2026 **fue cancelada** y $2/$10 pasó a ser el precio estándar (nota oficial en la página de pricing). El threshold para justificar Opus bajó y se quedó ahí (→ §25).

### El tokenizer cambió — tus estimados históricos están bajos

**Verificado 2026-09-02** (nota oficial en la página de pricing): de Claude 4.7 en adelante — Opus 4.7, Opus 4.8, **Opus 5**, **Sonnet 5**, Fable 5/5.1 — el tokenizer es nuevo y produce **~30% más tokens para el mismo texto**. **Sonnet 4.6 y anteriores, y Haiku 4.5, usan el tokenizer viejo.**

| Modelo | Tokenizer | Efecto sobre los estimados de esta sección |
|---|---|---|
| Haiku 4.5 | viejo | Los números de arriba valen tal cual |
| Sonnet 5 · Opus 5 · Fable 5.1 | nuevo (~+30%) | **Multiplicar los estimados por ~1.3** |

Dos consecuencias, ninguna obvia:

1. **La tabla de costo fijo de arriba subestima ~30% en todo lo que no sea haiku.** Un CLAUDE.md de ~200 tokens con el tokenizer viejo son ~260 en Sonnet 5 u Opus 5: el techo real de §2 está 30% más abajo de lo que creías.
2. **La ventaja de haiku es mayor que 2×.** "Sonnet cuesta 2× haiku" compara precio por token, pero haiku además necesita *menos tokens* para el mismo prompt: el ratio real ronda **~2.6×**. La regla "si haiku lo hace bien, no uses sonnet" se refuerza.

**Opus 5 : Sonnet 5 sigue siendo 2.5×** — comparten tokenizer, ahí la comparación es directa.

Para medir: `count_tokens` **con el modelo destino**. Extrapolar entre modelos es el error que este cambio vuelve caro (→ §21).

### Prompt Caching — reglas clave

| Tipo | Costo relativo | Cuándo ocurre |
|---|---|---|
| Cache write (TTL 5 min) | 1.25× | Primera llamada o después de expirar el TTL |
| Cache write (TTL 1 hora) | 2× | Opt-in — para sesiones con huecos de más de 5 min |
| Cache read | 0.1× | Mismo prefix dentro del TTL |
| Sin cache (base) | 1× | Referencia |

**Cuándo conviene cada TTL** (verificado 2026-09-02): el write de 5 min se paga solo **con 1 lectura**; el de 1 hora necesita **2 lecturas** para amortizarse. Si tu sesión tiene pausas de más de 5 minutos (pensar, revisar un PR, almorzar), el de 1 hora sale más barato que re-crear el cache desde cero. En Fable 5.1 el read baja a **0.025×** en vez de 0.1× — el único modelo con esa tarifa.

- **TTL por defecto: 5 minutos** — después de 5 min de inactividad el cache expira
- **Qué se cachea:** CLAUDE.md, system prompts de agentes, historial hasta el corte del prefix
- **Regla de prefix:** contenido estable → CLAUDE.md. Contenido dinámico (paths, IDs, runtime) → `additionalContext` de hook. El dinámico invalida el cache si entra en el prefix.

### Señales de consumo excesivo

- Tarea simple tarda más de lo esperado → CLAUDE.md creció demasiado
- El agente sabe cosas que no le dijiste → contenido duplicado entre archivos
- Reviewer tarda igual que el implementador → está corriendo en sonnet
- El lead ejecuta bash → tiene Bash en tools, no debería
- El lead escribe código directamente → tiene Write/Edit en tools — quitarlos, la delegación debe ser garantía física
- Cada agente hace 2-3 Read calls antes de empezar → gotchas deberían estar inline

<!-- §3-ref -->
### Costo por archivo bajo demanda

| Archivo | Tokens |
|---|---|
| Learnings por dominio (~100 líneas) | ~700 |
| Scope por sistema (~50 líneas) | ~350 |
| Doc de referencia (~100 líneas) | ~700 |
| Skill de convenciones (~80 líneas) | ~560 |
| Read tool call (overhead del wrapper) | ~300-600 |

### Estimados por arquetipo de agente (tokens internos — contexto aislado)

Los agentes corren en contexto aislado (Capa 3). Estos tokens **no se acumulan** en el hilo principal.
`†estimado` / `✓medido`

| Arquetipo | Modelo | Optimizado | Anti-pattern | Principal driver |
|---|---|---|---|---|
| **Bash-heavy** (git, deploy) — 1 invocación | haiku | ~5-7k✓ | ~20-25k (múltiples invocaciones) | Invocaciones separadas pagan cold start — consolidar |
| **Read-heavy** / reviewer (≤4 archivos, protocolo activo) | haiku | ~4-8k† | ~20-25k (≥7 archivos, sin protocolo) | Cada archivo extra = ~700-1,400t; sin protocolo 1-read-por-archivo |
| **Read-heavy** / debugger simple (1 bug, ≤4 archivos) | sonnet | ~6-10k† | ~21k (sin output format) | Output format no forzado: 2-4× verbosidad |
| **Read-heavy** / debugger complejo (2+ bugs, ≥10 tool uses) | sonnet | ~14-18k✓ | >21k | Hipótesis secundarias sin output format |
| **Write-heavy** / implementador (≤5 archivos) | sonnet | ~8-14k† | >20k | Read calls de contexto innecesarios antes de empezar |
| **Postmortem** (prompt corto, ≤3 dominios) | haiku | ~5-10k† | ~20-25k (prompt largo) | Prompt largo infla input — pasar solo insights, no historial |
| **Orchestrador** / lead | sonnet | ~10-18k† | >25k | Si implementa directamente (sin delegación real) |
| **Curador** | haiku | ~6-12k† | >15k | Lee todos los learnings — mantener < 150 líneas por archivo |

**Qué sube el costo de cualquier agente:**
- Cada `Read` call: ~700-1,400 tokens adicionales en el contexto aislado
- Output format no forzado: 2-4× más tokens en la respuesta final
- Sin gotchas inline: 2-3 Read calls extra antes de empezar

**Regla práctica:** `## Output — siempre este formato` con template compacto reduce el costo del output ~30-65%.

### Ejemplo real — feature mediana

```
Costo fijo sesión:              ~1,000t
@lead (planifica):                ~500t  ← lee scope-index.md
@implementador-A:                 ~600t  ← gotchas inline, sin Read de learnings
@implementador-B:                 ~700t  ← gotchas inline, sin Read de learnings
@reviewer (revisión):             ~400t  ← haiku, solo lectura
@git (commit + PR):               ~200t  ← haiku, comandos fijos
─────────────────────────────────────────
Total estimado:                 ~3,400t

Sin setup óptimo (sin fragmentar, hub auto-trigger, modelos incorrectos): ~8,000-12,000t
El setup correcto reduce 2.5-3.5x el costo por feature.
```

### Prompt Caching — detalles

**CLAUDE.md denso se amortiza — no penalizar el tamaño:**
```
CLAUDE.md 500 líneas × sin cache = ~3,500t por llamada
CLAUDE.md 500 líneas × con cache = ~350t por llamada (llamadas 2+)
```
El costo real por llamada es ~10% del nominal después de la primera.

**Implicación para `/loop` y sleeps:**
- `delaySeconds < 300` → cache sigue caliente → siguiente iteración barata
- `delaySeconds > 300` → cache expiró → recrea en la próxima llamada
- `ScheduleWakeup` recomienda 270s sobre 300s por esta razón exacta

**Leer hits/misses al final de sesión:**
```
Tokens: 12,450 input (8,200 cache read · 1,100 cache creation) · 2,450 output
                        ↑ amortizado              ↑ primer turno o post-TTL
```
`cache read >> cache creation` → sesión bien amortizada. Proporción similar → el prefix cambia entre llamadas — revisar contenido dinámico en CLAUDE.md.

---
