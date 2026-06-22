from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


ROOT_DIR = Path(__file__).resolve().parent.parent
ICONS_DIR = ROOT_DIR / "assets" / "icons"
DEFAULT_SOURCE_CANDIDATES = [
    ICONS_DIR / "Hello_Teacher_Original.png",
    ICONS_DIR / "Hello_Teacher.png",
]

# Future maintainers / LLMs:
# - The HTML templates and site.webmanifest already reference these exact output filenames.
# - Keep these names stable unless you also update html_template/*.html and site.webmanifest.
# - iOS Home Screen uses apple-touch-icon.png most directly.
# - icon-192.png and icon-512.png improve install support for other browsers and platforms.
OUTPUT_SPECS = {
    "apple-touch-icon.png": (180, 180),
    "icon-192.png": (192, 192),
    "icon-512.png": (512, 512),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the app icon set from a square PNG source. "
            "Example: python3 py/generate_icons.py assets/icons/Hello_Teacher_Original.png"
        )
    )
    parser.add_argument(
        "source",
        nargs="?",
        help="Optional path to the source PNG. Defaults to the best known icon source in assets/icons/.",
    )
    return parser.parse_args()


def resolve_source(source_arg: str | None) -> Path:
    if source_arg:
        candidate = Path(source_arg)
        if not candidate.is_absolute():
            candidate = ROOT_DIR / candidate
        return candidate

    for candidate in DEFAULT_SOURCE_CANDIDATES:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "No default icon source found. Provide a source PNG path, for example: "
        "python3 py/generate_icons.py assets/icons/Hello_Teacher_Original.png"
    )


def validate_source(source: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Source icon not found: {source}")
    if source.suffix.casefold() != ".png":
        raise ValueError(f"Source icon must be a PNG file: {source}")

    with Image.open(source) as image:
        width, height = image.size
        if width != height:
            raise ValueError(
                f"Source icon must be square. Got {width}x{height} from {source}"
            )


def generate_icons(source: Path) -> None:
    ICONS_DIR.mkdir(parents=True, exist_ok=True)

    with Image.open(source) as image:
        rgba_image = image.convert("RGBA")
        print(f"Using source: {source.relative_to(ROOT_DIR)} ({rgba_image.width}x{rgba_image.height})")

        for filename, size in OUTPUT_SPECS.items():
            output_path = ICONS_DIR / filename
            resized = rgba_image.resize(size, Image.Resampling.LANCZOS)
            resized.save(output_path)
            print(f"Wrote {output_path.relative_to(ROOT_DIR)} ({size[0]}x{size[1]})")


def main() -> None:
    args = parse_args()
    source = resolve_source(args.source)
    validate_source(source)
    generate_icons(source)


if __name__ == "__main__":
    main()