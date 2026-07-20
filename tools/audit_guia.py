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
  4. Inyección fence-safe (mirror de build_injection del hook):
       - con -quick: el bloque quick entero está balanceado, no vacío y ≤ QUICK_CEILING
       - sin -quick: la cápsula del head es no vacía y sin code fence
     (vacío = la sección nunca se inyecta; fence impar = contexto corrupto — silenciosos)
  5. Sección > 150 líneas sin split quick/ref
  6. Fences balanceados al final de cada archivo
  7. Versión del header (guia-00-indice.md) == versión de README.md y README.es.md
  8. Staleness de hechos fechados (§3 del protocolo: cazar el fallo silencioso,
     aplicado a la guía misma):
       - <!-- vence: YYYY-MM-DD --> ya pasada → ERROR (hecho con fecha de expiración
         conocida — ej. pricing introductorio — que nadie recheckeó a tiempo)
       - "verificado/corregido YYYY-MM-DD" con > STALE_DAYS de antigüedad → WARNING
         (no bloquea el exit code, solo avisa que puede valer la pena recheckear)
  9. README.es.md == concat de las 5 guías (vía tools/gen_readme_es.build_es).
     README.es.md es derivado; editar una guía sin regenerar lo deja stale en
     silencio — el check 7 solo compara la versión, no el cuerpo.

