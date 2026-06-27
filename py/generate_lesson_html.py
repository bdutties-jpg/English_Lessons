from __future__ import annotations

from datetime import datetime, timezone
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import MATH_CONFIG, READING_CONFIG

SHORT_SENTENCES_AUDIO_DIR = ROOT_DIR / "assets" / "audio" / "Short sentences"
LETTER_SOUNDS_AUDIO_DIR = ROOT_DIR / "assets" / "audio" / "Letters" / "Learning"
MENU_AUDIO_DIR = ROOT_DIR / "assets" / "audio" / "Menu"
UI_SOUNDS_AUDIO_DIR = ROOT_DIR / "assets" / "audio" / "UI_Sounds"
VOCABULARY_AUDIO_DIR = ROOT_DIR / "assets" / "audio" / "Vocabulary"
TEMPLATE_PATH = ROOT_DIR / "html_template" / "lesson_template.html"
HOME_TEMPLATE_PATH = ROOT_DIR / "html_template" / "home_template.html"
MATH_TEMPLATE_PATH = ROOT_DIR / "html_template" / "math_template.html"
READING_TEMPLATE_PATH = ROOT_DIR / "html_template" / "reading_template.html"
OUTPUT_PATH = ROOT_DIR / "output" / "short_sentences.html"
MATH_OUTPUT_PATH = ROOT_DIR / "output" / "math.html"
READING_OUTPUT_PATH = ROOT_DIR / "output" / "reading.html"
LETTER_SOUNDS_OUTPUT_PATH = ROOT_DIR / "output" / "letter_sounds.html"
INDEX_PATH = ROOT_DIR / "index.html"
APP_VERSION_PATH = ROOT_DIR / "app_version.json"
PLACEHOLDER = "__LESSONS_JSON__"
MENU_PLACEHOLDER = "__MENU_JSON__"
PAGE_CONFIG_PLACEHOLDER = "__PAGE_CONFIG_JSON__"
MATH_CONFIG_PLACEHOLDER = "__MATH_CONFIG_JSON__"
APP_VERSION_PLACEHOLDER = "__APP_VERSION__"
FILENAME_PATTERN = re.compile(r"^(?P<emoji>.+?)\s*-\s*(?P<text>.+)$")
VOCABULARY_PATTERN = re.compile(r"^(?P<word>.+?)\s+(?P<emoji>\S+)$")
APP_VERSION = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass(frozen=True)
class LessonButton:
    emoji: str
    text: str
    audio: str


@dataclass(frozen=True)
class GridButton:
    emoji: str
    text: str
    audio: str


@dataclass(frozen=True)
class VocabularyItem:
    word: str
    emoji: str
    audio: str


def encode_relative_path(path: Path, *, from_output_dir: bool = True) -> str:
    relative_path = path.relative_to(ROOT_DIR)
    encoded_path = "/".join(quote(part) for part in relative_path.parts)
    return f"../{encoded_path}" if from_output_dir else encoded_path


def apply_app_version(template: str) -> str:
    if APP_VERSION_PLACEHOLDER not in template:
        raise ValueError(f"Template is missing placeholder {APP_VERSION_PLACEHOLDER}")
    return template.replace(APP_VERSION_PLACEHOLDER, APP_VERSION)


def build_menu_audio_map() -> dict[str, str]:
    return {
        audio_path.stem.casefold(): encode_relative_path(audio_path, from_output_dir=False)
        for audio_path in MENU_AUDIO_DIR.glob("*.m4a")
    }


def build_ui_sound_map(*, from_output_dir: bool = True) -> dict[str, str]:
    return {
        audio_path.stem.casefold(): encode_relative_path(audio_path, from_output_dir=from_output_dir)
        for audio_path in UI_SOUNDS_AUDIO_DIR.glob("*.m4a")
    }


def build_letter_audio_map(*, from_output_dir: bool = True) -> dict[str, str]:
    preferred_notes = {
        "a": "soft",
        "c": "hard",
        "e": "soft",
        "i": "soft",
        "o": "soft",
        "u": "soft",
        "g": "hard",
    }
    candidates: dict[str, dict[str, str]] = {}

    for audio_path in sorted(LETTER_SOUNDS_AUDIO_DIR.rglob("*.m4a"), key=lambda path: path.stem.casefold()):
        label = audio_path.stem.strip()
        match = re.match(r"^(?P<letter>.+?)\s*\((?P<note>hard|soft)\)$", label, re.IGNORECASE)
        base_letter = match.group("letter").strip() if match else label
        note = match.group("note").strip().lower() if match else "default"
        candidates.setdefault(base_letter.casefold(), {})[note] = encode_relative_path(
            audio_path,
            from_output_dir=from_output_dir,
        )

    audio_map: dict[str, str] = {}
    for letter, options in candidates.items():
        preferred_note = preferred_notes.get(letter)
        if preferred_note and preferred_note in options:
            audio_map[letter] = options[preferred_note]
        elif "default" in options:
            audio_map[letter] = options["default"]
        else:
            audio_map[letter] = options.get("soft") or options.get("hard") or next(iter(options.values()))

    return audio_map


