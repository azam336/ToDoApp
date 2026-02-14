# To-Do CLI

A single-user, console-based to-do manager built with Python 3.11+ and zero external dependencies.

## Quick start

```bash
# Add items
python -m src.todo add "Buy milk" --category Shopping
python -m src.todo add "Write report" --category Work
python -m src.todo add "Call dentist"

# List all items
python -m src.todo list

# Filter
python -m src.todo list --category Shopping
python -m src.todo list --done false
python -m src.todo list --search "milk"

# Update an item (use the UUID printed on add)
python -m src.todo update <id> --done true
python -m src.todo update <id> --title "Buy oat milk" --category Groceries

# Delete
python -m src.todo delete <id>

# Show categories with counts
python -m src.todo categories
```

## Persistence

Data is stored in `todo_data.json` in the working directory.
Override with the `TODO_DB` environment variable:

```bash
export TODO_DB=/path/to/my_todos.json
```

## Running tests

```bash
python -m unittest discover -s tests -v
```

## Project structure

```
src/
  models.py    – TodoItem dataclass
  storage.py   – JSON load/save with atomic writes
  cli.py       – argparse commands and handlers
  todo.py      – main entry-point
tests/
  test_todo.py – unittest suite (18 tests)
```

## SDD dev log

1. **Spec** – defined data model (uuid, title, category, done, timestamps), five CLI commands (add, update, delete, list, categories), persistence format (JSON), and constraints (stdlib only, exit codes).
2. **CLI design** – chose argparse subcommands; each handler receives a `db` path override for testability.
3. **Test plan** – wrote 18 unittest cases covering: model defaults and serialization round-trip, storage load/save/atomic-write, and every CLI command including error paths (missing id → exit code 1) and all three list filters (category, done, search).
4. **Implementation** – built `models.py` → `storage.py` → `cli.py` → `todo.py` in dependency order, running tests after each module.
5. **Verification** – all 18 tests pass; end-to-end smoke test confirms add → list → filter → categories pipeline works correctly.
