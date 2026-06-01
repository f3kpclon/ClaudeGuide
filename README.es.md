# Guía del Dev Pobre: Agentes y Plugins en Claude Code
*Máxima eficiencia. Mínimo gasto. Cero disculpas.*

**Autor:** Félix Sotelo — Dev pobre con aspiraciones de rico
**Versión:** v4.6 · Validada en producción · Estimados actualizados con datos reales (2026-05-31)

---

> 🌐 **Language / Idioma:** [🇺🇸 English](README.md) · **🇪🇸 Español**

---

> Cada byte en contexto tiene costo. Esta guía existe para que construyas sistemas poderosos sin que tu tarjeta llore al final del mes.
>
> Si puedes hacer algo con **haiku**, no uses sonnet. Si puedes usar una regla en CLAUDE.md, no crees un agente. Si puedes poner un gotcha inline, no hagas que el agente lea un archivo.
>
> Esta es la filosofía. El resto es implementación.

---

## Por dónde empezar

**¿Primera vez con el sistema?** Lee en este orden:

1. **§4 — La analogía del restaurante** → entiende el sistema en 5 minutos antes de tocar código
2. **§1 — ¿Qué construir?** → el árbol de decisiones que te ahorra construir lo que no necesitas
3. **§2 — Presupuesto de tokens** → el único concepto que cambia cómo diseñas todo
4. **§12 — Errores críticos** (primera tabla) → lee solo esa, evita los más caros
5. **§15 — Glosario** → cuando un término no tenga sentido, búscalo ahí

**¿Ya conoces el sistema y quieres construir algo específico?**

| Quiero... | Ir a |
|---|---|
| Crear un agente | §5 — formato, modelo, tools, trigger list |
| Crear un hook | §7 — PreToolUse, PostToolUse, templates Python |
| Armar un plugin distribuible | §11 — estructura, plugin.json, probar local |
| Configurar learnings + curador | §9 — flujo postmortem → learnings → curador |
| Diseñar arquitectura multi-agente | §10 — lead, especialistas, flujo de trabajo |
| Saber si lo que construí es overkill | §14 — árbol anti-overkill |

---

📖 **[Ver la guía completa en español →](guia-agentes-plugins-claude-code.md)**

---

## Índice

