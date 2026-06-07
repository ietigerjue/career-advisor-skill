#!/usr/bin/env python3
"""Remove a portrait photo background for Chinese resume use.

This script runs fully locally with rembg + Pillow. It never uploads photos and
never overwrites the source image unless --force is explicitly provided.
"""

from __future__ import annotations

import argparse
import re
import sys
from io import BytesIO
from pathlib import Path
from typing import Sequence


NAMED_BACKGROUNDS = {
    "white": (255, 255, 255, 255),
    "light-blue": (219, 234, 254, 255),
    "light-gray": (243, 244, 246, 255),
    "transparent": None,
}


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove a portrait background locally and save a resume-ready copy."
    )
    parser.add_argument("input", type=Path, help="Source portrait image.")
    parser.add_argument("output", type=Path, help="Output image path.")
    parser.add_argument(
        "--background",
        default="white",
        help="white, light-blue, light-gray, transparent, or a hex color such as #ffffff.",
    )
    parser.add_argument(
        "--resize-mm",
        default="25x30",
        help="Optional final size in millimeters, WIDTHxHEIGHT. Use 'none' to keep size.",
    )
    parser.add_argument("--dpi", type=int, default=300, help="DPI used for --resize-mm.")
    parser.add_argument(
        "--model",
        default="u2netp",
        help="rembg model name. u2netp is smaller; u2net can be higher quality.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow overwriting an existing output file or writing over the input path.",
    )
    return parser.parse_args(argv)


def parse_background(value: str):
    normalized = value.strip().lower()
    if normalized in NAMED_BACKGROUNDS:
        return NAMED_BACKGROUNDS[normalized]
    match = re.fullmatch(r"#?([0-9a-f]{6})", normalized)
    if not match:
        allowed = ", ".join(NAMED_BACKGROUNDS)
        raise SystemExit(f"Unsupported background '{value}'. Use {allowed}, or #RRGGBB.")
    hex_value = match.group(1)
    return tuple(int(hex_value[index : index + 2], 16) for index in (0, 2, 4)) + (255,)


def parse_resize(value: str, dpi: int) -> tuple[int, int] | None:
    if value.strip().lower() == "none":
        return None
    match = re.fullmatch(r"(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)", value.strip().lower())
    if not match:
        raise SystemExit("--resize-mm must be WIDTHxHEIGHT, for example 25x30, or 'none'.")
    width_mm = float(match.group(1))
    height_mm = float(match.group(2))
    return (round(width_mm / 25.4 * dpi), round(height_mm / 25.4 * dpi))


def validate_paths(input_path: Path, output_path: Path, force: bool) -> None:
    if not input_path.is_file():
        raise SystemExit(f"Input image not found: {input_path}")
    if input_path.resolve() == output_path.resolve() and not force:
        raise SystemExit("Refusing to overwrite the source image. Use a different output or --force.")
    if output_path.exists() and not force:
        raise SystemExit(f"Output already exists: {output_path}. Use --force to overwrite.")
    output_path.parent.mkdir(parents=True, exist_ok=True)


def remove_background(args: argparse.Namespace) -> None:
    try:
        from PIL import Image  # type: ignore
        from rembg import remove, new_session  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "Install optional photo dependencies first:\n"
            "  pip install rembg pillow\n"
            "The first run may download the selected rembg model to the local cache."
        ) from exc

    with Image.open(args.input) as source:
        source = source.convert("RGBA")
        buffer = BytesIO()
        source.save(buffer, format="PNG")

    session = new_session(args.model)
    removed_bytes = remove(buffer.getvalue(), session=session)
    with Image.open(BytesIO(removed_bytes)) as cutout:
        cutout = cutout.convert("RGBA")
        target_size = parse_resize(args.resize_mm, args.dpi)
        if target_size:
            cutout = cutout.resize(target_size, Image.Resampling.LANCZOS)
        background = parse_background(args.background)
        if background is None:
            result = cutout
        else:
            result = Image.new("RGBA", cutout.size, background)
            result.alpha_composite(cutout)
            result = result.convert("RGB")
        save_kwargs = {}
        if args.output.suffix.lower() in {".jpg", ".jpeg"}:
            save_kwargs["quality"] = 95
            if result.mode == "RGBA":
                canvas = Image.new("RGB", result.size, (255, 255, 255))
                canvas.paste(result, mask=result.getchannel("A"))
                result = canvas
        result.save(args.output, dpi=(args.dpi, args.dpi), **save_kwargs)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    validate_paths(args.input, args.output, args.force)
    remove_background(args)
    print(f"Background-processed photo written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
