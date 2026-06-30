# Guía del Dev Pobre: Agentes y Plugins en Claude Code
*Máxima eficiencia. Mínimo gasto. Cero disculpas.*

**Autor:** Félix Sotelo — Dev pobre con aspiraciones de rico
**Versión:** v5.11 · Validada en producción · 2026-06-30

---

> 🌐 **Language / Idioma:** [🇺🇸 English](README.md) · **🇪🇸 Español**

---

> Cada byte en contexto tiene costo. Esta guía existe para que construyas sistemas poderosos sin que tu tarjeta llore al final del mes.
>
> Si puedes hacer algo con **haiku**, no uses sonnet. Si puedes usar una regla en CLAUDE.md, no crees un agente. Si puedes poner un gotcha inline, no hagas que el agente lea un archivo.
>
> El agente es tan bueno como el contexto que recibe. Contexto vago → el agente improvisa → loops de corrección → tokens ×3-5. Define output, scope y criterio de éxito **antes** de invocar. `/plan` primero. (→ §24)

---

## Por dónde empezar

**¿Primera vez con el sistema?** Lee en este orden:

1. **§4** — La analogía del restaurante → entiende el sistema en 5 minutos
2. **§1** — ¿Qué construir y cuándo? → el árbol de decisiones que te ahorra construir lo que no necesitas
3. **§2** — Presupuesto de tokens → el único concepto que cambia cómo diseñas todo
4. **§12** — Errores críticos (solo la primera tabla) → evita los más caros

**¿Ya conoces el sistema y querés construir algo específico?**

| Quiero... | Ir a |
|---|---|
| Crear un agente | §5 — formato, modelo, tools, trigger list |
| Crear una skill | §6 — tipos, lifecycle, `context:fork`, frontmatter completo |
| Crear un hook | §7 — 10 eventos, 5 modos de permiso, secret guard, routing por complejidad |
| Armar un plugin distribuible | §11 — estructura, plugin.json, instalación |
| Configurar learnings + curador | §9 — flujo postmortem → learnings → curador |
| Diseñar arquitectura multi-agente | §10 — lead, especialistas, flujo de trabajo |
| Elegir el modelo correcto | §25 — haiku/sonnet/opus + `effort` como alternativa |
| Ver un plan antes de ejecutar | §17 + §28 — skill `/plan` y cuándo usarla |
| Usar shortcuts de prompts | §28 — Prompt Library con 8 shortcuts y 4 recipes |
| Armar mi propio contexto global | §29 — construir `~/.claude/` desde cero |
| Auto-inyectar contexto de la guía | §26 — hook `guia_context.py` |
| Programar cloud agents | §30 — Cloud Agents (CCR) |
| Saber si lo que construí es overkill | §14 — árbol anti-overkill |
| Saber cuándo parar de optimizar | §23 — techos reales de tokens y palancas por impacto |
| Evitar los errores más caros | §12 — primera tabla |
| Validar lo que construí | §13 — checklist de calidad |
| Usar CLAUDE.local.md / output-styles / rules / settings.local.json | §32 — Archivos que nadie documenta |

---

## Novedades en v5.11

> *Sin contenido nuevo. La guía quedó más rápida de navegar y más limpia de leer: el orden físico de secciones ahora coincide con el Índice, los ejemplos aplican a cualquier stack, y el hook de contexto cubre 4 secciones más.*

| Área | Cambio |
|---|---|
| **Estructura** | Orden físico reordenado — §4→§1→§25→§2→§24 (Fundamentos), luego Core, Calidad, Avanzado. §25 de posición 25 → 3; §24 de posición 24 → 5 |
| **§3** | Tabla de benchmarks Godot (18 filas) → tabla de arquetipos genéricos (8 filas: bash-heavy, read-heavy reviewer/debugger, write-heavy, postmortem, orchestrador, curador) |
| **§5** | Tabla de modelo redundante eliminada — pointer a §25, que ahora está 2 secciones antes |
| **§2 §5 §17** | Template CLAUDE.md, ejemplos de gotchas y `/plan` generalizados — aplican a cualquier stack |
| **`guia_context.py`** | §12, §13, §22, §23 añadidos a KEYWORD_MAP — el hook cubre ahora 27/32 secciones |

<details>
<summary>Novedades en v5.10</summary>

> *§27 corrigió su arquitectura. El hook de contexto ganó deduplicación por sesión y presupuesto más ajustado.*

| Área | Cambio |
|---|---|
| **§27** | Handoff Protocol — diagrama de arquitectura corregido, flujo del Stop hook clarificado |
| **§26** | `guia_context.py` — deduplicación por sesión vía `/tmp/guia_seen_{sid}.json`; `LINES_BUDGET` 120 → 80 |

</details>

<details>
<summary>Novedades en v5.9</summary>

> *§32 mapea los cuatro archivos que nadie documenta: CLAUDE.local.md (override personal gitignored), output-styles/ (formato de respuesta on tap, 30-50% menos tokens de output), rules/ (reglas glob-scoped con ejemplos prácticos), y settings.local.json (permissions personales). Incluye tabla de distribución en plugins.*

| Área | Cambio |
|---|---|
| **§32 NUEVO** | `CLAUDE.local.md` — override personal gitignored, gana sobre `CLAUDE.md` en conflicto |
| **§32 NUEVO** | `output-styles/` — templates `terse.md` / `verbose.md`, 30-50% menos tokens de output en agentes de código |
| **§32 NUEVO** | `rules/` — glob-scoped con ejemplos `api.md` y `tests.md`, tabla de decisión vs `CLAUDE.md` |
| **§32 NUEVO** | `settings.local.json` — permissions personales gitignored por diseño |
| **§32 NUEVO** | Tabla de distribución en plugins — qué se distribuye (`rules/`, `output-styles/`, `settings.json`) vs qué se queda local |

