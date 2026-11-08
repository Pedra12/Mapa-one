#!/usr/bin/env python3
"""Inspect and extract ZIP files embedded inside already-extracted asset packs."""
from pathlib import Path, PurePosixPath
import json, zipfile

root = Path("asset-audit/extracted")
out = Path("asset-audit/nested")
out.mkdir(parents=True, exist_ok=True)
rows = []
for archive in sorted(root.rglob("*.zip")):
    rel = archive.relative_to(root)
    target = out / rel.parent / archive.stem
    target.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(archive) as zf:
            bad = zf.testzip()
            for info in zf.infolist():
                name = info.filename.replace("\\", "/")
                p = PurePosixPath(name)
                if p.is_absolute() or ".." in p.parts:
                    rows.append({"archive": str(rel), "path": name, "status": "blocked_unsafe_path"})
                    continue
                dest = target.joinpath(*p.parts)
                if info.is_dir():
                    dest.mkdir(parents=True, exist_ok=True)
                    continue
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(zf.read(info))
                rows.append({"archive": str(rel), "path": name, "size": info.file_size,
                             "output": str(dest), "status": "extracted"})
            rows.append({"archive": str(rel), "status": "archive_complete",
                         "entries": len(zf.infolist()), "bad_crc_entry": bad,
                         "output": str(target)})
    except Exception as e:
        rows.append({"archive": str(rel), "status": "error", "error": repr(e)})
Path("asset-audit/nested_inventory.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
lines = ["# Inventário dos ZIPs internos", ""]
for r in rows:
    if r["status"] == "archive_complete":
        lines.append(f"## {r['archive']}")
        lines.append(f"- Entradas: {r['entries']}; CRC inválido: {r['bad_crc_entry']}; destino: {r['output']}")
    elif r["status"] == "extracted":
        lines.append(f"- {r['archive']} :: {r['path']} ({r['size']} bytes)")
    else:
        lines.append(f"- **{r['status']}**: {r['archive']} :: {r.get('path', r.get('error', ''))}")
Path("asset-audit/NESTED_ASSETS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Nested archives: {sum(1 for x in rows if x['status']=='archive_complete')}; files: {sum(1 for x in rows if x['status']=='extracted')}")
