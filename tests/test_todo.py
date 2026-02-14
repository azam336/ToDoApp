"""Unit tests for the to-do app (models, storage, cli)."""

import json
import os
import tempfile
import unittest
from pathlib import Path

from src.models import TodoItem
from src.storage import load_items, save_items
from src.cli import main


class TestTodoItem(unittest.TestCase):
    """Tests for the TodoItem dataclass."""

    def test_defaults(self):
        item = TodoItem(title="Test")
        self.assertEqual(item.title, "Test")
        self.assertEqual(item.category, "General")
        self.assertFalse(item.done)
        self.assertTrue(len(item.id) == 36)  # uuid4 string length
        self.assertIn("T", item.created_at)   # ISO8601 contains T

    def test_roundtrip_dict(self):
        item = TodoItem(title="RT", category="Work")
        d = item.to_dict()
        restored = TodoItem.from_dict(d)
        self.assertEqual(item.id, restored.id)
        self.assertEqual(item.title, restored.title)
        self.assertEqual(item.category, restored.category)

    def test_touch_updates_timestamp(self):
        item = TodoItem(title="T")
        old = item.updated_at
        import time
        time.sleep(0.01)
        item.touch()
        self.assertNotEqual(old, item.updated_at)


class TestStorage(unittest.TestCase):
    """Tests for JSON load/save."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix=".json", mode="w", encoding="utf-8"
        )
        self.tmp.close()
        self.path = Path(self.tmp.name)

    def tearDown(self):
        if self.path.exists():
            self.path.unlink()

    def test_load_empty_file_path(self):
        # Non-existent file returns empty list.
        self.path.unlink()
        items = load_items(self.path)
        self.assertEqual(items, [])

    def test_save_and_load(self):
        items = [TodoItem(title="A"), TodoItem(title="B", category="Work")]
        save_items(items, self.path)
        loaded = load_items(self.path)
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0].title, "A")
        self.assertEqual(loaded[1].category, "Work")

    def test_atomic_write_valid_json(self):
        save_items([TodoItem(title="X")], self.path)
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)


class TestCLIAdd(unittest.TestCase):
    """Tests for the 'add' command."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix=".json", mode="w", encoding="utf-8"
        )
        self.tmp.close()
        self.db = Path(self.tmp.name)
        # Start with empty list.
        with open(self.db, "w", encoding="utf-8") as f:
            json.dump([], f)

    def tearDown(self):
        if self.db.exists():
            self.db.unlink()

    def test_add_default_category(self):
        rc = main(["add", "Buy milk"], db=self.db)
        self.assertEqual(rc, 0)
        items = load_items(self.db)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "Buy milk")
        self.assertEqual(items[0].category, "General")

    def test_add_with_category(self):
        main(["add", "Sprint review", "--category", "Work"], db=self.db)
        items = load_items(self.db)
        self.assertEqual(items[0].category, "Work")


class TestCLIUpdate(unittest.TestCase):
    """Tests for the 'update' command."""

    def setUp(self):
        self.db = Path(tempfile.mktemp(suffix=".json"))
        self.item = TodoItem(title="Old title", category="General")
        save_items([self.item], self.db)

    def tearDown(self):
        if self.db.exists():
            self.db.unlink()

    def test_update_title(self):
        rc = main(["update", self.item.id, "--title", "New title"], db=self.db)
        self.assertEqual(rc, 0)
        items = load_items(self.db)
        self.assertEqual(items[0].title, "New title")

    def test_update_done(self):
        main(["update", self.item.id, "--done", "true"], db=self.db)
        items = load_items(self.db)
        self.assertTrue(items[0].done)

    def test_update_missing_id(self):
        rc = main(["update", "nonexistent-id", "--title", "X"], db=self.db)
        self.assertEqual(rc, 1)


class TestCLIDelete(unittest.TestCase):
    """Tests for the 'delete' command."""

    def setUp(self):
        self.db = Path(tempfile.mktemp(suffix=".json"))
        self.item = TodoItem(title="Delete me")
        save_items([self.item], self.db)

    def tearDown(self):
        if self.db.exists():
            self.db.unlink()

    def test_delete_existing(self):
        rc = main(["delete", self.item.id], db=self.db)
        self.assertEqual(rc, 0)
        self.assertEqual(load_items(self.db), [])

    def test_delete_missing(self):
        rc = main(["delete", "bad-id"], db=self.db)
        self.assertEqual(rc, 1)


class TestCLIList(unittest.TestCase):
    """Tests for the 'list' command with filters."""

    def setUp(self):
        self.db = Path(tempfile.mktemp(suffix=".json"))
        items = [
            TodoItem(title="Buy milk", category="Shopping", done=False),
            TodoItem(title="Write report", category="Work", done=True),
            TodoItem(title="Buy eggs", category="Shopping", done=False),
        ]
        save_items(items, self.db)

    def tearDown(self):
        if self.db.exists():
            self.db.unlink()

    def test_list_all(self):
        rc = main(["list"], db=self.db)
        self.assertEqual(rc, 0)

    def test_list_filter_category(self):
        # Should not error; output tested implicitly.
        rc = main(["list", "--category", "Shopping"], db=self.db)
        self.assertEqual(rc, 0)

    def test_list_filter_done(self):
        rc = main(["list", "--done", "true"], db=self.db)
        self.assertEqual(rc, 0)

    def test_list_search(self):
        rc = main(["list", "--search", "buy"], db=self.db)
        self.assertEqual(rc, 0)


class TestCLICategories(unittest.TestCase):
    """Tests for the 'categories' command."""

    def setUp(self):
        self.db = Path(tempfile.mktemp(suffix=".json"))
        items = [
            TodoItem(title="A", category="Work"),
            TodoItem(title="B", category="Work"),
            TodoItem(title="C", category="Home"),
        ]
        save_items(items, self.db)

    def tearDown(self):
        if self.db.exists():
            self.db.unlink()

    def test_categories(self):
        rc = main(["categories"], db=self.db)
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
