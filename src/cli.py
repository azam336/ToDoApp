"""Argparse CLI definition and command handlers."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.models import TodoItem
from src.storage import load_items, save_items


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_item(items: list[TodoItem], item_id: str) -> TodoItem | None:
    for item in items:
        if item.id == item_id:
            return item
    return None


def _print_table(items: list[TodoItem]) -> None:
    """Print items as an aligned plain-text table."""
    if not items:
        print("No items found.")
        return

    headers = ["ID", "Title", "Category", "Done", "Created", "Updated"]
    rows: list[list[str]] = []
    for it in items:
        rows.append([
            it.id[:8],
            it.title,
            it.category,
            "Yes" if it.done else "No",
            it.created_at[:19],
            it.updated_at[:19],
        ])

    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in widths]))
    for row in rows:
        print(fmt.format(*row))


def _parse_bool(value: str) -> bool:
    if value.lower() in ("true", "1", "yes"):
        return True
    if value.lower() in ("false", "0", "no"):
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {value!r}")


# ---------------------------------------------------------------------------
# Command handlers — each returns an exit code (0 = success).
# ---------------------------------------------------------------------------

def cmd_add(args: argparse.Namespace, db: Path | None = None) -> int:
    items = load_items(db)
    item = TodoItem(title=args.title, category=args.category)
    items.append(item)
    save_items(items, db)
    print(f"Added: {item.id}")
    return 0


def cmd_update(args: argparse.Namespace, db: Path | None = None) -> int:
    items = load_items(db)
    item = _find_item(items, args.id)
    if item is None:
        print(f"Error: item {args.id!r} not found.", file=sys.stderr)
        return 1

    changed = False
    if args.title is not None:
        item.title = args.title
        changed = True
    if args.category is not None:
        item.category = args.category
        changed = True
    if args.done is not None:
        item.done = args.done
        changed = True

    if changed:
        item.touch()
        save_items(items, db)
        print(f"Updated: {item.id}")
    else:
        print("Nothing to update.")
    return 0


def cmd_delete(args: argparse.Namespace, db: Path | None = None) -> int:
    items = load_items(db)
    original_len = len(items)
    items = [it for it in items if it.id != args.id]
    if len(items) == original_len:
        print(f"Error: item {args.id!r} not found.", file=sys.stderr)
        return 1
    save_items(items, db)
    print(f"Deleted: {args.id}")
    return 0


def cmd_list(args: argparse.Namespace, db: Path | None = None) -> int:
    items = load_items(db)

    if args.category:
        items = [it for it in items if it.category.lower() == args.category.lower()]
    if args.done is not None:
        items = [it for it in items if it.done == args.done]
    if args.search:
        term = args.search.lower()
        items = [it for it in items if term in it.title.lower()]

    _print_table(items)
    return 0


def cmd_categories(args: argparse.Namespace, db: Path | None = None) -> int:
    items = load_items(db)
    counts: dict[str, int] = {}
    for it in items:
        counts[it.category] = counts.get(it.category, 0) + 1

    if not counts:
        print("No categories (no items).")
        return 0

    max_name = max(len(c) for c in counts)
    for cat in sorted(counts):
        print(f"  {cat:<{max_name}}  {counts[cat]}")
    return 0


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo",
        description="A simple console-based to-do manager.",
    )
    sub = parser.add_subparsers(dest="command")

    # add
    p_add = sub.add_parser("add", help="Add a new to-do item")
    p_add.add_argument("title", help="Title of the item")
    p_add.add_argument("--category", default="General", help="Category (default: General)")

    # update
    p_upd = sub.add_parser("update", help="Update an existing item")
    p_upd.add_argument("id", help="Item UUID")
    p_upd.add_argument("--title", default=None, help="New title")
    p_upd.add_argument("--category", default=None, help="New category")
    p_upd.add_argument("--done", type=_parse_bool, default=None, help="Mark done (true/false)")

    # delete
    p_del = sub.add_parser("delete", help="Delete an item by id")
    p_del.add_argument("id", help="Item UUID")

    # list
    p_ls = sub.add_parser("list", help="List items with optional filters")
    p_ls.add_argument("--category", default=None, help="Filter by category")
    p_ls.add_argument("--done", type=_parse_bool, default=None, help="Filter by done status")
    p_ls.add_argument("--search", default=None, help="Case-insensitive substring search in title")

    # categories
    sub.add_parser("categories", help="List all categories with item counts")

    return parser


def main(argv: list[str] | None = None, db: Path | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    dispatch = {
        "add": cmd_add,
        "update": cmd_update,
        "delete": cmd_delete,
        "list": cmd_list,
        "categories": cmd_categories,
    }
    return dispatch[args.command](args, db)