1. [¿Qué construir y cuándo?](#1-qué-construir-y-cuándo)
2. [Presupuesto de tokens](#2-presupuesto-de-tokens)
3. [Estimados de consumo](#3-estimados-de-consumo)
4. [Analogía — cómo pensar el sistema](#4-analogía--cómo-pensar-el-sistema)
5. [Agentes](#5-agentes)
6. [Skills](#6-skills)
7. [Hooks](#7-hooks)
8. [Scope del proyecto](#8-scope-del-proyecto)
9. [Learnings](#9-learnings)
10. [Arquitectura multi-agente](#10-arquitectura-multi-agente)
11. [Plugin distribuible](#11-plugin-distribuible)
12. [Errores comunes](#12-errores-comunes)
13. [Checklist de calidad](#13-checklist-de-calidad)
14. [Guía anti-overkill](#14-guía-anti-overkill)
15. [Glosario](#15-glosario)

---

## 1. ¿Qué construir y cuándo?

> La pregunta más importante antes de escribir una sola línea. Construir lo que no necesitas es el error más caro — no por el token que cuesta ahora, sino por el token que costará en cada sesión para siempre.

```
¿Qué necesitas?
│
├── Regla que aplica siempre en este proyecto
│   └── → CLAUDE.md
│
├── Tarea especializada que se repite
│   └── → Agente (.claude/agents/)
│
├── Referencia o template que Claude carga cuando lo necesita
│   └── → Skill (.claude/skills/)
│
├── Algo que debe ocurrir siempre (validar, bloquear, notificar)
│   └── → Hook (.claude/settings.json)
│
├── Contexto del proyecto (estado, decisiones, backlog)
│   └── → Scope (.claude/scope/)
│
├── Lecciones capturadas por sesión
│   └── → Learnings (.claude/learnings/)
│
└── Todo lo anterior, reutilizable en múltiples proyectos
    └── → Plugin (.claude-plugin/)
```

| | Agente local | Skill local | Plugin |
|---|---|---|---|
| Ubicación | `.claude/agents/` | `.claude/skills/` | directorio con `.claude-plugin/` |
| Scope | Solo este repo | Solo este repo | Donde se instale |
| Hooks | `.claude/settings.json` | — | `hooks/hooks.json` |
| Compartir | Solo via el repo | Solo via el repo | `claude plugin add github:...` |

**Regla:** empezar con agentes y skills locales. Convertir a plugin solo cuando se reutiliza en otro proyecto.

---

## 2. Presupuesto de tokens

> Pensar en tokens es como pensar en RAM en los 90: no puedes ignorarlo. La diferencia es que aquí cada megabyte también te cuesta plata.

El principio más importante de toda la guía. Cada byte en contexto tiene costo.

### Las tres capas de costo

```
Capa 1 — SIEMPRE en contexto (costo fijo por sesión)
  CLAUDE.md           → se re-inyecta en CADA tool call (el más caro)
  Agent descriptions  → presentes en el system prompt
  Skill metadata      → 30-50 tokens por skill registrada

Capa 2 — BAJO DEMANDA (costo variable)
  Gotchas inline      → en el system prompt del agente, cero Read calls
  SKILL.md content    → se carga cuando Claude lo activa
  Learnings           → solo el dominio relevante
  Scope               → solo el archivo que el agente necesita

Capa 3 — COSTO CERO en el contexto principal
  Agente en ejecución → corre en contexto aislado
```

### Límites por archivo

| Archivo | Límite | Por qué |
|---|---|---|
| `CLAUDE.md` | < 30 líneas | Se re-inyecta en cada tool call |
| Hub skill (proyecto con CLAUDE.md) | < 40 líneas | Siempre en contexto |
| Hub skill (plugin sin CLAUDE.md) | < 60 líneas | El hub es el único dispatch |
| Skills de referencia | < 200 líneas | Se cargan bajo demanda |
| Learnings por dominio | < 150 líneas | Se cargan solo cuando aplica |
| Scope por dominio | < 50 líneas | Deben ser densos y directos |
| `description` | < 1,024 chars | Hard limit del spec |

### CLAUDE.md — plantilla

```markdown
# [Proyecto]

## Dispatch
¿≥2 sistemas o ≥3 archivos? → @lead
¿Bug?                       → @debugger
¿[Dominio A]?               → @agente-a
¿Revisión?                  → @reviewer
¿Fin de sesión?             → @postmortem

## Reglas duras
- Regla crítica 1
- Código directo — sin over-engineering

## Learnings
[Dominio A]: leer `.claude/learnings/dominio-a.md`

## Scope
Leer `.claude/scope/scope-index.md` antes de cualquier tarea.
```

---

## 3. Estimados de consumo

### Costo fijo por sesión

| Componente | Tokens | Notas |
|---|---|---|
| CLAUDE.md (~30 líneas) | ~200 | Se re-inyecta en cada tool call |
| Hub skill (~40 líneas) | ~280 | Solo si auto-trigger está activo |
| Agent descriptions (×10) | ~400 | ~40t por agente registrado |
| scope-index.md (~20 líneas) | ~120 | Si está en CLAUDE.md |
| **Total fijo mínimo** | **~1,000** | Por sesión, antes de cualquier tarea |

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

### Impacto del modelo

| Modelo | Costo relativo | Cuándo |
|---|---|---|
| haiku | 1x | Tareas fijas: git, postmortem, reviewer de checklist |
| sonnet | 5x | Implementación, debugging |
| opus | 15x | Arquitectura con trade-offs complejos |

---

## 4. Analogía — cómo pensar el sistema

> Si la documentación oficial no tiene sentido todavía, empieza aquí.

### El restaurante

```
CLAUDE.md         → el pizarrón de reglas en la cocina
Agentes           → los cocineros especializados
Lead              → el jefe de cocina (coordina, no cocina)
Skills            → los recetarios (referencia, no ejecutan)
Hooks             → el sistema de control de calidad
Scope             → el menú del día
Learnings         → el cuaderno de errores de la cocina
Tokens            → el tiempo del turno
```

### La regla de oro

> Un agente que hace una sola cosa bien
> vale más que un agente que hace todo más o menos.

---

## 5. Agentes

### Formato

```markdown
---
name: mi-agente
description: Trigger list. Usar cuando el usuario pide X, menciona Y,
  o el contexto involucra Z.
tools: Read, Write, Edit, Glob, Grep
model: sonnet
---

# Nombre del Agente

Una línea de responsabilidad. Sin narración.

## Gotchas críticos
- Error frecuente 1: causa y fix en una línea.

## Reglas
- Regla concreta
```

### Modelo por tipo de agente

| Agente | Modelo | Criterio |
|---|---|---|
| git, postmortem, reviewer de checklist | `haiku` | Instrucciones fijas — 5x más barato |
| Implementador, debugger | `sonnet` | Razona sobre contexto variable |
| Arquitectura con trade-offs complejos | `opus` | Decisiones de alto nivel |

### Tools por responsabilidad

| Rol | Tools |
|---|---|
| Solo lectura (reviewer, auditor) | `Read, Glob, Grep` |
| Implementador | `Read, Write, Edit, Glob, Grep` |
| Orchestrador | `Read, Write, Edit, Glob, Grep` — sin Bash |
| Git / shell | `Bash, Read` |
| Postmortem | `Read, Write, Glob, Grep, Bash` |

### Output format — la palanca más barata

```markdown
## Output — siempre este formato, nada más
Hipótesis 1 (más probable): [causa en 1 línea]
Confirmar: [acción mínima]
Fix: [cambio concreto]

Hipótesis 2: [solo si la 1 no aplica]
```

**Impacto medido:** ahorro de ~30-65% de tokens vs sin formato forzado.

### Agentes base para cualquier proyecto

| Agente | Responsabilidad | Modelo |
|---|---|---|
| `lead` | Orchestrador ≥2 sistemas | sonnet |
| `reviewer` | Convenciones y calidad | haiku |
| `debugger` | Diagnóstico antes de modificar | sonnet |
| `git` | Ramas, commits, PRs | haiku |
| `postmortem` | Lecciones al final de sesión | haiku |
| `curador` | Mantenimiento mensual de learnings | haiku |

### Límites de tamaño

| Modelo | Límite del prompt | Por qué |
|---|---|---|
| haiku | < 60 líneas | Instrucciones concretas |
| sonnet | < 120 líneas | Razonamiento variable |
| opus | < 80 líneas | Decisiones de alto nivel |

---

## 6. Skills

### Tipos y configuración

| Tipo | `disable-model-invocation` | Tamaño | Uso |
|---|---|---|---|
| Hub / dispatch | `false` | < 40 líneas | Triage automático |
| Referencia | `true` | < 200 líneas | Convenciones, patrones |
| Template | `true` | Sin límite práctico | Nunca en contexto activo |

### Controlar cuándo se activa una skill

```json
{
  "skillOverrides": {
    "mi-hub": "user-invocable-only",
    "mi-referencia": "off"
  }
}
```

---

## 7. Hooks

> Los hooks son el único mecanismo de garantía real del sistema.

### Dónde van

| Contexto | Archivo |
|---|---|
| Proyecto local | `.claude/settings.json` |
| Plugin | `hooks/hooks.json` |

### Eventos esenciales

| Evento | Bloqueable | Uso |
|---|---|---|
| `PreToolUse` | **Sí** | Validar antes de escribir o ejecutar |
| `PostToolUse` | No | Confirmar, notificar, encadenar acciones |
| `SubagentStop` | No | Encadenar agentes, notificar al usuario |
| `Stop` | No | Recordatorios al final de sesión |

### Reglas de hooks

- `chmod +x` en todos los scripts
- `try/except` en **todos** los hooks
- PreToolUse usa JSON con `permissionDecision` — nunca `exit(2)`
- SubagentStop y PostToolUse usan `systemMessage` — nunca `echo` crudo
- Checks de string en Bash: usar `re.split` para aislar el primer comando
- Paths: `Path(__file__).parent.parent.parent` — nunca paths absolutos
- MultiEdit: extraer de `edits[].new_str`, no de `tool_input.new_str`

---

## 8. Scope del proyecto

### Estructura

```
.claude/scope/
├── scope-index.md        → resumen de 20 líneas — todos lo leen
├── scope-[sistema-a].md  → detalle de un sistema específico
└── scope-[sistema-b].md
```

### Quién lee qué

- **CLAUDE.md** → apunta solo a `scope-index.md`
- **Lead / orchestrador** → index + scope del sistema a planificar
- **Especialistas** → ninguno (reciben contexto del lead)
- **Postmortem** → index (para actualizar estado)

---

## 9. Learnings

### Estructura

```
.claude/learnings/
├── learnings-[dominio-a].md   → < 150 líneas
├── learnings-[dominio-b].md
└── learnings-general.md
```

### Formato de entry

```markdown
- [YYYY-MM-DD] [CATEGORÍA] descripción concreta del problema.
  Causa: por qué ocurre.
  Solución: fix exacto o patrón correcto.
```

### Flujo postmortem → learnings → curador

```
Sesión de trabajo
    ↓
@postmortem  →  escribe entries en learnings/learnings-[dominio].md
    ↓
stop.py      →  avisa si algún learnings supera 150 líneas
    ↓
@curador     →  mensual: dedup + prune + promueve gotchas críticos inline
```

---

## 10. Arquitectura multi-agente

### Flujo de trabajo recomendado

```
1. Commitear pendientes        → @git
2. Nueva rama                  → @git
3. Implementación              → especialista o @lead
4. Revisión                    → @reviewer
5. PR + merge                  → @git
6. Fin de sesión               → @postmortem
```

### Reglas de diseño

- **Agentes = contextos aislados** — lo que lee un agente no contamina el hilo principal
- **No nesting** — un especialista no puede invocar otro especialista
- **El lead no tiene Bash** — coordina con instrucciones, no ejecuta
- **Commitear antes de crear rama** — los cambios se mezclan si no

---

## 11. Plugin distribuible

Solo cuando necesitas reutilizar en múltiples proyectos o compartir con el equipo.

### Estructura

```
mi-plugin/
├── .claude-plugin/
│   └── plugin.json       ← REQUERIDO
├── agents/
├── skills/
├── hooks/
│   └── hooks.json        ← REQUERIDO si usas hooks
└── README.md             ← REQUERIDO para distribución
```

### Probar localmente

```bash
claude --plugin-dir ./mi-plugin   # cargar sin instalar
/reload-plugins                   # recargar cambios
/hooks                            # verificar hooks registrados
```

---

## 12. Errores comunes

### 🔴 Críticos

| Error | Síntoma | Fix |
|---|---|---|
| CLAUDE.md largo | Cada tool call consume tokens antes de trabajar | < 30 líneas |
| Hub auto-trigger con dispatch en CLAUDE.md | ~280t extra por tarea | `skillOverrides: {"hub": "user-invocable-only"}` |
| Sin model en agente | Todos usan el mismo modelo caro | Especificar siempre |
| Reviewer con sonnet | Costo de implementador para checklist | haiku |
| Bash en orchestrador | El lead ejecuta en vez de delegar | Sacar Bash |
| Postmortem escribe en el hub | Costo fijo crece con cada sesión | Escribir en `learnings/` |
| `new_str` en MultiEdit siempre vacío | Validación bypaseada sin error | Extraer de `edits[].new_str` |
| PreToolUse con exit 2 | Error sin razón estructurada | JSON `permissionDecision: deny`, exit 0 |
| Path absoluto en hook | Hook rompe al mover el proyecto | `Path(__file__).parent.parent.parent` |
| Agente git hace push a master | Irreversible | Hook PreToolUse que bloquea |
| Reviewer con ≥7 archivos | 34 tool uses → 22.7k tokens (medido) | Solo archivos directamente modificados (≤4) |

### 🟡 Frecuentes

| Error | Síntoma | Fix |
|---|---|---|
| `hooks.json` faltante | Scripts Python nunca se ejecutan | Crear `hooks/hooks.json` |
| Doc monolítico | Agente lee 500 líneas innecesarias | Dividir por dominio |
| Contenido duplicado | Se paga dos veces en tokens | Un solo lugar por contenido |
| Sin protocolo de fallo bash | Loop de workarounds infinito | Máximo 2 ciclos |
| Learnings monolítico | 500+ líneas se cargan siempre | Fragmentar en dominios |
| Agente de diagnóstico sin output format | 3-4x más tokens en la respuesta | Agregar `## Output` con template compacto |

---

## 13. Checklist de calidad

```
CLAUDE.md
□ < 30 líneas
□ Solo triage y reglas críticas
□ Referencia a scope-index.md
□ Sin tablas ni ejemplos de código

Agentes
□ description como trigger list
□ model especificado (haiku/sonnet/opus)
□ tools al mínimo necesario
□ orchestrador sin Bash
□ reviewer con haiku
□ gotchas críticos inline
□ agentes de diagnóstico tienen sección ## Output con formato forzado
□ sin contenido duplicado con skills o docs

Skills
□ Hub: disable-model-invocation: false, < 40 líneas
□ Hub con dispatch en CLAUDE.md → skillOverrides: user-invocable-only
□ Referencias: disable-model-invocation: true

Scope
□ scope-index.md < 20 líneas
□ Un archivo por sistema, < 50 líneas
□ Postmortem lo actualiza al terminar sesión

Learnings
□ Un archivo por dominio, < 150 líneas
□ Entries concretas: problema + causa + solución
□ Top 5-10 gotchas críticos inline en el agente correspondiente
□ Curador para mantenimiento mensual (no en cada sesión)
□ Postmortem escribe en learnings/ — NUNCA en el hub

Hooks
□ settings.json declara todos los hooks
□ Scripts con chmod +x
□ PreToolUse usa JSON permissionDecision
□ SubagentStop y PostToolUse usan systemMessage
□ try/except en TODOS los hooks
□ Sin paths absolutos
□ MultiEdit extrae edits[].new_str

Plugin (si aplica)
□ plugin.json con campos del spec
□ README.md con instalación y uso
□ hooks/hooks.json existe
```

---

## 14. Guía anti-overkill

### La pregunta que frena el overkill

> **¿Qué pasa si NO lo hago?**

Si la respuesta es "nada, funciona igual" → no lo construyas.

### Cuándo NO construir cada componente

| Componente | Overkill cuando... | Alternativa |
|---|---|---|
| Agente nuevo | La tarea ocurre < 3 veces | Agregar una sección al agente existente |
| Hook | La regla no tiene consecuencias reales si se ignora | Regla en el prompt |
| Plugin | El código se usa en un solo proyecto | Agente/skill local |
| Curador | < 3 meses o learnings < 150 líneas | No correrlo todavía |
| Hub skill | CLAUDE.md ya tiene el dispatch completo | `skillOverrides: user-invocable-only` |
| Opus | La tarea es implementación, checklist o git | haiku o sonnet |
| Lead | La tarea involucra 1 sistema y < 3 archivos | Especialista directo |

### El costo del "por si acaso"

```
Un agente que nunca se invoca:          ~40t en system prompt por sesión
Una skill con auto-trigger innecesaria: ~280t por tarea (LLM call)
Un hook que corre en cada Bash:         ~50ms de latencia por comando
Un learnings de 200 líneas:            ~1,400t cuando se carga
Un CLAUDE.md de 60 líneas:             ~400t re-inyectados en CADA tool call
```

---

## 15. Glosario

**Token** — La unidad de costo de Claude. ~½ de una palabra en español. Todo lo que está en contexto consume tokens. Tokens = plata.

**Contexto** — La "memoria de trabajo" de Claude. Tiene un límite y tiene costo. Si algo está en contexto, Claude lo ve y lo procesa.

**Capa 3 / Contexto aislado** — Cuando un agente corre, lo hace en su propio contexto separado. Lo que el agente lee no contamina el hilo principal. Gratis para el hilo principal.

**haiku** — El más barato. 1x costo de referencia. Para tareas con instrucciones fijas.

**sonnet** — El intermedio. 5x más caro que haiku. Para implementación y debugging.

**opus** — El más poderoso y caro. 15x más caro que haiku. Para arquitectura con trade-offs complejos.

**Agente** — Claude con un rol fijo, herramientas específicas y su propio system prompt. Corre en contexto aislado. Se invoca con `@nombre-agente`.

**Skill** — Archivo de referencia (Markdown) que Claude carga cuando lo necesita. Comparte el hilo principal. Se invoca con `/nombre-skill`.

**Hub** — Skill especial de triage siempre en contexto. Su único trabajo: decirle a Claude qué agente usar.

**Hook** — Script Python que se ejecuta automáticamente cuando Claude hace algo. `PreToolUse` es el único tipo bloqueante.

**Plugin** — Agentes + skills + hooks empaquetados con `plugin.json`. Se instala con `claude plugin add github:usuario/repo`.

**Learnings** — Archivos Markdown donde el postmortem escribe lecciones por sesión. Fragmentados por dominio. Se cargan bajo demanda. Límite: 150 líneas por archivo.

**Gotcha** — Error conocido documentado para que el agente no lo repita.

**Gotcha inline** — Gotcha directamente en el system prompt del agente. Cero Read calls — el agente ya lo sabe de entrada.

**Postmortem** — Agente que captura lecciones de sesión en learnings. Nunca escribe en el hub.

**Curador** — Agente mensual que mantiene los learnings: elimina duplicados y promueve gotchas críticos a inline.

**Trigger list** — La descripción de un agente, escrita para que Claude sepa cuándo activarlo. La parte más importante del agente.

**skillOverrides** — Configuración en `settings.json` para controlar si una skill se activa: `on`, `user-invocable-only`, o `off`.

**ADR (Architecture Decision Record)** — Entrada en el scope que documenta una decisión de diseño. Inmutable — nunca se edita, solo se agrega.

---

## Recursos oficiales

- [Agents](https://code.claude.com/docs/en/sub-agents)
- [Skills](https://code.claude.com/docs/en/skills)
- [Hooks](https://code.claude.com/docs/en/hooks-guide)
- [Plugins](https://code.claude.com/docs/en/plugins)
- [Agent Teams](https://code.claude.com/docs/en/agent-teams)
