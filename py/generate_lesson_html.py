from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote


ROOT_DIR = Path(__file__).resolve().parent.parent
AUDIO_DIR = ROOT_DIR / "assets" / "audio"
TEMPLATE_PATH = ROOT_DIR / "html_template" / "lesson_template.html"
OUTPUT_PATH = ROOT_DIR / "output" / "lesson_buttons.html"
PLACEHOLDER = "__LESSONS_JSON__"
FILENAME_PATTERN = re.compile(r"^(?P<emoji>.+?)\s*-\s*(?P<text>.+)$")


@dataclass(frozen=True)
class LessonButton:
    emoji: str
    text: str
    audio: str


def parse_audio_file(audio_path: Path) -> LessonButton:
    match = FILENAME_PATTERN.match(audio_path.stem)
    if not match:
        raise ValueError(
            f"Audio file '{audio_path.name}' must follow the pattern 'emoji - text.m4a'."
        )

    relative_audio_path = audio_path.relative_to(ROOT_DIR)
    encoded_audio_path = "/".join(quote(part) for part in relative_audio_path.parts)
    return LessonButton(
        emoji=match.group("emoji").strip(),
        text=match.group("text").strip(),
        audio=f"../{encoded_audio_path}",
    )


def build_lessons() -> list[dict[str, str]]:
    audio_files = sorted(AUDIO_DIR.glob("*.m4a"), key=lambda path: path.name.casefold())
    if not audio_files:
        raise FileNotFoundError(f"No .m4a files found in {AUDIO_DIR}")

    return [parse_audio_file(audio_path).__dict__ for audio_path in audio_files]


def render_html(lessons: list[dict[str, str]]) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    lessons_json = json.dumps(lessons, ensure_ascii=False, indent=2)
    if PLACEHOLDER not in template:
        raise ValueError(f"Template is missing placeholder {PLACEHOLDER}")
    return template.replace(PLACEHOLDER, lessons_json)


def main() -> None:
    lessons = build_lessons()
    html = render_html(lessons)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"Wrote {len(lessons)} buttons to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()