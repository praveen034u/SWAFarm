"""Unit tests for the project-local KiCad MCP server."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import server


class OutputPathTests(unittest.TestCase):
    def test_output_directory_stays_in_mcp_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir).resolve()
            with patch.object(server, "PROJECT_DIR", project):
                result = server._output_dir("documentation")
                self.assertEqual(result, project / "mcp-output" / "documentation")

    def test_parent_traversal_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            server._output_dir("../outside")

    def test_absolute_path_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            server._output_dir(str(Path("C:/outside")))


class ReportSummaryTests(unittest.TestCase):
    def test_drc_report_is_counted_and_truncated(self) -> None:
        report = {
            "source": "board.kicad_pcb",
            "violations": [
                {"severity": "error", "type": "clearance"},
                {"severity": "warning", "type": "clearance"},
            ],
            "unconnected_items": [{"severity": "error", "type": "unconnected_items"}],
            "schematic_parity": [],
        }
        summary = server._summarize_report(report, max_issues=2)
        self.assertEqual(summary["total_issues"], 3)
        self.assertEqual(summary["returned_issues"], 2)
        self.assertTrue(summary["truncated"])
        self.assertEqual(summary["counts_by_severity"], {"error": 2, "warning": 1})


if __name__ == "__main__":
    unittest.main()