def parse_audio_file(audio_path: Path) -> LessonButton:
    match = FILENAME_PATTERN.match(audio_path.stem)
    if not match:
        raise ValueError(
            f"Audio file '{audio_path.name}' must follow the pattern 'emoji - text.m4a'."
        )

    return LessonButton(
        emoji=match.group("emoji").strip(),
        text=match.group("text").strip(),
        audio=encode_relative_path(audio_path),
    )


def build_lessons() -> list[dict[str, str]]:
    audio_files = sorted(
        SHORT_SENTENCES_AUDIO_DIR.glob("*.m4a"), key=lambda path: path.name.casefold()
    )
    if not audio_files:
        raise FileNotFoundError(f"No .m4a files found in {SHORT_SENTENCES_AUDIO_DIR}")

    return [parse_audio_file(audio_path).__dict__ for audio_path in audio_files]


def build_letter_sounds() -> list[dict[str, str]]:
    def sort_key(audio_path: Path) -> tuple[int, object, str]:
        label = audio_path.stem.strip()
        match = re.match(r"^(?P<letter>.+?)\s*\((?P<note>hard|soft)\)$", label, re.IGNORECASE)
        base_letter = match.group("letter").strip() if match else label
        lowered = base_letter.casefold()
        special_order = {"ch": 0, "th": 1}
        if lowered in special_order:
            return (1, special_order[lowered], label.casefold())
        return (0, lowered, label.casefold())

    audio_files = sorted(LETTER_SOUNDS_AUDIO_DIR.glob("*.m4a"), key=sort_key)
    if not audio_files:
        raise FileNotFoundError(f"No .m4a files found in {LETTER_SOUNDS_AUDIO_DIR}")

    buttons: list[dict[str, str]] = []
    for audio_path in audio_files:
        label = audio_path.stem.strip()
        match = re.match(r"^(?P<letter>.+?)\s*\((?P<note>hard|soft)\)$", label, re.IGNORECASE)
        if match:
            letter = match.group("letter").strip()
            note = match.group("note").strip().lower()
        else:
            letter = label
            note = ""

        buttons.append(
            {
                "emoji": "",
                "text": label,
                "audio": encode_relative_path(audio_path),
                "display": f"{letter.upper()} {letter.lower()}",
                "note": f"({note})" if note else "",
            }
        )

    return buttons


def build_vocabulary() -> list[dict[str, str]]:
    audio_files = sorted(VOCABULARY_AUDIO_DIR.glob("*.m4a"), key=lambda path: path.stem.casefold())
    if not audio_files:
        raise FileNotFoundError(f"No .m4a files found in {VOCABULARY_AUDIO_DIR}")

    items: list[dict[str, str]] = []
    for audio_path in audio_files:
        label = audio_path.stem.strip()
        match = VOCABULARY_PATTERN.match(label)
        if not match:
            raise ValueError(
                f"Vocabulary file '{audio_path.name}' must follow the pattern 'Word emoji.m4a'."
            )
        items.append(
            VocabularyItem(
                word=match.group("word").strip(),
                emoji=match.group("emoji").strip(),
                audio=encode_relative_path(audio_path),
            ).__dict__
        )

    return items


def render_audio_grid_page(
    items: list[dict[str, str]],
    *,
    title: str,
    subtitle: str,
    description: str,
    back_audio: str,
    title_uppercase: bool = True,
    button_style: str = "default",
) -> str:
    template = apply_app_version(TEMPLATE_PATH.read_text(encoding="utf-8"))
    lessons_json = json.dumps(items, ensure_ascii=False, indent=2)
    page_config = json.dumps(
        {
            "title": title,
            "subtitle": subtitle,
            "description": description,
            "backAudio": back_audio,
            "titleUppercase": title_uppercase,
            "buttonStyle": button_style,
        },
        ensure_ascii=False,
        indent=2,
    )
    if PLACEHOLDER not in template:
        raise ValueError(f"Template is missing placeholder {PLACEHOLDER}")
    if PAGE_CONFIG_PLACEHOLDER not in template:
        raise ValueError(f"Template is missing placeholder {PAGE_CONFIG_PLACEHOLDER}")
    return (
        template.replace(PLACEHOLDER, lessons_json)
        .replace(PAGE_CONFIG_PLACEHOLDER, page_config)
    )


