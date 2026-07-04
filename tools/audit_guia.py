#!/usr/bin/env python3
"""
audit_guia.py — verifica que el enforcement de la guía no esté muerto (§13).

La guía vive en 5 archivos (guia-00-indice.md + 01-fundamentos/02-construccion/
03-calidad/04-avanzado). Los checks corren agregando los 5, pero cualquier cosa
sensible a límites de sección (budget de -quick, sección >150 líneas, fences)
se calcula POR ARCHIVO — un límite nunca cruza de un archivo a otro.

Checks:
  1. Cada <!-- §N --> tiene entry en el KEYWORD_MAP del hook instalado
     Y en la copia embebida de §26 (exentas: §1, §4, §15 — intro/glosario)
  2. LINES_BUDGET del hook instalado == el de la copia embebida
  3. Ningún <!-- §N[-quick|-ref] --> dentro de un code fence
  4. Cada bloque -quick cabe en LINES_BUDGET (lo que excede se trunca al inyectar)
  5. Sección > 150 líneas sin split quick/ref
  6. Fences balanceados al final de cada archivo
  7. Versión del header (guia-00-indice.md) == versión de README.md y README.es.md

Uso: python3 tools/audit_guia.py   (exit 0 = limpio, 1 = violaciones)
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GUIA_FILES = sorted(REPO.glob("guia-0*.md"))
HUB = REPO / "guia-00-indice.md"
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
    if not GUIA_FILES:
        errors.append("no encontré archivos guia-0*.md en el repo")
        print("❌ 1 violación(es):\n  - " + errors[0])
        return 1

    hook_src = HOOK.read_text() if HOOK.exists() else ""
    _, installed_budget = parse_keyword_map(hook_src, "hook instalado") if hook_src else (set(), None)
    budget = installed_budget or 80

    anchors: set[int] = set()
    quicks: dict[int, tuple[Path, int]] = {}  # n -> (archivo, línea)
    all_texts = []

    for path in GUIA_FILES:
        text = path.read_text()
        all_texts.append(text)
        lines = text.splitlines()

        # --- markers, fences y posiciones (todo scopeado a ESTE archivo) ---
        file_marks = []
        for ln, line, inside in fence_state_machine(lines):
            m = MARKER.match(line.strip())
            if m:
                n, kind = int(m.group(1)), m.group(2)
                if inside:
                    errors.append(f"{path.name}:{ln}: marker §{n}{kind or ''} DENTRO de un code fence")
                file_marks.append((ln, n, kind))
                if kind is None:
                    anchors.add(n)
                elif kind == "-quick":
                    quicks[n] = (path, ln)

        # --- tamaño de quicks: corta en el próximo marker DE ESTE ARCHIVO ---
        positions = sorted(ln for ln, _, _ in file_marks)
        for n, (qpath, qln) in list(quicks.items()):
            if qpath != path:
                continue
            nxt = next((p for p in positions if p > qln), len(lines) + 1)
            size = nxt - qln - 1
            if size > budget:
                errors.append(f"{path.name} §{n}-quick: {size} líneas > budget {budget} — se trunca al inyectar")

        # --- secciones > 150 sin split, dentro de ESTE archivo -------------
        plains = sorted((ln, n) for ln, n, k in file_marks if k is None)
        for i, (ln, n) in enumerate(plains):
            end = plains[i + 1][0] if i + 1 < len(plains) else len(lines)
            if end - ln > 150 and n not in quicks:
                errors.append(f"{path.name} §{n}: {end - ln} líneas sin split quick/ref")

    # --- KEYWORD_MAP: instalado vs embebido (§26) vs anchors (todos los archivos) ---
    all_text = "\n".join(all_texts)
    embedded, embedded_budget = parse_keyword_map(all_text, "copia embebida §26")
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

    # --- versión hub (guia-00-indice.md) == READMEs -------------------------
    hub_text = HUB.read_text() if HUB.exists() else ""
    ver = re.search(r"\*\*Versión:\*\*\s*(v\d+\.\d+)", hub_text)
    if not ver:
        errors.append("no encontré la versión en guia-00-indice.md")
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
    print(f"✅ audit limpio — {len(GUIA_FILES)} archivos, {len(anchors)} secciones, {len(quicks)} quicks ≤ {budget} líneas, "
          f"KEYWORD_MAP sincronizado, versión {ver.group(1) if ver else '?'} en sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())
