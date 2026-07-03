#!/usr/bin/env python3
"""
audit_guia.py — verifica que el enforcement de la guía no esté muerto (§13).

Checks:
  1. Cada <!-- §N --> tiene entry en el KEYWORD_MAP del hook instalado
     Y en la copia embebida de §26 (exentas: §1, §4, §15 — intro/glosario)
  2. LINES_BUDGET del hook instalado == el de la copia embebida
  3. Ningún <!-- §N[-quick|-ref] --> dentro de un code fence
  4. Cada bloque -quick cabe en LINES_BUDGET (lo que excede se trunca al inyectar)
  5. Sección > 150 líneas sin split quick/ref
  6. Fences balanceados al final del archivo
  7. Versión del header de la guía == versión de README.md y README.es.md

Uso: python3 tools/audit_guia.py   (exit 0 = limpio, 1 = violaciones)
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GUIA = REPO / "guia-agentes-plugins-claude-code.md"
HOOK = Path.home() / ".claude" / "hooks" / "guia_context.py"
EXEMPT = {1, 4, 15}  # intro/analogía/glosario — sin entry por diseño
MARKER = re.compile(r"^<!-- §(\d+)(-quick|-ref)? -->$")

errors: list[str] = []


def fence_state_machine(lines):
    """Yields (line_number, line, inside_fence). CommonMark: cierra un run >= apertura."""
    stack = []
    for i, line in enumerate(lines, 1):
        m = re.match(r"^\s*(`{3,})", line)
        if m:
            run = len(m.group(1))
            if stack and run >= stack[-1]:
                stack.pop()
            else:
                stack.append(run)
            yield i, line, bool(stack)
        else:
            yield i, line, bool(stack)
    if stack:
        errors.append(f"fence sin cerrar al EOF (nivel {len(stack)})")


def parse_keyword_map(text: str, label: str):
    """Extrae números de sección y LINES_BUDGET de un KEYWORD_MAP en `text`."""
    sections = {int(n) for n in re.findall(r"\],\s*(\d+)\),", text)}
    budget = re.search(r"LINES_BUDGET\s*=\s*(\d+)", text)
    if not sections:
        errors.append(f"{label}: no pude parsear el KEYWORD_MAP")
    return sections, int(budget.group(1)) if budget else None


def main() -> int:
    lines = GUIA.read_text().splitlines()

    # --- markers, fences y posiciones -------------------------------------
    anchors, quicks, all_marks = set(), {}, []
    for ln, line, inside in fence_state_machine(lines):
        m = MARKER.match(line.strip())
        if m:
            n, kind = int(m.group(1)), m.group(2)
            if inside:
                errors.append(f"línea {ln}: marker §{n}{kind or ''} DENTRO de un code fence")
            all_marks.append((ln, n, kind))
            if kind is None:
                anchors.add(n)
            elif kind == "-quick":
                quicks[n] = ln

    # --- tamaño de quicks (regla del hook: corta en el próximo <!-- §) ----
    hook_src = HOOK.read_text() if HOOK.exists() else ""
    _, installed_budget = parse_keyword_map(hook_src, "hook instalado") if hook_src else (set(), None)
    budget = installed_budget or 80
    positions = sorted(ln for ln, _, _ in all_marks)
    for n, qln in quicks.items():
        nxt = next((p for p in positions if p > qln), len(lines) + 1)
        size = nxt - qln - 1
        if size > budget:
            errors.append(f"§{n}-quick: {size} líneas > budget {budget} — se trunca al inyectar")

    # --- secciones > 150 sin split -----------------------------------------
    plains = sorted((ln, n) for ln, n, k in all_marks if k is None)
    for i, (ln, n) in enumerate(plains):
        end = plains[i + 1][0] if i + 1 < len(plains) else len(lines)
        if end - ln > 150 and n not in quicks:
            errors.append(f"§{n}: {end - ln} líneas sin split quick/ref")

    # --- KEYWORD_MAP: instalado vs embebido vs anchors ---------------------
    guia_text = GUIA.read_text()
    embedded, embedded_budget = parse_keyword_map(guia_text, "copia embebida §26")
    expected = anchors - EXEMPT
    if hook_src:
        installed, _ = parse_keyword_map(hook_src, "hook instalado")
        for miss in sorted(expected - installed):
            errors.append(f"§{miss}: sin entry en KEYWORD_MAP del hook INSTALADO")
        if installed != embedded:
            diff = installed.symmetric_difference(embedded)
            errors.append(f"KEYWORD_MAP divergió entre hook instalado y copia §26: {sorted(diff)}")
        if embedded_budget is not None and installed_budget != embedded_budget:
            errors.append(
                f"LINES_BUDGET divergió: instalado={installed_budget} vs embebido={embedded_budget}")
    for miss in sorted(expected - embedded):
        errors.append(f"§{miss}: sin entry en la copia embebida del KEYWORD_MAP (§26)")

    # --- versión guía == READMEs -------------------------------------------
    ver = re.search(r"\*\*Versión:\*\*\s*(v\d+\.\d+)", guia_text)
    if not ver:
        errors.append("no encontré la versión en el header de la guía")
    else:
        for readme in ("README.md", "README.es.md"):
            txt = (REPO / readme).read_text()
            rv = re.search(r"\*\*Versi[oó]n:\*\*\s*(v\d+\.\d+)", txt)
            if not rv:
                errors.append(f"{readme}: sin línea de versión parseable")
            elif rv.group(1) != ver.group(1):
                errors.append(f"{readme}: {rv.group(1)} != guía {ver.group(1)}")

    if errors:
        print(f"❌ {len(errors)} violación(es):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"✅ audit limpio — {len(anchors)} secciones, {len(quicks)} quicks ≤ {budget} líneas, "
          f"KEYWORD_MAP sincronizado, versión {ver.group(1) if ver else '?'} en sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())
