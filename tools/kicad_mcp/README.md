# SWAFarm KiCad MCP server

This project-local MCP server exposes safe KiCad 10 CLI operations to Codex.

Available tools:

- `project_info`: inspect the configured project and KiCad installation.
- `run_erc`: run schematic electrical-rules checking.
- `run_drc`: run PCB design-rules checking without changing the board.
- `export_documentation`: create a schematic PDF and CSV BOM.
- `export_manufacturing_files`: create Gerber and drill files.
- `export_step`: create a STEP model.

All generated files are restricted to `Hardware/SWAFarmNodeV1/mcp-output`.
The server does not modify `.kicad_pro`, `.kicad_sch`, or `.kicad_pcb` files.

## Manual launch

From the repository root:

```powershell
$env:KICAD_PROJECT_DIR = "C:\Project\SWAFarm\Hardware\SWAFarmNodeV1"
$env:KICAD_CLI = "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
python tools\kicad_mcp\server.py
```

The process uses MCP over standard input/output, so it normally appears to wait silently.
Codex launches and communicates with it automatically after registration.

## Codex registration

This workstation is registered globally under the name `kicad-swafarm`. Verify it with:

```powershell
codex mcp get kicad-swafarm
```

Restart the Codex desktop app or IDE extension after registration. In a new session, use
`/mcp` to confirm the server is active, then ask Codex to call `project_info`, `run_erc`,
or another listed tool.
