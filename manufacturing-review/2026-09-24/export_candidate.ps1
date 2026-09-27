$ErrorActionPreference = 'Stop'
$kicad = 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
$root = 'C:/Project/SWAFarm/manufacturing-review/2026-09-24'
$board = "$root/project/SWAFarmNodeV1.kicad_pcb"
$schematic = "$root/project/SWAFarmNodeV1.kicad_sch"
$out = "$root/release-candidate"
function Check-Exit { if ($LASTEXITCODE -ne 0) { throw "KiCad export/check failed: $LASTEXITCODE" } }
& $kicad sch erc --severity-all --exit-code-violations -o "$root/reports/erc-release.rpt" $schematic
Check-Exit
& $kicad pcb drc --refill-zones --save-board --schematic-parity --severity-all --exit-code-violations --format json -o "$root/reports/drc-final.json" $board
Check-Exit
& $kicad pcb drc --schematic-parity --severity-all --exit-code-violations -o "$root/reports/drc-release.rpt" $board
Check-Exit
& $kicad pcb export gerbers --check-zones --layers 'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.SilkS,B.SilkS,Edge.Cuts' -o "$out/fab/" $board
Check-Exit
& $kicad pcb export drill --format excellon --excellon-units mm --excellon-oval-format route --excellon-separate-th --generate-map --map-format gerberx2 --generate-report --report-path "$out/fab/drill-report.txt" -o "$out/fab/" $board
Check-Exit
& $kicad pcb export ipcd356 -o "$out/review/IPC356-native-unprocessed.ipc" $board
Check-Exit
& $kicad pcb export pos --format csv --units mm --side both -o "$out/assembly/CPL-KiCad.csv" $board
Check-Exit
& $kicad sch export bom --fields 'Reference,Value,Footprint,QUANTITY,Manufacturer,MPN,DNP,Datasheet' --labels 'References,Value,Footprint,QtyPerBoard,Manufacturer,MPN,DNP,Datasheet' --group-by 'Value,Footprint,MPN' -o "$out/assembly/BOM.csv" $schematic
Check-Exit
& $kicad pcb export svg --layers 'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.SilkS,B.SilkS,Edge.Cuts' --mode-multi --fit-page-to-board --exclude-drawing-sheet --check-zones -o "$out/review/layers/" $board
Check-Exit
& $kicad pcb export pdf --layers 'F.Fab,F.SilkS,Edge.Cuts' --black-and-white --scale 0 --mode-single --sketch-pads-on-fab-layers --exclude-value -o "$out/assembly/assembly-top.pdf" $board
Check-Exit
& $kicad pcb export pdf --layers 'B.Fab,B.SilkS,Edge.Cuts' --black-and-white --scale 0 --mirror --mode-single --sketch-pads-on-fab-layers --exclude-value -o "$out/assembly/assembly-bottom.pdf" $board
Check-Exit
& $kicad sch export pdf -o "$out/assembly/schematic.pdf" $schematic
Check-Exit
foreach ($side in @('top','bottom')) {
    & $kicad pcb render --side $side --width 1600 --height 1280 --quality basic --use-board-stackup-colors -o "$out/review/assembled-$side.png" $board
    Check-Exit
}
Copy-Item -LiteralPath "$root/reports/drc-final.json","$root/reports/drc-release.rpt","$root/reports/erc-release.rpt" -Destination "$out/review/" -Force
