from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Tuple

_TYPE_SIZES = {
    1: 1,  # BYTE
    2: 1,  # ASCII
    3: 2,  # SHORT
    4: 4,  # LONG
    5: 8,  # RATIONAL
    7: 1,  # UNDEFINED
}


@dataclass(frozen=True)
class GPSData:
    latitude: float
    longitude: float


class _ExifParser:
    def __init__(self, blob: bytes) -> None:
        self._blob = blob
        if len(blob) < 8:
            raise ValueError("invalid EXIF segment")
        endian = blob[0:2]
        if endian == b"II":
            self._endian = "<"
        elif endian == b"MM":
            self._endian = ">"
        else:
            raise ValueError("unknown TIFF endianness")

    def _u16(self, offset: int) -> int:
        from struct import unpack_from

        if offset + 2 > len(self._blob):
            raise ValueError("offset out of range")
        return unpack_from(self._endian + "H", self._blob, offset)[0]

    def _u32(self, offset: int) -> int:
        from struct import unpack_from

        if offset + 4 > len(self._blob):
            raise ValueError("offset out of range")
        return unpack_from(self._endian + "I", self._blob, offset)[0]

    def _read_ifd(self, offset: int) -> Tuple[dict[int, object], Optional[int]]:
        if offset >= len(self._blob):
            raise ValueError("IFD offset out of range")

        count = self._u16(offset)
        base = offset + 2
        entries: dict[int, object] = {}
        for idx in range(count):
            entry_offset = base + idx * 12
            if entry_offset + 12 > len(self._blob):
                break
            tag = self._u16(entry_offset)
            typ = self._u16(entry_offset + 2)
            item_count = self._u32(entry_offset + 4)
            raw_value = self._blob[entry_offset + 8 : entry_offset + 12]
            try:
                value = self._decode_value(typ, item_count, raw_value)
            except Exception:
                continue
            entries[tag] = value

        next_offset_pos = base + count * 12
        next_offset = None
        if next_offset_pos + 4 <= len(self._blob):
            ptr = self._u32(next_offset_pos)
            next_offset = ptr if ptr != 0 else None
        return entries, next_offset

    def _decode_value(self, typ: int, count: int, raw_value: bytes):
        size = _TYPE_SIZES.get(typ)
        if size is None:
            raise ValueError("unsupported type")
        total_size = size * max(count, 1)
        if total_size <= 4:
            data = raw_value[:total_size]
        else:
            value_offset = self._u32_from_bytes(raw_value)
            if value_offset + total_size > len(self._blob):
                raise ValueError("value offset out of range")
            data = self._blob[value_offset : value_offset + total_size]

        if typ == 2:  # ASCII
            return data.partition(b"\x00")[0].decode("ascii", errors="replace")
        if typ == 3:  # SHORT
            return self._decode_shorts(data, count)
        if typ == 4:  # LONG
            return self._decode_longs(data, count)
        if typ == 5:  # RATIONAL
            return self._decode_rationals(data, count)
        return data

    def _u32_from_bytes(self, raw: bytes) -> int:
        from struct import unpack

        padded = raw[:4] + b"\x00" * (4 - len(raw))
        return unpack(self._endian + "I", padded)[0]

    def _decode_shorts(self, data: bytes, count: int) -> Tuple[int, ...]:
        from struct import iter_unpack

        return tuple(v[0] for v in iter_unpack(self._endian + "H", data[: 2 * count]))

    def _decode_longs(self, data: bytes, count: int) -> Tuple[int, ...]:
        from struct import iter_unpack

        return tuple(v[0] for v in iter_unpack(self._endian + "I", data[: 4 * count]))

    def _decode_rationals(self, data: bytes, count: int) -> Tuple[Tuple[int, int], ...]:
        rationals = []
        for idx in range(count):
            start = idx * 8
            num = self._u32_from_bytes(data[start : start + 4])
            den = self._u32_from_bytes(data[start + 4 : start + 8])
            rationals.append((num, den))
        return tuple(rationals)

    def ifd0(self) -> dict[int, object]:
        first_ifd_offset = self._u32(4)
        entries, _ = self._read_ifd(first_ifd_offset)
        return entries

    def gps(self) -> Optional[GPSData]:
        ifd0 = self.ifd0()
        gps_pointer = ifd0.get(0x8825)
        if gps_pointer is None:
            return None
        if isinstance(gps_pointer, tuple):
            gps_offset = gps_pointer[0]
        elif isinstance(gps_pointer, int):
            gps_offset = gps_pointer
        else:
            return None

        gps_ifd, _ = self._read_ifd(gps_offset)
        lat_ref = gps_ifd.get(0x0001)
        lat_vals = gps_ifd.get(0x0002)
        lon_ref = gps_ifd.get(0x0003)
        lon_vals = gps_ifd.get(0x0004)
        if not (lat_ref and lat_vals and lon_ref and lon_vals):
            return None

        latitude = _rational_triplet_to_deg(lat_vals, lat_ref)
        longitude = _rational_triplet_to_deg(lon_vals, lon_ref)
        if latitude is None or longitude is None:
            return None
        return GPSData(latitude=latitude, longitude=longitude)

    def orientation(self) -> Optional[int]:
        value = self.ifd0().get(0x0112)
        if value is None:
            return None
        if isinstance(value, tuple):
            value = value[0] if value else None
        elif isinstance(value, bytes):
            value = value[0] if value else None
        if isinstance(value, int) and value != 0:
            return value
        return None

    def camera_model(self) -> Optional[str]:
        value = self.ifd0().get(0x0110)
        if value is None:
            return None
        if isinstance(value, bytes):
            value = value.decode("ascii", errors="replace").strip() or None
        elif isinstance(value, tuple):
            # Some encoders expose ASCII as tuple of ints
            try:
                value = bytes(value).decode("ascii", errors="replace").strip() or None
            except Exception:
                value = None
        elif isinstance(value, str):
            value = value.strip() or None
        else:
            value = None
        return value


