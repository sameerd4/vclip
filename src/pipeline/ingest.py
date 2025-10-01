from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .models import PhotoAsset

_SUPPORTED_EXT = {".jpg", ".jpeg", ".png"}


def find_new_photos(folder: Path) -> Iterable[PhotoAsset]:
    """Return photos found in the inbox directory."""

    if not folder.exists():
        return []

    photos = []
    for p in sorted(folder.iterdir()):
        if p.suffix.lower() in _SUPPORTED_EXT:
            photos.append(PhotoAsset(path=p))
    return photos

