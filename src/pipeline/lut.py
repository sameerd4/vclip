from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable

from .models import LutProfile


class LutLibrary:
    """Tracks available LUT files on disk."""

    def __init__(self, lut_dir: Path) -> None:
        self._lut_dir = lut_dir
        self._cache: Dict[str, LutProfile] = {}

    def refresh(self) -> None:
        self._cache.clear()
        for path in sorted(self._lut_dir.glob("*.cube")):
            name = path.stem
            self._cache[name] = LutProfile(name=name, path=path)

    def __contains__(self, key: str) -> bool:
        return key in self._cache

    def __getitem__(self, key: str) -> LutProfile:
        return self._cache[key]

    def profiles(self) -> Iterable[LutProfile]:
        return self._cache.values()

    def ensure(self) -> None:
        if not self._lut_dir.exists():
            self._lut_dir.mkdir(parents=True, exist_ok=True)

