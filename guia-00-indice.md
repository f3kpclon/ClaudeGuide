# Guía del Dev Pobre: Agentes y Plugins en Claude Code
*Máxima eficiencia. Mínimo gasto. Cero disculpas.*

**Autor:** Félix Sotelo — Dev pobre con aspiraciones de rico
**Versión:** v5.21 · fix inconsistencia 40 vs 60 líneas en budget de hub — §6 no reflejaba la excepción de plugin-sin-CLAUDE.md que ya existía en §2, encontrada auditando design-ios contra la guía — 2026-07-05

---

> Cada byte en contexto tiene costo. Esta guía existe para que construyas sistemas poderosos sin que tu tarjeta llore al final del mes.
>
> Si puedes hacer algo con **haiku**, no uses sonnet. Si puedes usar una regla en CLAUDE.md, no crees un agente. Si puedes poner un gotcha inline, no hagas que el agente lea un archivo.
>
> El agente es tan bueno como el contexto que recibe. Contexto vago → el agente improvisa → loops de corrección → tokens ×3-5. Define output, scope y criterio de éxito **antes** de invocar. `/plan` primero. (→ §24)
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
| Escalar memoria a búsqueda semántica | §16 — vector memory, MongoDB Atlas, cuándo migrar |
| Ver plan antes de ejecutar / optimizar prompts | §17 — skill /plan + invocation templates |
| Saber cuándo parar de optimizar tokens | §23 — techos reales, fórmula, palancas por orden de impacto |
| Asegurar un sistema multi-usuario | §18 — 3 capas, security_utils.py, pre_write_guard |
| Preservar contexto entre sesiones | §27 — handoff protocol + auto-compaction |
| Usar CLAUDE.local.md, rules/, output-styles/ | §32 — los archivos que nadie documenta |
| Integrar /rewind, /fork, /compact con hooks | §33 — comandos nativos y sus límites reales |

---

## Índice

### Fundamentos — leer primero
- [§4 — Analogía: cómo pensar el sistema](guia-01-fundamentos.md#4-analogía--cómo-pensar-el-sistema)
- [§1 — ¿Qué construir y cuándo?](guia-01-fundamentos.md#1-qué-construir-y-cuándo)
- [§2 — Presupuesto de tokens](guia-01-fundamentos.md#2-presupuesto-de-tokens)
- [§25 — Modelo correcto (haiku/sonnet/opus)](guia-01-fundamentos.md#25-modelo-correcto--tabla-de-decisión-única)
- [§24 — El factor humano: contexto antes de invocar](guia-01-fundamentos.md#24-el-contrato-del-contexto--el-factor-humano)

### Construcción — lo que más usas
- [§5 — Agentes](guia-02-construccion.md#5-agentes)
- [§7 — Hooks](guia-02-construccion.md#7-hooks)
- [§6 — Skills](guia-02-construccion.md#6-skills)
  - [Los dos ejes de visibilidad](guia-02-construccion.md#los-dos-ejes-de-visibilidad)
- [§8 — Scope del proyecto](guia-02-construccion.md#8-scope-del-proyecto)
- [§9 — Learnings](guia-02-construccion.md#9-learnings)
- [§10 — Arquitectura multi-agente](guia-02-construccion.md#10-arquitectura-multi-agente)
- [§11 — Plugin distribuible](guia-02-construccion.md#11-plugin-distribuible)
- [§31 — Advisor Pattern (validación sin subir de modelo)](guia-02-construccion.md#31-advisor-pattern--validación-sin-subir-de-modelo)
- [§32 — Archivos que nadie documenta (CLAUDE.local.md, output-styles/, rules/, settings.local.json)](guia-02-construccion.md#32-archivos-que-nadie-documenta--el-resto-del-claude)
- [§17 — Plan + Invocation Templates](guia-02-construccion.md#17-plan--invocation-templates--eficiencia-máxima-de-prompts)
- [§26 — Hook global de contexto](guia-02-construccion.md#26-hook-global-de-contexto)
- [§27 — Handoff Protocol](guia-02-construccion.md#27-handoff-protocol)
- [§28 — Prompt Library (shortcuts + recipes)](guia-02-construccion.md#28-prompt-library--shortcuts-para-claude-code)
- [§29 — Contexto global propio](guia-02-construccion.md#29-contexto-global-propio--construir-tu-sistema)
- [§30 — Cloud Agents programados — /schedule y /web-setup](guia-02-construccion.md#30-cloud-agents-programados--schedule-y-web-setup)
- [§33 — Comandos nativos (rewind, clear, compact, fork) + integración con hooks](guia-02-construccion.md#33-comandos-nativos--rewind-clear-compact-fork-y-su-integración-con-agenteshooks)

### Calidad y eficiencia
- [§14 — Guía anti-overkill](guia-03-calidad.md#14-guía-anti-overkill)
- [§12 — Errores comunes](guia-03-calidad.md#12-errores-comunes)
- [§13 — Checklist de calidad](guia-03-calidad.md#13-checklist-de-calidad)
- [§23 — Techos reales de tokens](guia-03-calidad.md#23-techos-reales-de-tokens--cuándo-parar-de-optimizar)
- [§3 — Estimados de consumo](guia-03-calidad.md#3-estimados-de-consumo)

### Avanzado y referencia
- [§16 — Vector Memory](guia-04-avanzado.md#16-vector-memory--upgrade-del-sistema-de-learnings)
- [§18 — Seguridad](guia-04-avanzado.md#18-seguridad)
- [§19 — Testing de agentes](guia-04-avanzado.md#19-testing-de-agentes)
- [§20 — CI/CD](guia-04-avanzado.md#20-cicd)
- [§21 — Observabilidad y debugging](guia-04-avanzado.md#21-observabilidad-y-debugging)
- [§22 — Prompt engineering avanzado](guia-04-avanzado.md#22-prompt-engineering-avanzado)
- [§15 — Glosario](guia-04-avanzado.md#15-glosario)

---


## Mapa de archivos

| Archivo | Contenido |
|---|---|
| `guia-01-fundamentos.md` | 01 · Fundamentos — §4, §1, §2, §25, §24 |
| `guia-02-construccion.md` | 02 · Construcción — §5, §7, §6, §8, §9, §10, §11, §31, §32, §17, §26, §27, §28, §29, §30, §33 |
| `guia-03-calidad.md` | 03 · Calidad y eficiencia — §14, §12, §13, §23, §3 |
| `guia-04-avanzado.md` | 04 · Avanzado y referencia — §16, §18, §19, §20, §21, §22, §15 |

`grep -rn "<!-- §N -->" guia-*.md` encuentra la sección sin importar en qué archivo vive.

---

## Recursos oficiales

- [Agents](https://code.claude.com/docs/en/sub-agents)
- [Skills](https://code.claude.com/docs/en/skills)
- [Hooks](https://code.claude.com/docs/en/hooks-guide)
- [Plugins](https://code.claude.com/docs/en/plugins)
- [Agent Teams](https://code.claude.com/docs/en/agent-teams)
