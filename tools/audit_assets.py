#!/usr/bin/env python3
"""Inventory and safely extract every ZIP asset in the repository and release."""
from __future__ import annotations
import argparse, collections, hashlib, json, os, stat, zipfile
from pathlib import Path, PurePosixPath

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def safe_extract(zf: zipfile.ZipFile, destination: Path, rows: list, archive_name: str):
    root = destination.resolve()
    for info in zf.infolist():
        raw = info.filename.replace("\\", "/")
        rel = PurePosixPath(raw)
        if rel.is_absolute() or any(p in ("..", "") for p in rel.parts):
            rows.append({"archive": archive_name, "path": raw, "status": "blocked_unsafe_path",
                         "size": info.file_size})
            continue
        target = (destination / Path(*rel.parts)).resolve()
        if target != root and root not in target.parents:
            rows.append({"archive": archive_name, "path": raw, "status": "blocked_path_escape",
                         "size": info.file_size})
            continue
        if info.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            rows.append({"archive": archive_name, "path": raw, "status": "directory", "size": 0})
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        mode = (info.external_attr >> 16) & 0xFFFF
        data = zf.read(info)
        if stat.S_ISLNK(mode):
            target = target.with_name(target.name + ".symlink-target.txt")
            status = "symlink_target_preserved_as_text"
        else:
            status = "extracted"
        with target.open("wb") as out:
            out.write(data)
        rows.append({"archive": archive_name, "path": raw, "output": str(target),
                     "status": status, "size": len(data),
                     "sha256": hashlib.sha256(data).hexdigest()})

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=".")
    ap.add_argument("--release-zip", default="")
    ap.add_argument("--output", default="asset-audit")
    args = ap.parse_args()
    source, output = Path(args.source), Path(args.output)
    extracted = output / "extracted"
    extracted.mkdir(parents=True, exist_ok=True)
    archives = sorted(p for p in source.glob("*.zip") if p.is_file())
    if args.release_zip:
        release = Path(args.release_zip)
        if release.is_file():
            archives.append(release)
    rows, archive_summary = [], []
    for archive in archives:
        try:
            with zipfile.ZipFile(archive) as zf:
                bad = zf.testzip()
                dest = extracted / archive.stem.replace("/", "_")
                dest.mkdir(parents=True, exist_ok=True)
                before = len(rows)
                safe_extract(zf, dest, rows, archive.name)
                archive_summary.append({
                    "archive": archive.name, "archive_bytes": archive.stat().st_size,
                    "entries": len(zf.infolist()), "bad_crc_entry": bad,
                    "extracted_entries": len(rows) - before,
                    "uncompressed_bytes": sum(i.file_size for i in zf.infolist() if not i.is_dir()),
                    "destination": str(dest)
                })
        except Exception as exc:
            archive_summary.append({"archive": archive.name, "error": repr(exc)})
    ext = collections.Counter()
    for row in rows:
        if row.get("status") in ("extracted", "symlink_target_preserved_as_text"):
            ext[Path(row["path"]).suffix.lower() or "[sem extensão]"] += 1
    report = {
        "archives": archive_summary,
        "entry_count": len(rows),
        "file_type_counts": dict(sorted(ext.items())),
        "entries": rows
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "asset_inventory.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Inventário integral dos pacotes ZIP", ""]
    for a in archive_summary:
        lines += [f"## {a['archive']}", f"- Entradas: {a.get('entries', 'ERRO')}",
                  f"- Bytes descompactados: {a.get('uncompressed_bytes', 'n/d')}",
                  f"- CRC inválido: {a.get('bad_crc_entry', 'n/d')}",
                  f"- Pasta: {a.get('destination', 'n/d')}", ""]
    lines += ["## Contagem por extensão", ""]
    lines += [f"- `{k}`: {v}" for k, v in sorted(ext.items())]
    lines += ["", "## Arquivos e pastas (caminhos originais)", ""]
    lines += [f"- [{r['status']}] `{r['archive']} :: {r['path']}` ({r.get('size', 0)} bytes)" for r in rows]
    (output / "ASSET_INVENTORY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"archives": archive_summary, "entry_count": len(rows), "file_type_counts": dict(ext)}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