def render_home_html() -> str:
    template = apply_app_version(HOME_TEMPLATE_PATH.read_text(encoding="utf-8"))
    menu_audio = build_menu_audio_map()
    menu_items = [
        {
            "emoji": "🗣️",
            "title": "Short Sentences",
            "subtitle": "Những câu ngắn",
            "href": "output/short_sentences.html",
            "audio": menu_audio.get("short sentences", ""),
        },
        {
            "emoji": "🔤",
            "title": "Letter Sounds",
            "subtitle": "âm của chữ cái",
            "href": "output/letter_sounds.html",
            "audio": menu_audio.get("letter sounds", ""),
        },
        {
            "emoji": "➕➖",
            "title": "Math",
            "subtitle": "toán học",
            "href": "output/math.html",
            "audio": menu_audio.get("math", ""),
        },
        {
            "emoji": "📖",
            "title": "Reading",
            "subtitle": "đọc",
            "href": "output/reading.html",
            "audio": menu_audio.get("reading", ""),
        },
    ]
    menu_json = json.dumps(menu_items, ensure_ascii=False, indent=2)
    if MENU_PLACEHOLDER not in template:
        raise ValueError(f"Template is missing placeholder {MENU_PLACEHOLDER}")
    return template.replace(MENU_PLACEHOLDER, menu_json)


def render_math_html() -> str:
    template = apply_app_version(MATH_TEMPLATE_PATH.read_text(encoding="utf-8"))
    if MATH_CONFIG_PLACEHOLDER not in template:
        raise ValueError(f"Template is missing placeholder {MATH_CONFIG_PLACEHOLDER}")
    math_config = dict(MATH_CONFIG)
    for key in ("correct_answer", "wrong_answer", "star_celebration", "star_party"):
        audio_path = math_config.get(key)
        if audio_path:
            math_config[key] = encode_relative_path(ROOT_DIR / audio_path)
    return template.replace(MATH_CONFIG_PLACEHOLDER, json.dumps(math_config, ensure_ascii=False, indent=2))


def render_reading_html() -> str:
    template = apply_app_version(READING_TEMPLATE_PATH.read_text(encoding="utf-8"))
    vocabulary = build_vocabulary()
    letter_audio_map = build_letter_audio_map()
    reading_config = dict(READING_CONFIG)

    for key in ("correct_answer", "wrong_answer", "star_celebration", "star_party"):
        audio_path = reading_config.get(key)
        if audio_path:
            reading_config[key] = encode_relative_path(ROOT_DIR / audio_path)

    for item in vocabulary:
        letter_buttons: list[dict[str, str]] = []
        for letter in item["word"]:
            audio = letter_audio_map.get(letter.casefold())
            if not audio:
                raise ValueError(f"No letter sound audio found for '{letter}' in word '{item['word']}'.")
            letter_buttons.append({"label": letter.upper(), "audio": audio})
        item["letters"] = letter_buttons

    page_config = {
        "title": "Reading",
        "subtitle": "đọc",
        "description": "Tap the letters, then choose the matching picture.",
        "backAudio": encode_relative_path(MENU_AUDIO_DIR / "Back to home.m4a"),
        "readingConfig": reading_config,
        "vocabulary": vocabulary,
    }
    if PAGE_CONFIG_PLACEHOLDER not in template:
        raise ValueError(f"Template is missing placeholder {PAGE_CONFIG_PLACEHOLDER}")
    return template.replace(PAGE_CONFIG_PLACEHOLDER, json.dumps(page_config, ensure_ascii=False, indent=2))


def main() -> None:
    lessons = build_lessons()
    letter_sounds = build_letter_sounds()
    back_audio = encode_relative_path(MENU_AUDIO_DIR / "Back to home.m4a")
    lesson_html = render_audio_grid_page(
        lessons,
        title="Short Sentences",
        subtitle="Những câu ngắn",
        description="Press a picture to hear the English sentence one time.",
        back_audio=back_audio,
    )
    letter_sounds_html = render_audio_grid_page(
        letter_sounds,
        title="Letter Sounds",
        subtitle="âm của chữ cái",
        description="Tap a button to hear each letter sound.",
        back_audio=back_audio,
        title_uppercase=False,
        button_style="letter-sounds",
    )
    home_html = render_home_html()
    math_html = render_math_html()
    reading_html = render_reading_html()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(lesson_html, encoding="utf-8")
    MATH_OUTPUT_PATH.write_text(math_html, encoding="utf-8")
    READING_OUTPUT_PATH.write_text(reading_html, encoding="utf-8")
    LETTER_SOUNDS_OUTPUT_PATH.write_text(letter_sounds_html, encoding="utf-8")
    INDEX_PATH.write_text(home_html, encoding="utf-8")
    APP_VERSION_PATH.write_text(json.dumps({"version": APP_VERSION}, indent=2), encoding="utf-8")
    print(f"Wrote {len(lessons)} buttons to {OUTPUT_PATH}")
    print(f"Wrote math page to {MATH_OUTPUT_PATH}")
    print(f"Wrote reading page to {READING_OUTPUT_PATH}")
    print(f"Wrote {len(letter_sounds)} buttons to {LETTER_SOUNDS_OUTPUT_PATH}")
    print(f"Wrote home page to {INDEX_PATH}")
    print(f"Wrote app version to {APP_VERSION_PATH}")


if __name__ == "__main__":
    main()