</details>

<details>
<summary>Novedades en v5.8</summary>

> *§6 explica los dos ejes de visibilidad (`disable-model-invocation` × `user-invocable`) como flags ortogonales, agrega la matriz 2×2 y el patrón "librería interna" con template.*

| Área | Cambio |
|---|---|
| **§6** | Modelo de dos ejes de visibilidad — `disable-model-invocation` vs `user-invocable` como flags independientes, matriz 2×2, template "Librería interna" |

</details>

<details>
<summary>Novedades en v5.5</summary>

> *§3 tiene ahora mostrador de triage (split quick/ref). §20 aprendió a contratar a Claude como operario en CI, no solo a testear la oficina. El resto completó los instrumentos que faltaban.*

| Área | Cambio |
|---|---|
| **§3** | Split quick/ref — tablas de estimación al frente, benchmarks godot y detalles de caching en ref |
| **§20** | Claude-en-CI: patrones `--print` + `--dangerously-skip-permissions`, trigger `@claude` por comentario, tabla de costo por trigger con guía de modelo |

<details>
<summary>Novedades en v5.4</summary>

> *Cinco instrumentos nuevos en la orquesta: un medidor de costo (caching), un director más inteligente (routing de modelo), un sous-chef revisor (Advisor), salas de ensayo aisladas (worktrees), y una red de seguridad antes de que el escenario colapse (auto-compaction).*

| Área | Cambio |
|---|---|
| **§3** | Prompt Caching — 90% de descuento en system prompts repetidos, comportamiento del TTL, reglas de diseño para maximizar hits |
| **§25** | Escala de effort completa (`xlow`→`ultra`), Fable 5 como alias default, Fast Mode, framework costo/beneficio de Extended Context 1M |
| **§31 NUEVO** | Advisor Pattern — haiku revisando output de sonnet a ~1.15× costo vs ~5× de subir a Opus |
| **§10** | Worktrees — agentes paralelos con aislamiento git, `isolation: "worktree"` en Agent tool |
| **§27** | Comportamiento de auto-compaction — qué sobrevive, qué no, cómo preparar el contexto antes de que ocurra |

</details>

<details>
<summary>Novedades en v5.3</summary>

> *§7 pasó de ser el cartel de "prohibido entrar" a un sistema completo: enfermera de triage en la puerta, escáner en cada escritura, lista VIP en la ventanilla de permisos.*

| Área | Cambio |
|---|---|
| **§7** | 5 modos de permiso — desde auditoría read-only (`plan`) hasta bypass total (`bypassPermissions`), con cuándo usar cada uno |
| **§7** | Routing por complejidad — como la enfermera de triage: lee el prompt, asigna haiku/sonnet/opus antes de que Claude empiece a planificar. 0 tokens si no hay match |
| **§7** | Secret detection guard — escáner de aeropuerto para escrituras: bloquea API keys y credenciales antes de que toquen el disco, ignora `.env.example` y docs |
| **§7** | Hook PermissionRequest — patrón lista VIP: Read/Glob/Grep entran directo; el resto pasa por el filtro |

</details>

<details>
<summary>Novedades en v5.2</summary>

| Área | Cambio |
|---|---|
| **§7** | 5 modos de permiso — desde auditoría read-only (`plan`) hasta bypass total (`bypassPermissions`), con cuándo usar cada uno |
| **§7** | Routing por complejidad — como la enfermera de triage: lee el prompt, asigna haiku/sonnet/opus antes de que Claude empiece a planificar. 0 tokens si no hay match |
| **§7** | Secret detection guard — escáner de aeropuerto para escrituras: bloquea API keys y credenciales antes de que toquen el disco, ignora `.env.example` y docs |
| **§7** | Hook PermissionRequest — patrón lista VIP: Read/Glob/Grep entran directo; el resto pasa por el filtro |

<details>
<summary>Novedades en v5.2</summary>

| Área | Cambio |
|---|---|
| **§30 NUEVO** | Cloud Agents (CCR) — `/schedule`, `/web-setup`, prompts self-contained, referencia de cron |
| **§26** | Detección en dos tiers para hooks `UserPromptSubmit` de plugin (símbolos + proximidad) |
| **§14** | Nuevo anti-patrón: agente con secciones `## Catalog` que almacenan API shapes completas |
| **§10** | Checkpoint de delegación del lead — el estado vive en la conversación, no en el filesystem |

</details>

<details>
<summary>Novedades en v5.0</summary>

| Área | Cambio |
|---|---|
| **§6 Skills** | Frontmatter completo (17 campos), lifecycle, `context:fork`, supporting files, `ultrathink` |
| **§7 Hooks** | 10 eventos (antes 4), `updatedInput`, npm security guard (supply chain + slopsquatting) |
| **§25 Modelo** | `effort` como alternativa a Opus (~5×), framework de decisión, ejemplo `security-auditor` |
| **§28 NUEVO** | Prompt Library — 8 shortcuts con tags, 4 recipes, 4 Leyes |
| **§29 NUEVO** | Contexto global propio — construir `~/.claude/` desde cero |
| **Docs** | 5 errores factuales corregidos vs documentación oficial de Claude Code |

</details>

---

## Docs oficiales

[Agents](https://code.claude.com/docs/en/sub-agents) · [Skills](https://code.claude.com/docs/en/skills) · [Hooks](https://code.claude.com/docs/en/hooks-guide) · [Plugins](https://code.claude.com/docs/en/plugins) · [Agent Teams](https://code.claude.com/docs/en/agent-teams)

---

## Contribuir

Si querés sugerir algo, abrí un [Issue](../../issues). Si encaja en el flujo de trabajo, lo incorporo. Gracias por leer.
