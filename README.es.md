# Guía del Dev Pobre: Agentes y Plugins en Claude Code
*Máxima eficiencia. Mínimo gasto. Cero disculpas.*

**Autor:** Félix Sotelo — Dev pobre con aspiraciones de rico
**Versión:** v5.0 · Validada en producción · 2026-06-21

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
| Crear un hook | §7 — 10 eventos, `updatedInput`, npm security guard |
| Armar un plugin distribuible | §11 — estructura, plugin.json, instalación |
| Configurar learnings + curador | §9 — flujo postmortem → learnings → curador |
| Diseñar arquitectura multi-agente | §10 — lead, especialistas, flujo de trabajo |
| Elegir el modelo correcto | §25 — haiku/sonnet/opus + `effort` como alternativa |
| Ver un plan antes de ejecutar | §17 + §28 — skill `/plan` y cuándo usarla |
| Usar shortcuts de prompts | §28 — Prompt Library con 8 shortcuts y 4 recipes |
| Armar mi propio contexto global | §29 — construir `~/.claude/` desde cero |
| Auto-inyectar contexto de la guía | §26 — hook `guia_context.py` |
| Saber si lo que construí es overkill | §14 — árbol anti-overkill |
| Saber cuándo parar de optimizar | §23 — techos reales de tokens y palancas por impacto |
| Evitar los errores más caros | §12 — primera tabla |
| Validar lo que construí | §13 — checklist de calidad |

---

## Novedades en v5.0

| Área | Cambio |
|---|---|
| **§6 Skills** | Frontmatter completo (17 campos), lifecycle, `context:fork`, supporting files, `ultrathink` |
| **§7 Hooks** | 10 eventos (antes 4), `updatedInput`, npm security guard (supply chain + slopsquatting) |
| **§25 Modelo** | `effort` como alternativa a Opus (~5×), framework de decisión, ejemplo `security-auditor` |
| **§28 NUEVO** | Prompt Library — 8 shortcuts con tags, 4 recipes, 4 Leyes |
| **§29 NUEVO** | Contexto global propio — construir `~/.claude/` desde cero |
| **Docs** | 5 errores factuales corregidos vs documentación oficial de Claude Code |

---

## Docs oficiales

[Agents](https://code.claude.com/docs/en/sub-agents) · [Skills](https://code.claude.com/docs/en/skills) · [Hooks](https://code.claude.com/docs/en/hooks-guide) · [Plugins](https://code.claude.com/docs/en/plugins) · [Agent Teams](https://code.claude.com/docs/en/agent-teams)

---

## Contribuir

Si querés sugerir algo, abrí un [Issue](../../issues). Si encaja en el flujo de trabajo, lo incorporo. Gracias por leer.
