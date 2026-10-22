#!/usr/bin/env python3
"""Pack an MCPB bundle (ZIP) honoring .mcpbignore.

The official @anthropic-ai/mcpb pack validates against the MCPB JSON schema,
which forbids extra properties on tools (additionalProperties=false excludes
inputSchema) - but Smithery REQUIRES inputSchema. The two are incompatible,
so use this custom packer.

Run from the server directory: python3 scripts/mcpb_pack.py
Output: server.mcpb in the same directory.
"""
import fnmatch
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "server.mcpb"
IGNORE_FILE = ROOT / ".mcpbignore"


def load_patterns() -> list[str]:
    if not IGNORE_FILE.exists():
        return []
    return [
        line.strip()
        for line in IGNORE_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def ignored(rel: str, patterns: list[str]) -> bool:
    parts = rel.split("/")
    for i in range(len(parts)):
        prefix = "/".join(parts[: i + 1])
        for pat in patterns:
            p = pat.rstrip("/")
            if fnmatch.fnmatch(prefix, p) or prefix == p:
                return True
            if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(rel, pat.lstrip("/") + "/*"):
                return True
    return False


def main() -> int:
    patterns = load_patterns()
    manifest_path = ROOT / "manifest.json"
    if not manifest_path.exists():
        print("ERROR: manifest.json missing", file=sys.stderr)
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for t in manifest.get("tools", []):
        if not isinstance(t.get("inputSchema"), dict):
            print(f"ERROR: tool {t.get('name')} has no inputSchema", file=sys.stderr)
            return 1
    files = []
    for f in sorted(ROOT.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(ROOT).as_posix()
        if rel == OUTPUT.name or ignored(rel, patterns):
            continue
        files.append((f, rel))
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f, rel in files:
            z.write(f, rel)
    print(f"packed {len(files)} files -> {OUTPUT} ({OUTPUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
