#!/usr/bin/env python3
"""Extract RAR archives discovered inside the supplied asset packs and inventory them."""
from pathlib import Path
import json, subprocess

base = Path("asset-audit/nested")
out = Path("asset-audit/rar-extracted")
out.mkdir(parents=True, exist_ok=True)
rows = []
archives = sorted(base.rglob("*.rar"))
for archive in archives:
    rel = archive.relative_to(base)
    dest = out / rel.parent / archive.stem
    dest.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(["unar", "-f", "-o", str(dest), str(archive)],
                          text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    rows.append({"archive": str(rel), "destination": str(dest),
                 "returncode": proc.returncode, "log": proc.stdout[-6000:]})
    for file in sorted(dest.rglob("*")):
        if file.is_file():
            rows.append({"archive": str(rel), "file": str(file.relative_to(dest)),
                         "size": file.stat().st_size, "output": str(file)})
Path("asset-audit/rar_inventory.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
lines = ["# Inventário dos arquivos RAR", ""]
for row in rows:
    if "returncode" in row:
        lines += [f"## {row['archive']}", f"- Código de saída: {row['returncode']}", f"- Destino: {row['destination']}", ""]
    else:
        lines.append(f"- {row['archive']} :: {row['file']} ({row['size']} bytes)")
Path("asset-audit/RAR_ASSETS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"RAR archives: {len(archives)}; extracted files: {sum('file' in x for x in rows)}")
if any(x.get("returncode", 0) != 0 for x in rows if "returncode" in x):
    raise SystemExit("One or more RAR archives could not be extracted")
