"""Generate image-generation prompts locally from an approved script.

Usage:
    python -m src.visuals.generate_prompts JeLIYZJ3hfM
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


DEFAULT_VIDEO_ID = "JeLIYZJ3hfM"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate visual prompts locally from a validated script."
    )
    parser.add_argument(
        "video_id",
        nargs="?",
        default=DEFAULT_VIDEO_ID,
    )
    return parser.parse_args()


def paths_for(video_id: str) -> tuple[Path, Path]:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", video_id):
        raise ValueError(
            "video_id may contain only letters, numbers, underscores, and hyphens."
        )

    script_path = Path("data/scripts") / f"{video_id}_original_script.json"
    output_path = Path("data/visuals") / f"{video_id}_visual_prompts.json"

    return script_path, output_path


def load_script(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Script file not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError("Script JSON must contain an object.")

    scenes = data.get("scenes")

    if not isinstance(scenes, list) or len(scenes) != 8:
        raise ValueError("Script must contain exactly 8 scenes.")

    return data


def clean_text(text: str) -> str:
    """Normalize whitespace while preserving Hindi text."""
    return re.sub(r"\s+", " ", str(text)).strip()


def build_character_description(data: dict[str, Any]) -> str:
    characters = data.get("characters", [])

    if not characters:
        return "consistent main character"

    character = characters[0]

    name = clean_text(character.get("name", "मुख्य पात्र"))
    description = clean_text(
        character.get("description", "रंगीन, प्यारा और बाल-अनुकूल पात्र")
    )

    return f"{name}, {description}"


def build_visual_prompt(
    character_description: str,
    scene: dict[str, Any],
) -> str:
    visual = clean_text(scene.get("visual", ""))
    purpose = clean_text(scene.get("purpose", ""))

    return (
        f"Create a colourful 3D children's animation frame. "
        f"Main character: {character_description}. "
        f"Scene purpose: {purpose}. "
        f"Action and composition: {visual}. "
        f"Keep the character appearance, clothing, colours and proportions "
        f"consistent with previous scenes. "
        f"Bright cinematic lighting, expressive face, clear readable action, "
        f"playful family-friendly atmosphere, vertical 9:16 composition, "
        f"no text, no subtitles, no watermark."
    )


def generate_prompts(data: dict[str, Any]) -> dict[str, Any]:
    character_description = build_character_description(data)

    output_scenes = []

    for scene in data["scenes"]:
        prompt = build_visual_prompt(
            character_description,
            scene,
        )

        output_scenes.append(
            {
                "scene": scene["scene"],
                "duration": scene["duration"],
                "purpose": scene["purpose"],
                "narration": clean_text(scene["narration"]),
                "source_visual": clean_text(scene["visual"]),
                "image_prompt": prompt,
            }
        )

    return {
        "video_id": None,
        "title": clean_text(data.get("title", "")),
        "character": character_description,
        "scenes": output_scenes,
    }


def main() -> None:
    args = parse_args()

    script_path, output_path = paths_for(args.video_id)

    print(f"Loading script: {script_path}")

    data = load_script(script_path)

    print(f"Script loaded: {data.get('title', '')}")
    print("Generating visual prompts locally...")
    
    result = generate_prompts(data)
    result["video_id"] = args.video_id

    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Generated {len(result['scenes'])} visual prompts.")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
