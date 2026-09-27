"""Project-local MCP server for safe KiCad CLI automation."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROJECT_DIR = REPOSITORY_ROOT / "Hardware" / "SWAFarmNodeV1"
PROJECT_DIR = Path(os.environ.get("KICAD_PROJECT_DIR", DEFAULT_PROJECT_DIR)).resolve()
DEFAULT_KICAD_CLI = Path(r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe")
KICAD_CLI = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli") or str(DEFAULT_KICAD_CLI)
COMMAND_TIMEOUT_SECONDS = int(os.environ.get("KICAD_COMMAND_TIMEOUT_SECONDS", "180"))

READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)
WRITES_EXPORTS = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)

mcp = FastMCP(
    "SWAFarm KiCad",
    instructions=(
        "Tools operate only on the SWAFarmNodeV1 KiCad project. Prefer project_info before "
        "other calls. ERC and DRC are read-only. Export tools only create or replace files "
        "inside the project's mcp-output directory and never alter KiCad design sources."
    ),
)


def _ensure_ready() -> None:
    if not PROJECT_DIR.is_dir():
        raise RuntimeError(f"KiCad project directory does not exist: {PROJECT_DIR}")
    if not Path(KICAD_CLI).is_file():
        raise RuntimeError(f"kicad-cli executable does not exist: {KICAD_CLI}")


def _design_files() -> tuple[Path, Path, Path]:
    _ensure_ready()
    projects = sorted(PROJECT_DIR.glob("*.kicad_pro"))
    if not projects:
        raise RuntimeError(f"No .kicad_pro file found in {PROJECT_DIR}")

    project = projects[0]
    schematic = project.with_suffix(".kicad_sch")
    board = project.with_suffix(".kicad_pcb")
    missing = [str(path) for path in (schematic, board) if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing KiCad design files: {', '.join(missing)}")
    return project, schematic, board


def _run_kicad(args: list[str], timeout: int = COMMAND_TIMEOUT_SECONDS) -> dict[str, Any]:
    _ensure_ready()
    command = [KICAD_CLI, *args]
    try:
        completed = subprocess.run(
            command,
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"KiCad command timed out after {timeout} seconds") from exc

    return {
        "command": command,
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def _run_check(kind: str, source: Path, schematic_parity: bool = False) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"swafarm-kicad-{kind}-") as temp_dir:
        report_path = Path(temp_dir) / f"{kind}.json"
        args = [kind.split("_")[0], kind.split("_")[1], "--format", "json", "--severity-all"]
        if schematic_parity:
            args.append("--schematic-parity")
        args.extend(["--output", str(report_path), str(source)])
        result = _run_kicad(args)

        report: Any = None
        if report_path.is_file():
            report_text = report_path.read_text(encoding="utf-8", errors="replace")
            try:
                report = json.loads(report_text)
            except json.JSONDecodeError:
                report = report_text
        result["report"] = report

        if result["exit_code"] != 0 and report is None:
            raise RuntimeError(
                f"KiCad {kind} failed with exit code {result['exit_code']}: "
                f"{result['stderr'] or result['stdout']}"
            )
        return result


def _summarize_report(report: dict[str, Any], max_issues: int) -> dict[str, Any]:
    max_issues = max(1, min(max_issues, 200))
    issues: list[dict[str, Any]] = []

    if isinstance(report.get("sheets"), list):
        for sheet in report["sheets"]:
            for violation in sheet.get("violations", []):
                issues.append({"category": "erc", "sheet": sheet.get("path"), **violation})
    else:
        for category in ("violations", "unconnected_items", "schematic_parity"):
            for violation in report.get(category, []):
                issues.append({"category": category, **violation})

    by_severity: dict[str, int] = {}
    by_type: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for issue in issues:
        severity = str(issue.get("severity", "unknown"))
        issue_type = str(issue.get("type", "unknown"))
        category = str(issue.get("category", "unknown"))
        by_severity[severity] = by_severity.get(severity, 0) + 1
        by_type[issue_type] = by_type.get(issue_type, 0) + 1
        by_category[category] = by_category.get(category, 0) + 1

    metadata = {
        key: value
        for key, value in report.items()
        if key not in {"sheets", "violations", "unconnected_items", "schematic_parity"}
    }
    return {
        "metadata": metadata,
        "total_issues": len(issues),
        "returned_issues": min(len(issues), max_issues),
        "truncated": len(issues) > max_issues,
        "counts_by_severity": by_severity,
        "counts_by_category": by_category,
        "counts_by_type": dict(sorted(by_type.items(), key=lambda item: (-item[1], item[0]))),
        "issues": issues[:max_issues],
    }


def _output_dir(relative_subdir: str) -> Path:
    normalized = Path(relative_subdir)
    if normalized.is_absolute() or ".." in normalized.parts:
        raise ValueError("Output directory must be a relative path without '..'")

    output_root = (PROJECT_DIR / "mcp-output").resolve()
    candidate = (output_root / normalized).resolve()
    if candidate != output_root and output_root not in candidate.parents:
        raise ValueError("Output directory must remain inside the project's mcp-output directory")
    candidate.mkdir(parents=True, exist_ok=True)
    return candidate


def _generated_files(directory: Path) -> list[str]:
    return [
        str(path.relative_to(PROJECT_DIR))
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    ]


@mcp.tool(annotations=READ_ONLY)
def project_info() -> dict[str, Any]:
    """Return KiCad version, design paths, lock state, and available source files."""
    project, schematic, board = _design_files()
    version = _run_kicad(["--version"])
    locks = sorted(path.name for path in PROJECT_DIR.glob("~*.lck"))
    source_files = sorted(
        str(path.relative_to(PROJECT_DIR))
        for pattern in ("*.kicad_pro", "*.kicad_sch", "*.kicad_pcb")
        for path in PROJECT_DIR.glob(pattern)
    )
    return {
        "project_directory": str(PROJECT_DIR),
        "project": project.name,
        "root_schematic": schematic.name,
        "board": board.name,
        "kicad_cli": KICAD_CLI,
        "kicad_version": version["stdout"],
        "source_files": source_files,
        "lock_files": locks,
        "kicad_appears_open": bool(locks),
    }


@mcp.tool(annotations=READ_ONLY)
def run_erc(max_issues: int = 100) -> dict[str, Any]:
    """Run electrical-rules checking and return counts plus up to max_issues details."""
    _, schematic, _ = _design_files()
    result = _run_check("sch_erc", schematic)
    return {
        "exit_code": result["exit_code"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        **_summarize_report(result["report"], max_issues),
    }


@mcp.tool(annotations=READ_ONLY)
def run_drc(check_schematic_parity: bool = True, max_issues: int = 100) -> dict[str, Any]:
    """Run design-rules checking and return counts plus up to max_issues details."""
    _, _, board = _design_files()
    result = _run_check("pcb_drc", board, schematic_parity=check_schematic_parity)
    return {
        "exit_code": result["exit_code"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        **_summarize_report(result["report"], max_issues),
    }


@mcp.tool(annotations=WRITES_EXPORTS)
def export_documentation(output_subdir: str = "documentation") -> dict[str, Any]:
    """Export the schematic PDF and CSV BOM under mcp-output."""
    _, schematic, _ = _design_files()
    output_dir = _output_dir(output_subdir)
    pdf_path = output_dir / "SWAFarmNodeV1-schematic.pdf"
    bom_path = output_dir / "SWAFarmNodeV1-bom.csv"

    commands = [
        _run_kicad(["sch", "export", "pdf", "--output", str(pdf_path), str(schematic)]),
        _run_kicad(["sch", "export", "bom", "--output", str(bom_path), str(schematic)]),
    ]
    failures = [item for item in commands if item["exit_code"] != 0]
    if failures:
        raise RuntimeError(f"One or more documentation exports failed: {failures}")
    return {"output_directory": str(output_dir), "files": _generated_files(output_dir)}


@mcp.tool(annotations=WRITES_EXPORTS)
def export_manufacturing_files(output_subdir: str = "manufacturing") -> dict[str, Any]:
    """Export Gerbers and Excellon drill files under mcp-output using board plot settings."""
    _, _, board = _design_files()
    output_dir = _output_dir(output_subdir)
    commands = [
        _run_kicad(
            [
                "pcb",
                "export",
                "gerbers",
                "--board-plot-params",
                "--output",
                str(output_dir),
                str(board),
            ]
        ),
        _run_kicad(
            [
                "pcb",
                "export",
                "drill",
                "--generate-map",
                "--generate-report",
                "--output",
                str(output_dir),
                str(board),
            ]
        ),
    ]
    failures = [item for item in commands if item["exit_code"] != 0]
    if failures:
        raise RuntimeError(f"One or more manufacturing exports failed: {failures}")
    return {"output_directory": str(output_dir), "files": _generated_files(output_dir)}


@mcp.tool(annotations=WRITES_EXPORTS)
def export_step(output_subdir: str = "3d") -> dict[str, Any]:
    """Export a STEP model under mcp-output without changing the board."""
    _, _, board = _design_files()
    output_dir = _output_dir(output_subdir)
    step_path = output_dir / "SWAFarmNodeV1.step"
    result = _run_kicad(
        ["pcb", "export", "step", "--force", "--output", str(step_path), str(board)],
        timeout=max(COMMAND_TIMEOUT_SECONDS, 600),
    )
    if result["exit_code"] != 0:
        raise RuntimeError(f"STEP export failed: {result['stderr'] or result['stdout']}")
    return {"output_directory": str(output_dir), "files": _generated_files(output_dir)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
