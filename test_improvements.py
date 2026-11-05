import tempfile
import unittest
from pathlib import Path
from reset_demo import build_demo
from database import get_all_customers


class DemoTests(unittest.TestCase):
    def test_demo_creation_and_overwrite_refusal(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'demo.db'
            build_demo(target)
            self.assertEqual(len(get_all_customers(target)), 40)
            before = target.read_bytes()
            with self.assertRaises(FileExistsError):
                build_demo(target)
            self.assertEqual(target.read_bytes(), before)