def _rational_triplet_to_deg(values: Iterable[Tuple[int, int]], ref: str | Iterable) -> Optional[float]:
    try:
        ref_char = ref if isinstance(ref, str) else bytes(ref).decode("ascii", errors="replace")
    except Exception:
        return None

    rationals = list(values)
    if len(rationals) < 3:
        return None
    parts = []
    for num, den in rationals[:3]:
        if den == 0:
            return None
        parts.append(num / den)
    deg = parts[0] + parts[1] / 60.0 + parts[2] / 3600.0
    if ref_char.upper() in ("S", "W"):
        deg = -deg
    return deg


def extract_gps(path: Path) -> Optional[GPSData]:
    data = path.read_bytes()
    exif_segment = _find_exif_segment(data)
    if exif_segment is None:
        return None

    parser = _ExifParser(exif_segment)
    return parser.gps()


def extract_orientation(path: Path) -> Optional[int]:
    data = path.read_bytes()
    exif_segment = _find_exif_segment(data)
    if exif_segment is None:
        return None
    parser = _ExifParser(exif_segment)
    return parser.orientation()


def extract_camera_model(path: Path) -> Optional[str]:
    data = path.read_bytes()
    exif_segment = _find_exif_segment(data)
    if exif_segment is None:
        return None
    parser = _ExifParser(exif_segment)
    return parser.camera_model()


def _find_exif_segment(blob: bytes) -> Optional[bytes]:
    import struct

    size = len(blob)
    if size < 4 or blob[0:2] != b"\xFF\xD8":
        return None
    offset = 2

    while offset + 4 <= size:
        if blob[offset] != 0xFF:
            offset += 1
            continue
        marker = blob[offset + 1]
        offset += 2
        if marker == 0xDA:  # Start of Scan
            break
        if offset + 2 > size:
            break
        segment_length = struct.unpack(">H", blob[offset : offset + 2])[0]
        if marker == 0xE1:
            start = offset + 2
            end = start + segment_length - 2
            if end > size:
                break
            segment = blob[start:end]
            if segment.startswith(b"Exif\x00\x00"):
                return segment[6:]
        offset += segment_length
    return None


__all__ = ["GPSData", "extract_gps", "extract_orientation", "extract_camera_model"]
