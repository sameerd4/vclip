from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .config import ProjectPaths
from .models import LutProfile, PhotoAsset


@dataclass(frozen=True)
class GradeResult:
    processed_path: Path
    gallery_path: Path


class Grader:
    """Apply LUTs to staged photos using ffmpeg."""

    def __init__(
        self,
        paths: ProjectPaths,
        ffmpeg_bin: str | None = None,
        gallery_landscape_width: int = 2560,
        gallery_vertical_height: int = 2560,
    ) -> None:
        self._paths = paths
        self._ffmpeg = ffmpeg_bin or "ffmpeg"
        self._gallery_landscape_width = gallery_landscape_width
        self._gallery_vertical_height = gallery_vertical_height

    def apply(self, asset: PhotoAsset, lut: LutProfile, overwrite: bool = True) -> GradeResult:
        """Apply LUT to photo and write processed + gallery variants."""

        processed_dir = self._paths.processed / asset.path.stem
        processed_dir.mkdir(parents=True, exist_ok=True)

        lut_slug = _slugify(lut.name)
        src_suffix = asset.path.suffix.lower() or ".jpg"
        processed_name = f"{asset.path.stem}__{lut_slug}{src_suffix}"
        processed_path = processed_dir / processed_name

        gallery_dir = self._gallery_dir_for(asset)
        gallery_dir.mkdir(parents=True, exist_ok=True)
        gallery_name = f"{asset.path.stem}__{lut_slug}.jpg"
        gallery_path = gallery_dir / gallery_name

        if not overwrite and processed_path.exists():
            raise FileExistsError(processed_path)
        if not overwrite and gallery_path.exists():
            raise FileExistsError(gallery_path)

        self._run_ffmpeg(
            [
                "-y" if overwrite else "-n",
                "-i",
                str(asset.path),
                "-vf",
                self._build_processed_filter(lut.path),
                "-frames:v",
                "1",
                str(processed_path),
            ]
        )

        self._run_ffmpeg(
            [
                "-y" if overwrite else "-n",
                "-i",
                str(asset.path),
                "-vf",
                self._build_gallery_filter(asset, lut.path),
                "-frames:v",
                "1",
                str(gallery_path),
            ]
        )

        return GradeResult(processed_path=processed_path, gallery_path=gallery_path)

    def _run_ffmpeg(self, args: list[str]) -> None:
        cmd = [self._ffmpeg] + args
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            raise RuntimeError(
                f"ffmpeg failed (code {proc.returncode})\ncmd: {' '.join(cmd)}\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
            )

    def _build_processed_filter(self, lut_path: Path) -> str:
        return f"lut3d=file='{_escape_filter_path(lut_path)}'"

    def _build_gallery_filter(self, asset: PhotoAsset, lut_path: Path) -> str:
        base_filter = self._build_processed_filter(lut_path)
        if asset.is_vertical():
            scale = (
                "scale=-1:'if(gt(ih,{h}),{h},ih)':flags=lanczos".format(
                    h=self._gallery_vertical_height
                )
            )
        else:
            scale = (
                "scale='if(gt(iw,{w}),{w},iw)':-1:flags=lanczos".format(
                    w=self._gallery_landscape_width
                )
            )
        return f"{base_filter},{scale}"

    def _gallery_dir_for(self, asset: PhotoAsset) -> Path:
        sub = "vertical" if asset.is_vertical() else "landscape"
        return self._paths.gallery / sub


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug or "lut"


def _escape_filter_path(path: Path) -> str:
    text = str(path)
    text = text.replace("\\", "\\\\")
    text = text.replace("'", "\\'")
    return text


__all__ = ["Grader", "GradeResult"]
