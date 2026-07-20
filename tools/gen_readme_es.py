#!/usr/bin/env python3
"""
gen_readme_es.py — regenera README.es.md concatenando las 5 guías.

README.es.md NO es un archivo editable a mano: es un artefacto derivado de
guia-00-indice.md + guia-01..04. El transform es un concat con un único
retoque — insertar el banner de idioma tras el primer `---` del hub (que
apunta a la versión inglesa). Todo lo demás (incluidos los headers por-archivo
"# Guía del Dev Pobre — NN · …") se conserva tal cual.

`build_es()` es la fuente de verdad del transform; audit_guia.py la importa
para verificar que el README.es.md commiteado == la regeneración (si divergen,
alguien editó las guías sin regenerar → el check 9 del audit falla).

Uso: python3 tools/gen_readme_es.py   (reescribe README.es.md in-place)
     python3 tools/gen_readme_es.py --check   (exit 1 si está desincronizado)
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HUB = REPO / "guia-00-indice.md"
# Orden fijo: hub primero, luego 01..04 (mismo orden que sorted(glob) del audit).
PARTS = [HUB] + sorted(REPO.glob("guia-0[1-9]*.md"))
BANNER = "> 🌐 **Language / Idioma:** [🇺🇸 English](README.md) · **🇪🇸 Español**"


def build_es() -> str:
    """Devuelve el contenido esperado de README.es.md a partir de las guías vivas."""
    # Hub con el banner insertado tras su primer separador `---`.
    hub_lines = HUB.read_text().split("\n")
    out, inserted = [], False
    for line in hub_lines:
        out.append(line)
        if not inserted and line.strip() == "---":
            out += ["", BANNER, "", "---"]
            inserted = True
    if not inserted:
        raise SystemExit("gen_readme_es: no encontré el primer '---' en el hub para anclar el banner")
    parts = ["\n".join(out)]
    parts += [p.read_text() for p in PARTS[1:]]
    # Un renglón en blanco entre archivos; una sola newline final.
    return "\n\n".join(p.rstrip("\n") for p in parts) + "\n"


def main() -> int:
    target = REPO / "README.es.md"
    expected = build_es()
    if "--check" in sys.argv:
        actual = target.read_text() if target.exists() else ""
        if actual != expected:
            print("❌ README.es.md desincronizado — corré: python3 tools/gen_readme_es.py")
            return 1
        print("✅ README.es.md en sync con las guías")
        return 0
    target.write_text(expected)
    print(f"✅ README.es.md regenerado ({len(expected.splitlines())} líneas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
