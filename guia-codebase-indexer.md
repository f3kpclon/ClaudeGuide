# codebase-indexer — El Mayordomo de tus Proyectos
*Haz que Claude sepa dónde está parado antes de que digas una sola palabra.*

**Autor:** Félix Sotelo
**Versión:** v1.0 · 2026-06-05

---

> Claude es inteligente. Pero sin contexto, es como contratar al mejor chef del mundo y no decirle qué hay en la cocina.
>
> `codebase-indexer` resuelve eso: cada vez que abres una sesión, Claude ya sabe qué stack usas, cómo se llaman tus módulos y qué archivos hay en cada carpeta. Sin que tengas que explicarlo.

---

## Por dónde empezar

1. **§1 — La analogía** → entiende el problema en 2 minutos
2. **§2 — Instalación** → un solo comando
3. **§3 — Cómo funciona** → el ciclo detect → cache → render
4. **§4 — El hook SessionStart** → automatización real
5. **§5 — Búsqueda cross-repo** → encuentra módulos en todos tus proyectos
6. **§6 — Filosofía LowCost** → por qué esto importa en tokens y dinero
7. **§7 — Referencia rápida** → comandos y flags

---

<!-- §1 -->
## §1 — La analogía: el mayordomo que llega antes que tú

Imagina que cada vez que entras a trabajar, un mayordomo ya puso sobre tu escritorio:
- Una nota que dice *"este proyecto es Swift, se llama BarcodeScanner"*
- Una lista de las habitaciones de la casa: *"scenes/, scripts/, tests/"*
- Los archivos más importantes de cada habitación: *"player_controller.gd, game_manager.gd..."*

Eso es exactamente lo que hace `codebase-indexer`. Antes de que Claude lea una sola línea de tu código, ya tiene ese resumen en contexto.

**Sin la herramienta:**
```
Tú: "oye, ¿puedo refactorizar el sistema de salud?"
Claude: "¿qué stack usas? ¿dónde está ese archivo? ¿tienes tests?"
→ 3-4 mensajes de ida y vuelta antes de empezar
```

**Con la herramienta:**
```
Tú: "oye, ¿puedo refactorizar el sistema de salud?"
Claude: "sí, está en scripts/health_component.gd, tienes test en tests/test_health_component.gd"
→ respuesta directa, cero setup
```

---

<!-- §2 -->
## §2 — Instalación

### Requisitos
- macOS con Homebrew
- Claude Code instalado

### Un solo comando

```bash
git clone https://github.com/f3kpclon/codebase-indexer
cd codebase-indexer
./install.sh
```

El script hace todo:
1. Instala `pipx` si no lo tienes (vía brew)
2. Instala `codebase-indexer` con su propio entorno aislado
3. Copia el hook a `~/.claude/hooks/inject-index.sh`
4. Agrega el hook a `~/.claude/settings.json` sin romper lo que ya tenías

### Verificar instalación

```bash
index --help
```

Si responde con la ayuda del CLI, está listo.

---

<!-- §3 -->
## §3 — Cómo funciona

### El ciclo completo

```
tu proyecto/
    ├── project.godot  ← manifiesto detectado
    ├── scripts/
    │   ├── player_controller.gd
    │   └── game_manager.gd
    └── scenes/
        └── Player.tscn
         ↓
    detect()  → stack: godot, module: First_test_game
    cache()   → ¿cambió algo? no → skip
    render()  → escribe .claude/index/INDEX.md
```

### El INDEX.md resultante

```markdown
# Codebase Index
Generated: 2026-06-05T03:10:10Z

## Stack
- godot

## Modules
- First_test_game

## Manifests
- project.godot

## Structure
- scripts/  (28 files)
  - player_controller.gd, game_manager.gd, health_component.gd ...
- scenes/  (17 files)
  - Player.tscn, GameOver.tscn, HUD.tscn ...
```

Claude lee este archivo al inicio de cada sesión. Es su mapa del territorio.

### Stacks soportados

| Manifiesto | Stack detectado |
|---|---|
| `pyproject.toml`, `setup.py`, `requirements.txt` | Python |
| `go.mod` | Go |
| `Package.swift` | Swift (SPM) |
| `*.xcodeproj`, `*.xcworkspace` | Swift (Xcode) |
| `Cargo.toml` | Rust |
| `package.json` | Node |
| `project.godot` | Godot |
| `Gemfile` | Ruby |
| `mix.exs` | Elixir |
| `Dockerfile` | Docker |

