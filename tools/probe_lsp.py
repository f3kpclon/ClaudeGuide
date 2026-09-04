#!/usr/bin/env python3
"""
probe_lsp.py — ¿los language servers configurados están vivos? (§36)

Un LSP muerto no falla: contesta vacío. `findReferences` sobre un símbolo con
usos devuelve "No references found" cuando el binario no está, cuando el índice
no cargó, o cuando el servidor se cayó — la misma respuesta que un símbolo
realmente sin usos. Este script es el juez real (protocolo §7): habla LSP por
stdio directo en vez de inspeccionar config.

Modo default — inventario:
  1. Cruza los plugins habilitados (~/.claude/settings.json) con los lspServers
     declarados por cada marketplace / plugin.
  2. Por cada servidor: ¿el `command` existe en PATH?  (causa nº1 de "no hace nada")
  3. Lo arranca y completa el handshake `initialize` → capabilities REALES.
  4. Avisa colisiones de extensión (arranca solo el primero registrado).

Modo control positivo:
  probe_lsp.py --refs ARCHIVO:LINEA:COLUMNA
  Corre un textDocument/references de verdad. Si un símbolo que sabés que tiene
  usos devuelve 0, el servidor no está listo — no es que no haya usos.

Exit 0 = todos los servidores configurados respondieron. 1 = alguno está muerto.
Sin dependencias: stdlib only.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

CLAUDE = Path.home() / ".claude"
TIMEOUT = 30.0  # s — jdtls/kotlin declaran startupTimeout de 120s; acá solo medimos vida


# ---------------------------------------------------------------- descubrimiento

def enabled_plugins() -> set[str]:
    """Nombres de plugin habilitados en settings.json (claves 'plugin@marketplace')."""
    out = set()
    for name in ("settings.json", "settings.local.json"):
        f = CLAUDE / name
        if not f.exists():
            continue
        try:
            data = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        for key, on in (data.get("enabledPlugins") or {}).items():
            if on:
                out.add(key.split("@")[0])
    return out


def discover_servers() -> list[dict]:
    """[{plugin, name, cfg, source}] de los plugins habilitados."""
    on = enabled_plugins()
    found, seen = [], set()

    def add(plugin, name, cfg, source):
        if not isinstance(cfg, dict) or (plugin, name) in seen:
            return
        seen.add((plugin, name))
        found.append({"plugin": plugin, "name": name, "cfg": cfg, "source": source})

    for mk in (CLAUDE / "plugins" / "marketplaces").glob("*/.claude-plugin/marketplace.json"):
        try:
            data = json.loads(mk.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        for entry in data.get("plugins", []):
            plugin = entry.get("name")
            if plugin not in on:
                continue
            servers = entry.get("lspServers")
            if isinstance(servers, dict):
                for name, cfg in servers.items():
                    add(plugin, name, cfg, mk.name)

    # .lsp.json / plugin.json en el plugin instalado (la otra ubicación soportada)
    for root in list((CLAUDE / "plugins" / "marketplaces").glob("*/plugins/*")) + \
                list((CLAUDE / "plugins" / "cache").glob("*/*/*")):
        plugin = root.name if root.parent.name == "plugins" else root.parent.name
        if plugin not in on or not root.is_dir():
            continue
        lsp = root / ".lsp.json"
        if lsp.exists():
            try:
                for name, cfg in json.loads(lsp.read_text()).items():
                    add(plugin, name, cfg, ".lsp.json")
            except (json.JSONDecodeError, AttributeError, OSError):
                pass
        man = root / ".claude-plugin" / "plugin.json"
        if man.exists():
            try:
                servers = json.loads(man.read_text()).get("lspServers")
            except (json.JSONDecodeError, OSError):
                servers = None
            if isinstance(servers, dict):
                for name, cfg in servers.items():
                    add(plugin, name, cfg, "plugin.json")
    return found


# ---------------------------------------------------------------------- cliente

class Client:
    """JSON-RPC sobre stdio, framing Content-Length. Lo mínimo para preguntar si vive."""

    def __init__(self, cfg: dict, root: Path):
        env = dict(os.environ)
        env.update({k: str(v) for k, v in (cfg.get("env") or {}).items()})
        self.proc = subprocess.Popen(
            [cfg["command"], *(cfg.get("args") or [])],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            env=env, cwd=str(root),
        )
        self._id = 0
        self.root = root

    def _send(self, payload: dict):
        body = json.dumps(payload).encode()
        self.proc.stdin.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)
        self.proc.stdin.flush()

    def notify(self, method: str, params: dict):
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def _read_one(self):
        length = None
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise EOFError("el servidor cerró stdout")
            line = line.strip()
            if not line:
                break
            if line.lower().startswith(b"content-length:"):
                length = int(line.split(b":")[1])
        if length is None:
            raise ValueError("respuesta sin Content-Length (¿logs a stdout?)")
        return json.loads(self.proc.stdout.read(length))

    def request(self, method: str, params: dict, timeout=TIMEOUT):
        self._id += 1
        rid = self._id
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        box = {}

        def pump():
            try:
                while True:
                    msg = self._read_one()
                    if msg.get("id") == rid and ("result" in msg or "error" in msg):
                        box["msg"] = msg
                        return
                    # petición del servidor hacia nosotros: contestar para no bloquearlo
                    if "id" in msg and "method" in msg:
                        self._send({"jsonrpc": "2.0", "id": msg["id"], "result": None})
            except Exception as exc:  # noqa: BLE001 — el motivo se reporta, no se traga
                box["err"] = exc

        th = threading.Thread(target=pump, daemon=True)
        th.start()
        th.join(timeout)
        if "err" in box:
            raise box["err"]
        if "msg" not in box:
            raise TimeoutError(f"sin respuesta a {method} en {timeout:.0f}s")
        return box["msg"]

    def initialize(self):
        res = self.request("initialize", {
            "processId": os.getpid(),
            "rootUri": self.root.as_uri(),
            "workspaceFolders": [{"uri": self.root.as_uri(), "name": self.root.name}],
            "capabilities": {},
        })
        self.notify("initialized", {})
        return (res.get("result") or {}).get("capabilities") or {}

    def close(self):
        try:
            self.notify("exit", {})
            self.proc.wait(timeout=3)
        except Exception:  # noqa: BLE001 — cerrar nunca debe romper el reporte
            self.proc.kill()


CAPS = [("referencesProvider", "findReferences"),
        ("implementationProvider", "goToImplementation"),
        ("callHierarchyProvider", "incoming/outgoingCalls"),
        ("workspaceSymbolProvider", "workspaceSymbol"),
        ("documentSymbolProvider", "documentSymbol"),
        ("definitionProvider", "goToDefinition"),
        ("hoverProvider", "hover")]


# ------------------------------------------------------------------------ modos

def inventory(root: Path) -> int:
    servers = discover_servers()
    if not servers:
        print("Ningún lspServer declarado por los plugins habilitados.")
        print("→ Sin LSP, findReferences no existe: 'no hay usos' no se puede afirmar.")
        return 0

    by_ext: dict[str, str] = {}
    dead = 0
    for s in servers:
        cfg, label = s["cfg"], f"{s['plugin']}:{s['name']}"
        cmd = cfg.get("command")
        exts = list((cfg.get("extensionToLanguage") or {}).keys())
        print(f"\n▸ {label}  ({', '.join(exts) or 'sin extensiones'})  [{s['source']}]")

        if not cmd or not exts:
            print("  ✗ config inválida (falta command o extensionToLanguage) — se saltea entero")
            dead += 1
            continue

        path = shutil.which(cmd)
        if not path:
            print(f"  ✗ binario '{cmd}' NO está en PATH — el plugin no hace nada, y no avisa")
            dead += 1
            continue
        print(f"  · binario: {path}")

        try:
            cli = Client(cfg, root)
            caps = cli.initialize()
            ok = [n for k, n in CAPS if caps.get(k)]
            missing = [n for k, n in CAPS if not caps.get(k)]
            print(f"  ✓ responde initialize — anuncia: {', '.join(ok) or 'nada'}")
            if missing:
                print(f"    no anuncia: {', '.join(missing)}")
            cli.close()
        except Exception as exc:  # noqa: BLE001
            print(f"  ✗ arrancó pero no habla LSP: {type(exc).__name__}: {exc}")
            dead += 1
            continue

        for e in exts:
            if e in by_ext:
                print(f"  ! colisión en '{e}': la atiende {by_ext[e]} (primero registrado)")
            else:
                by_ext[e] = label

    print(f"\n{len(servers) - dead}/{len(servers)} servidores vivos.")
    if dead:
        print("Un servidor muerto devuelve vacío, no error: no le creas a un 0.")
    return 1 if dead else 0


def check_refs(target: str, root: Path, wait: float) -> int:
    try:
        raw, line, col = target.rsplit(":", 2)
        file, line, col = Path(raw).resolve(), int(line), int(col)
    except ValueError:
        print("Formato: --refs ARCHIVO:LINEA:COLUMNA (1-based, como el editor)")
        return 1
    if not file.exists():
        print(f"No existe: {file}")
        return 1

    ext = file.suffix
    match = next((s for s in discover_servers()
                  if ext in (s["cfg"].get("extensionToLanguage") or {})), None)
    if not match:
        print(f"Ningún servidor habilitado declara '{ext}'.")
        return 1
    cfg = match["cfg"]
    if not shutil.which(cfg.get("command") or ""):
        print(f"✗ binario '{cfg.get('command')}' no está en PATH.")
        return 1

    cli = Client(cfg, root)
    try:
        cli.initialize()
        uri = file.as_uri()
        cli.notify("textDocument/didOpen", {"textDocument": {
            "uri": uri,
            "languageId": cfg["extensionToLanguage"][ext],
            "version": 1,
            "text": file.read_text(),
        }})
        # El índice puede no estar listo al primer intento: se reintenta hasta el
        # deadline. Sin esto, "0 referencias" mide la impaciencia, no el código.
        started = time.monotonic()
        refs, waited = [], 0.0
        while True:
            res = cli.request("textDocument/references", {
                "textDocument": {"uri": uri},
                "position": {"line": line - 1, "character": col - 1},
                "context": {"includeDeclaration": True},
            })
            refs = res.get("result") or []
            waited = time.monotonic() - started
            if refs or waited >= wait:
                break
            time.sleep(1.0)

        tag = f" (tras {waited:.0f}s de indexado)" if refs and waited >= 1 else ""
        print(f"{match['plugin']}:{match['name']} → {len(refs)} referencia(s) en {file.name}:{line}:{col}{tag}")
        for r in refs:
            pos = r.get("range", {}).get("start", {})
            name = Path(r.get("uri", "")).name
            print(f"  {name}:{pos.get('line', 0) + 1}:{pos.get('character', 0) + 1}")
        if not refs:
            print(f"\n0 referencias tras {waited:.0f}s. Antes de concluir 'no tiene usos': repetí")
            print("sobre un símbolo con usos conocidos. Si ése también da 0, el índice no está")
            print("listo (en Swift: falta `swift build`; en Godot: falta el editor abierto).")
        return 0
    finally:
        cli.close()


def main() -> int:
    ap = argparse.ArgumentParser(description="¿Los language servers configurados están vivos? (§36)")
    ap.add_argument("--refs", metavar="ARCHIVO:LINEA:COL",
                    help="control positivo: referencias reales de un símbolo (1-based)")
    ap.add_argument("--root", default=".", help="raíz del workspace (default: cwd)")
    ap.add_argument("--wait", type=float, default=45.0, metavar="SEG",
                    help="con --refs: segundos a reintentar mientras el índice carga (default: 45)")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    return check_refs(args.refs, root, args.wait) if args.refs else inventory(root)


if __name__ == "__main__":
    sys.exit(main())
