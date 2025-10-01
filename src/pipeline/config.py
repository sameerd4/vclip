from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    """Resolved directories for the local grading workflow."""

    root: Path

    @property
    def luts(self) -> Path:
        return self.root / "src" / "luts"

    @property
    def inbox(self) -> Path:
        return self.root / "src" / "photos" / "inbox"

    @property
    def processed(self) -> Path:
        return self.root / "src" / "photos" / "processed"

    @property
    def gallery(self) -> Path:
        return self.root / "src" / "photos" / "gallery"

    @property
    def data(self) -> Path:
        return self.root / "src" / "data"

    @classmethod
    def from_env(cls, start: Path | None = None) -> "ProjectPaths":
        base = (start or Path.cwd()).resolve()
        return cls(root=base)

