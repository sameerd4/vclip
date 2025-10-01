from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from .config import ProjectPaths


@dataclass(frozen=True)
class GalleryEntry:
    orientation: str
    path: str
    source: str
    lut: str


def build_manifest(paths: ProjectPaths) -> dict:
    entries = list(_collect_entries(paths))
    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "landscape": [asdict(e) for e in entries if e.orientation == "landscape"],
        "vertical": [asdict(e) for e in entries if e.orientation == "vertical"],
    }


def write_manifest(paths: ProjectPaths, manifest_path: Path | None = None) -> Path:
    manifest = build_manifest(paths)
    out_path = manifest_path or (paths.data / "gallery.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2))
    return out_path


def _collect_entries(paths: ProjectPaths) -> Iterable[GalleryEntry]:
    gallery_root = paths.gallery
    for orientation in ("landscape", "vertical"):
        base_dir = gallery_root / orientation
        if not base_dir.exists():
            continue
        for file in sorted(base_dir.glob("*.jpg")):
            source, lut = _parse_name(file.name)
            rel = Path("gallery") / orientation / file.name
            yield GalleryEntry(
                orientation=orientation,
                path=str(rel),
                source=source,
                lut=lut,
            )


def _parse_name(filename: str) -> tuple[str, str]:
    stem = Path(filename).stem
    if "__" in stem:
        src, lut = stem.split("__", 1)
    else:
        src, lut = stem, "default"
    lut = lut.replace("_", " ").title()
    return src, lut


__all__ = ["GalleryEntry", "build_manifest", "write_manifest"]
