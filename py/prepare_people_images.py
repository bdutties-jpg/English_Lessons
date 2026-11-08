from __future__ import annotations

from pathlib import Path
import shutil

from PIL import Image, ImageOps


ROOT_DIR = Path(__file__).resolve().parent.parent
PEOPLE_DIR = ROOT_DIR / "assets" / "people"
HANDS_DIR = PEOPLE_DIR / "hands"
FACES_DIR = PEOPLE_DIR / "faces"
SUPPORTED_SUFFIXES = {".jpeg", ".jpg", ".png", ".webp"}
# The source art is square. A top-centered 72% crop keeps the full face and
# shoulders while ending just above the outstretched hands.
FACE_CROP_RATIO = 0.72


def move_source_images() -> list[Path]:
    HANDS_DIR.mkdir(parents=True, exist_ok=True)
    for image_path in PEOPLE_DIR.iterdir():
        if image_path.is_file() and image_path.suffix.casefold() in SUPPORTED_SUFFIXES:
            shutil.move(str(image_path), HANDS_DIR / image_path.name)
    return sorted(
        (path for path in HANDS_DIR.iterdir() if path.suffix.casefold() in SUPPORTED_SUFFIXES),
        key=lambda path: path.name.casefold(),
    )


def create_face_crop(source_path: Path) -> Path:
    FACES_DIR.mkdir(parents=True, exist_ok=True)
    with Image.open(source_path) as source:
        image = ImageOps.exif_transpose(source)
        width, height = image.size
        crop_size = round(min(width, height) * FACE_CROP_RATIO)
        left = (width - crop_size) // 2
        top = 0
        face = image.crop((left, top, left + crop_size, top + crop_size))

        destination = FACES_DIR / source_path.name
        if destination.suffix.casefold() in {".jpg", ".jpeg"}:
            face.convert("RGB").save(destination, quality=95, optimize=True)
        else:
            face.save(destination)
    return destination


def main() -> None:
    source_images = move_source_images()
    if not source_images:
        raise FileNotFoundError(f"No people images found in {HANDS_DIR}")

    face_images = [create_face_crop(source_path) for source_path in source_images]
    print(f"Moved {len(source_images)} people images to {HANDS_DIR}")
    print(f"Created {len(face_images)} square face crops in {FACES_DIR}")


if __name__ == "__main__":
    main()