Uso: python3 tools/audit_guia.py   (exit 0 = limpio, 1 = violaciones)
"""
import re
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GUIA_FILES = sorted(REPO.glob("guia-0*.md"))
HUB = REPO / "guia-00-indice.md"
HOOK = Path.home() / ".claude" / "hooks" / "guia_context.py"
EXEMPT = {1, 4, 15}  # intro/analogía/glosario — sin entry por diseño
MARKER = re.compile(r"^<!-- §(\d+)(-quick|-ref)? -->$")
STALE_DAYS = 90
QUICK_CEILING = 5500  # mirror del hook: un -quick más grande que esto se inyecta como cápsula
VENCE = re.compile(r"<!--\s*vence:\s*(\d{4}-\d{2}-\d{2})\s*-->")
VERIFICADO = re.compile(r"(?:[Vv]erificado|[Cc]orregido)(?:\s+\d{4}-\d{2}-\d{2})?[^\n.]{0,60}?(\d{4}-\d{2}-\d{2})")

errors: list[str] = []
warnings: list[str] = []


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
    budget = re.search(r"CAP_CHARS\s*=\s*(\d+)", text)
    if not sections:
        errors.append(f"{label}: no pude parsear el KEYWORD_MAP")
    return sections, int(budget.group(1)) if budget else None


def build_capsule_lines(lines, start, budget):
    """Réplica del build_capsule del hook — devuelve las líneas de la cápsula o None.
    Debe seguir espejando ~/.claude/hooks/guia_context.py (misma clase de divergencia
    silenciosa que el KEYWORD_MAP)."""
    def has_body(acc):
        return any(l.strip() and not l.lstrip().startswith("#") for l in acc)
    out, used, in_fence = [], 0, False
    for line in lines[start:]:
        if re.match(r"<!-- §\d", line):
            break
        if re.match(r"\s*```", line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not line.strip() and (not out or not out[-1].strip()):
            continue
        if line.strip() in ("---", "***", "___"):
            continue
        if has_body(out) and used + len(line) + 1 > budget:
            break
        out.append(line)
        used += len(line) + 1
    while out and not out[-1].strip():
        out.pop()
    return out if has_body(out) else None


def main() -> int:
    if not GUIA_FILES:
        errors.append("no encontré archivos guia-0*.md en el repo")
        print("❌ 1 violación(es):\n  - " + errors[0])
        return 1

    hook_src = HOOK.read_text() if HOOK.exists() else ""
    _, installed_budget = parse_keyword_map(hook_src, "hook instalado") if hook_src else (set(), None)
    budget = installed_budget or 550

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

        # --- inyección fence-safe: mirror de build_injection del hook ---
        # con -quick: se inyecta el bloque quick COMPLETO → debe estar balanceado, no vacío
        #   y ≤ QUICK_CEILING (si no, corrompe el contexto o infla la inyección).
        # sin -quick: cápsula fence-safe del head → no vacía y sin fence.
        # Ambos fallos son silenciosos (vacío = nunca se inyecta; fence impar = contexto roto).
        by_kind: dict[int, dict] = {}
        for ln, n, kind in file_marks:
            by_kind.setdefault(n, {})[kind] = ln
        marker_lines = sorted(ln for ln, _, _ in file_marks)
        for n, kinds in by_kind.items():
            if n in EXEMPT:
                continue
            if "-quick" in kinds:
                q = kinds["-quick"]
                nxt = next((p for p in marker_lines if p > q), len(lines) + 1)
                block = lines[q:nxt - 1]
                while block and not block[0].strip():
                    block = block[1:]
                while block and not block[-1].strip():
                    block = block[:-1]
                has_body = any(l.strip() and not l.lstrip().startswith("#") for l in block)
                fences = sum(1 for l in block if re.match(r"\s*```", l))
                chars = len("\n".join(block))
                if not has_body:
                    errors.append(f"{path.name} §{n}-quick: bloque sin sustancia — no se inyectaría nada")
                elif fences % 2:
                    errors.append(f"{path.name} §{n}-quick: {fences} fences (impar) — el quick se inyecta entero y rompería el contexto")
                elif chars > QUICK_CEILING:
                    errors.append(f"{path.name} §{n}-quick: {chars} chars > techo {QUICK_CEILING} — se inyecta entero; recortalo o movelo a -ref")
            else:
                start = kinds.get(None)
                if start is None:
                    continue
                cap = build_capsule_lines(lines, start, budget)
                if cap is None:
                    errors.append(f"{path.name} §{n}: cápsula de inyección vacía (la cabeza es toda código/marcadores) — no se inyectaría nada")
                elif any(x.lstrip().startswith("```") for x in cap):
                    errors.append(f"{path.name} §{n}: cápsula con code fence — la lógica de skip está rota")

        # --- secciones > 150 sin split, dentro de ESTE archivo -------------
        plains = sorted((ln, n) for ln, n, k in file_marks if k is None)
        for i, (ln, n) in enumerate(plains):
            end = plains[i + 1][0] if i + 1 < len(plains) else len(lines)
            if end - ln > 150 and n not in quicks:
                errors.append(f"{path.name} §{n}: {end - ln} líneas sin split quick/ref")

        # --- staleness: hechos fechados que vencieron o quedaron viejos ----
        today = date.today()
        for ln, line in enumerate(lines, 1):
            for m in VENCE.finditer(line):
                d = date.fromisoformat(m.group(1))
                if d < today:
                    errors.append(
                        f"{path.name}:{ln}: <!-- vence: {d} --> ya pasó ({(today - d).days} días) — recheckear el hecho")
            for m in VERIFICADO.finditer(line):
                d = date.fromisoformat(m.group(1))
                age = (today - d).days
                if age > STALE_DAYS:
                    warnings.append(
                        f"{path.name}:{ln}: fecha de verificación de {age} días — considerar recheck")

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
                f"CAP_CHARS divergió: instalado={installed_budget} vs embebido={embedded_budget}")
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

    # --- README.es.md == concat de las 5 guías (check 9) --------------------
    # README.es.md es un artefacto derivado (ver tools/gen_readme_es.py). Sin
    # este check, editar una guía sin regenerar deja el ES stale en silencio
    # (el check 7 solo compara la cadena de versión, no el cuerpo).
    try:
        from gen_readme_es import build_es
        actual_es = (REPO / "README.es.md").read_text()
        if actual_es != build_es():
            errors.append("README.es.md desincronizado con las guías — corré: "
                          "python3 tools/gen_readme_es.py")
    except Exception as e:  # noqa: BLE001 — el generador ausente/roto es un hallazgo, no silencio
        errors.append(f"no pude verificar README.es.md contra el generador: {e}")

    if warnings:
        print(f"⚠️  {len(warnings)} advertencia(s) de staleness (no bloquean el exit code):")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print(f"❌ {len(errors)} violación(es):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"✅ audit limpio — {len(GUIA_FILES)} archivos, {len(anchors)} secciones, inyección fence-safe "
          f"({len(quicks)} quicks completos / resto cápsula ≤{budget}c), KEYWORD_MAP sincronizado, "
          f"versión {ver.group(1) if ver else '?'} en sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())
