#!/usr/bin/env python3
"""
Mide el costo real de los archivos que entran en contexto — §2/§3.

Motivación: los presupuestos de §2 están en LÍNEAS, pero la densidad real varía
3-4× entre archivos, así que "< 200 líneas" significa cosas muy distintas según
cómo escribas. Este script mide, no estima.

Sin API key: líneas, chars y densidad (chars por línea no vacía).
Con API key: tokens reales vía count_tokens, en dos modelos a la vez para medir
             empíricamente el delta de tokenizer (§3 lo cita como ~1.3× desde la
             doc — acá se comprueba). count_tokens no se factura.

Uso:
    python3 tools/medir_contexto.py                # densidad, sin API
    ANTHROPIC_API_KEY=sk-... python3 tools/medir_contexto.py --tokens
"""
import argparse
import os
import statistics
import sys
from pathlib import Path

HOME = Path.home()
REPO = Path(__file__).resolve().parent.parent

# (etiqueta, path, presupuesto §2 en líneas o None)
def targets() -> list:
    out = []
    for label, p, budget in [
        ("CLAUDE.md global",       HOME / ".claude/CLAUDE.md", 30),
        ("CLAUDE.md proyecto",     REPO / "CLAUDE.md", 30),
        ("CLAUDE.local.md",        REPO / "CLAUDE.local.md", 30),
        ("scope-index.md",         REPO / ".claude/scope/scope-index.md", 20),
    ]:
        if p.exists():
            out.append((label, p, budget))
    for d in ("skills/*/SKILL.md", "agents/*.md", "rules/*.md"):
        for p in sorted((HOME / ".claude").glob(d)) + sorted((REPO / ".claude").glob(d)):
            kind = d.split("/")[0]
            budget = {"skills": 200, "agents": 60, "rules": 150}[kind]
            out.append((f"{kind[:-1]}: {p.parent.name if kind == 'skills' else p.stem}", p, budget))
    return out


def measure(paths, models):
    client = None
    if models:
        try:
            import anthropic
            client = anthropic.Anthropic()
        except Exception as e:
            print(f"⚠️  sin cliente API ({e}) — solo densidad\n", file=sys.stderr)
            models = []

    rows = []
    for label, p, budget in paths:
        text = p.read_text()
        lines = text.splitlines()
        ne = [l for l in lines if l.strip()] or [""]
        row = {"label": label, "lines": len(lines), "chars": len(text),
               "dens": len(text) / len(ne), "budget": budget, "tok": {}}
        for m in models:
            try:
                r = client.messages.count_tokens(
                    model=m, messages=[{"role": "user", "content": text}])
                row["tok"][m] = r.input_tokens
            except Exception as e:
                row["tok"][m] = None
                print(f"⚠️  {label} / {m}: {e}", file=sys.stderr)
        rows.append(row)
    return rows, models


def report(rows, models):
    head = f"{'archivo':<30}{'líneas':>7}{'chars':>7}{'c/lín':>7}"
    for m in models:
        head += f"{m.replace('claude-', ''):>16}"
    head += f"{'  §2':>6}"
    print(head)
    print("-" * len(head))
    for r in rows:
        line = f"{r['label']:<30}{r['lines']:>7}{r['chars']:>7}{r['dens']:>7.1f}"
        for m in models:
            t = r["tok"].get(m)
            line += f"{(t if t is not None else '—'):>16}"
        over = r["budget"] and r["lines"] > r["budget"]
        line += f"{('  ❌' if over else '  ok'):>6}"
        if over:
            line += f" (>{r['budget']})"
        print(line)

    dens = [r["dens"] for r in rows]
    print("-" * len(head))
    print(f"densidad: mediana {statistics.median(dens):.1f} · min {min(dens):.1f} · "
          f"max {max(dens):.1f} · dispersión {max(dens)/min(dens):.1f}×")

    if len(models) == 2:
        a, b = models
        ratios = [r["tok"][b] / r["tok"][a] for r in rows
                  if r["tok"].get(a) and r["tok"].get(b)]
        if ratios:
            print(f"tokenizer {b} / {a}: mediana {statistics.median(ratios):.3f}× "
                  f"(min {min(ratios):.3f} · max {max(ratios):.3f}) — n={len(ratios)}")
    if models:
        m0 = models[0]
        cpt = [r["chars"] / r["tok"][m0] for r in rows if r["tok"].get(m0)]
        if cpt:
            print(f"chars por token en {m0}: mediana {statistics.median(cpt):.2f} "
                  f"→ para estimar sin API: tokens ≈ chars / {statistics.median(cpt):.1f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokens", action="store_true",
                    help="contar tokens reales vía count_tokens (necesita credencial)")
    ap.add_argument("--models", default="claude-haiku-4-5,claude-sonnet-5",
                    help="modelos a comparar (el 1º es la referencia)")
    args = ap.parse_args()
    models = [m.strip() for m in args.models.split(",")] if args.tokens else []
    if args.tokens and not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")):
        print("⚠️  --tokens sin ANTHROPIC_API_KEY: probando el resolver del SDK igual\n",
              file=sys.stderr)
    rows, models = measure(targets(), models)
    report(rows, models)


if __name__ == "__main__":
    main()
