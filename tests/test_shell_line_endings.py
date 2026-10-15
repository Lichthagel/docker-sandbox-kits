from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ShellLineEndingTests(unittest.TestCase):
    def test_shell_files_use_lf_and_remain_lf_on_windows_checkout(self):
        files = subprocess.run(
            ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True
        ).stdout.decode().split("\0")
        for name in filter(None, files):
            path = ROOT / name
            content = path.read_bytes()
            if path.name != "bashrc" and path.suffix != ".sh" and not content.startswith(
                (b"#!/bin/bash", b"#!/bin/sh")
            ):
                continue
            with self.subTest(path=name):
                self.assertNotIn(b"\r", content, "shell files must not contain CRLF")
                attribute = subprocess.run(
                    ["git", "check-attr", "eol", "--", name], cwd=ROOT,
                    capture_output=True, check=True, text=True,
                ).stdout.strip()
                self.assertEqual(attribute, f"{name}: eol: lf")