Si no hay ningún manifiesto conocido pero hay una carpeta `.claude/`, también indexa.

### El cache

La herramienta calcula un SHA256 del contenido de tus manifiestos. Si nada cambió desde la última vez, no regenera el INDEX.md. Cero trabajo innecesario.

Para forzar regeneración:

```bash
index index . --force
```

---

<!-- §4 -->
## §4 — El hook SessionStart: automatización real

El hook es la pieza que convierte la herramienta en algo invisible y automático.

### Cómo funciona

Cada vez que abres Claude Code en un proyecto, el hook corre `index index .` automáticamente. Si el proyecto cambió (nuevo manifiesto, contenido modificado), regenera el INDEX.md. Si no cambió, termina en milisegundos.

El hook activa si:
- Encuentra un manifiesto conocido (`Package.swift`, `go.mod`, `project.godot`, `*.xcodeproj`, etc.)
- O existe una carpeta `.claude/` en el directorio

```bash
# ~/.claude/hooks/inject-index.sh — se corre en cada SessionStart
```

### Verificar que el hook funciona

```bash
# 1. Modifica algo en el manifiesto del proyecto
echo "" >> ~/tu-proyecto/project.godot

# 2. Abre una nueva sesión de Claude Code ahí

# 3. Verifica el timestamp
stat ~/tu-proyecto/.claude/index/INDEX.md
```

Si el timestamp coincide con cuando abriste la sesión, el hook está funcionando.

### Correr manualmente

```bash
cd ~/tu-proyecto
bash ~/.claude/hooks/inject-index.sh
```

---

<!-- §5 -->
## §5 — Búsqueda cross-repo

`codebase-indexer` mantiene una base de datos SQLite con todos los proyectos que ha indexado. Puedes buscar módulos en todos ellos:

```bash
index search "player"
```

Responde:
```
/Users/felix/Desktop/first_test_game    First_test_game    godot
/Users/felix/work/unity-platformer      PlayerController   node
```

Útil cuando tienes muchos proyectos y no recuerdas en cuál implementaste algo.

### Opciones

```bash
index search "rails"          # busca en todos los repos indexados
index search "react" --db ~/custom.db   # base de datos personalizada
```

---

<!-- §6 -->
## §6 — Filosofía LowCost: por qué esto importa en tokens

Cada mensaje que Claude procesa tiene costo. El contexto que envías al inicio de la sesión se cobra. Pero es una inversión inteligente:

**Sin INDEX.md:**
- Claude pregunta el stack → 1 turno
- Claude pregunta dónde está X → 1 turno  
- Claude lee archivos para orientarse → 3-5 tool calls
- Total: ~5-8k tokens de orientación

**Con INDEX.md (≈1k tokens):**
- Claude ya sabe dónde está parado
- Empieza a trabajar desde el primer mensaje
- Total: 1k tokens fijos, cero turnos de orientación

El INDEX.md es como pagar una entrada barata para saltar la fila. El costo fijo de 1k tokens te ahorra 5-8k de navegación por sesión.

### Regla de oro

> Si Claude tiene que preguntarte "¿qué stack usas?" o "¿dónde está ese archivo?", el hook no está funcionando.

---

<!-- §7 -->
## §7 — Referencia rápida

### Comandos

```bash
# Indexar un proyecto
index index /ruta/al/proyecto

# Indexar y forzar regeneración aunque no haya cambios
index index /ruta/al/proyecto --force

# Indexar con output personalizado
index index /ruta/al/proyecto --output /ruta/INDEX.md

# Buscar módulos en todos los repos indexados
index search "query"

# Buscar con base de datos personalizada
index search "query" --db ~/.mi-base.db
```

### Rutas por defecto

| Cosa | Ruta |
|---|---|
| INDEX.md generado | `<proyecto>/.claude/index/INDEX.md` |
| Base de datos SQLite | `~/.codebase-indexer/index.db` |
| Cache | `<proyecto>/.codebase-indexer-cache.json` |
| Hook global | `~/.claude/hooks/inject-index.sh` |

### Archivos ignorados en el scanner

El scanner ignora automáticamente: `.git`, `.godot`, `.venv`, `node_modules`, `build`, `dist`, `vendor`, `target`, `__pycache__`, `.xcodeproj`, `.xcworkspace`, y carpetas ocultas.

### Reinstalar después de actualizar el repo

```bash
cd ~/Desktop/codebase-indexer
git pull
pipx install . --force
```
