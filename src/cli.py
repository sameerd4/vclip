#!/usr/bin/env python3
"""Prototype CLI for staging and previewing LUT options."""

from __future__ import annotations

import argparse
from pathlib import Path

from pipeline import Grader, LutLibrary, ProjectPaths, extract_gps, find_new_photos


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local grading pipeline prototype")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Base path of the project (default: current directory)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List staged photos and available LUTs",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="Include EXIF-derived details when listing photos",
    )
    parser.add_argument(
        "--grade",
        metavar="PHOTO",
        help="Apply a LUT to the specified photo filename from the inbox",
    )
    parser.add_argument(
        "--lut",
        metavar="LUT",
        help="Name of the LUT to apply when using --grade",
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Fail if targets already exist instead of overwriting",
    )
    return parser.parse_args()


def list_state(paths: ProjectPaths, library: LutLibrary, show_details: bool = False) -> None:
    photos = list(find_new_photos(paths.inbox))

    print("Staged photos:")
    if not photos:
        print("  (none found)")
    for asset in photos:
        orient = "vertical" if asset.is_vertical() else "landscape"
        line = f"  - {asset.path.name} [{orient}]"
        print(line)
        if show_details:
            dims = asset.dimensions()
            if dims:
                print(f"      size: {dims[0]}×{dims[1]}")
            else:
                print("      size: (unknown)")
            cam_info = asset.device_summary()
            if cam_info:
                friendly, raw = cam_info
                if friendly == raw:
                    print(f"      camera: {friendly}")
                else:
                    print(f"      camera: {friendly} ({raw})")
            else:
                print("      camera: (unknown)")
            gps = None
            try:
                gps = extract_gps(asset.path)
            except Exception as exc:
                print(f"      exif: error reading GPS ({exc})")
            else:
                if gps:
                    lat = f"{gps.latitude:.6f}"
                    lon = f"{gps.longitude:.6f}"
                    print(f"      gps: {lat}, {lon}")
                else:
                    print("      gps: (not present)")

    print("\nAvailable LUTs:")
    profiles = list(library.profiles())
    if not profiles:
        print("  (drop .cube files into", paths.luts, ")")
    for lut in profiles:
        print(f"  - {lut.name}")


def main() -> None:
    args = parse_args()
    paths = ProjectPaths.from_env(args.project_root)
    library = LutLibrary(paths.luts)
    library.ensure()
    library.refresh()

    if args.grade:
        if not args.lut:
            raise SystemExit("error: --grade requires --lut to be specified")
        grade_photo(paths, library, args.grade, args.lut, overwrite=not args.no_overwrite)
        return

    if args.list:
        list_state(paths, library, show_details=args.details)
        return

    print("Prototype CLI ready. Use --list to view staged assets.")


def grade_photo(
    paths: ProjectPaths,
    library: LutLibrary,
    photo_name: str,
    lut_name: str,
    overwrite: bool,
) -> None:
    photos = {asset.path.name: asset for asset in find_new_photos(paths.inbox)}
    asset = _resolve_case_insensitive(photos, photo_name)
    if asset is None:
        raise SystemExit(f"error: photo '{photo_name}' not found in inbox")

    lut_profiles = {profile.name: profile for profile in library.profiles()}
    lut = _resolve_case_insensitive(lut_profiles, lut_name)
    if lut is None:
        raise SystemExit(f"error: LUT '{lut_name}' not found")

    grader = Grader(paths)
    result = grader.apply(asset, lut, overwrite=overwrite)

    print("Graded photo:")
    print(f"  source:    {asset.path}")
    print(f"  lut:       {lut.name}")
    print(f"  processed: {result.processed_path}")
    print(f"  gallery:   {result.gallery_path}")


def _resolve_case_insensitive(mapping, key: str):
    if key in mapping:
        return mapping[key]
    lowered = key.lower()
    for name, value in mapping.items():
        if name.lower() == lowered:
            return value
    return None


if __name__ == "__main__":
    main()
