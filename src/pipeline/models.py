from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from .exif import extract_camera_model, extract_orientation

_MODEL_MAP = {
    "FC9313": "DJI Mini 5 Pro",
}


@dataclass(frozen=True)
class LutProfile:
    """Metadata for a LUT file."""

    name: str
    path: Path


@dataclass(frozen=True)
class PhotoAsset:
    """Represents a source photo staged for grading."""

    path: Path

    def dimensions(self) -> Optional[Tuple[int, int]]:
        try:
            dims = _read_dimensions(self.path)
        except Exception:
            return None
        orientation = None
        try:
            orientation = extract_orientation(self.path)
        except Exception:
            orientation = None
        if orientation in {5, 6, 7, 8}:
            width, height = dims
            return height, width
        return dims

    def is_vertical(self) -> bool:
        dims = self.dimensions()
        if not dims:
            return False
        width, height = dims
        return height >= width

    def device_model(self) -> Optional[str]:
        info = self.device_summary()
        return info[1] if info else None

    def device_name(self) -> Optional[str]:
        info = self.device_summary()
        return info[0] if info else None

    def device_summary(self) -> Optional[Tuple[str, str]]:
        try:
            raw = extract_camera_model(self.path)
        except Exception:
            return None
        if not raw:
            return None
        friendly = _MODEL_MAP.get(raw, raw)
        return friendly, raw


def _read_dimensions(path: Path) -> Tuple[int, int]:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return _read_jpeg_dimensions(path)
    if suffix == ".png":
        return _read_png_dimensions(path)
    raise ValueError(f"unsupported image format: {suffix}")


def _read_jpeg_dimensions(path: Path) -> Tuple[int, int]:
    with path.open("rb") as fh:
        if fh.read(2) != b"\xFF\xD8":
            raise ValueError("not a JPEG file")
        while True:
            marker_start = fh.read(1)
            if not marker_start:
                break
            if marker_start != b"\xFF":
                continue
            marker = fh.read(1)
            if not marker:
                break
            if marker[0] in (0xD8, 0xD9):
                continue
            if 0xD0 <= marker[0] <= 0xD7:
                continue
            length_bytes = fh.read(2)
            if len(length_bytes) != 2:
                break
            segment_length = int.from_bytes(length_bytes, "big")
            if marker[0] in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                data = fh.read(segment_length - 2)
                if len(data) != segment_length - 2:
                    break
                height = int.from_bytes(data[1:3], "big")
                width = int.from_bytes(data[3:5], "big")
                return width, height
            fh.seek(segment_length - 2, 1)
    raise ValueError("could not determine JPEG dimensions")


def _read_png_dimensions(path: Path) -> Tuple[int, int]:
    with path.open("rb") as fh:
        sig = fh.read(8)
        if sig != b"\x89PNG\r\n\x1a\n":
            raise ValueError("not a PNG file")
        length = int.from_bytes(fh.read(4), "big")
        chunk_type = fh.read(4)
        if chunk_type != b"IHDR" or length != 13:
            raise ValueError("invalid PNG IHDR chunk")
        width = int.from_bytes(fh.read(4), "big")
        height = int.from_bytes(fh.read(4), "big")
        return width, height


__all__ = ["LutProfile", "PhotoAsset"]
