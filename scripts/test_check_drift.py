#!/usr/bin/env python3
"""Tests for the drift check. Run with: python3 scripts/test_check_drift.py"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_drift import find_drift, load_config, render_comment  # noqa: E402

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".docsdrift.yml"
)


class TestDriftDetection(unittest.TestCase):
    def setUp(self):
        self.config = load_config(CONFIG_PATH)

    def test_config_loads_rules(self):
        self.assertTrue(self.config.get("rules"))
        self.assertIn("name", self.config["rules"][0])

    def test_code_change_without_docs_is_flagged(self):
        findings = find_drift(["src/api/users.py"], self.config)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["name"], "Public API reference")

    def test_code_and_docs_together_is_clean(self):
        findings = find_drift(
            ["src/api/users.py", "docs/api/users.md"], self.config
        )
        self.assertEqual(findings, [])

    def test_unrelated_change_is_clean(self):
        findings = find_drift(["tests/test_users.py"], self.config)
        self.assertEqual(findings, [])

    def test_multiple_rules_can_drift_at_once(self):
        findings = find_drift(["src/api/users.py", "Dockerfile"], self.config)
        self.assertEqual(len(findings), 2)

    def test_clean_comment_wording(self):
        self.assertIn("No drift found", render_comment([]))

    def test_drift_comment_lists_the_file(self):
        findings = find_drift(["src/api/users.py"], self.config)
        comment = render_comment(findings)
        self.assertIn("src/api/users.py", comment)
        self.assertIn("docs-drift-ok", comment)


if __name__ == "__main__":
    unittest.main(verbosity=2)
