"""Generate scene-by-scene visual prompts from an original short-video script.

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

import requests


# ============================================================
# CONFIGURATION
# ============================================================

MODEL = "qwen2.5:7b"
OLLAMA_URL = "http://localhost:11434/api/generate"

DEFAULT_VIDEO_ID = "JeLIYZJ3hfM"

EXPECTED_PURPOSES = [
    "HOOK",
    "SETUP",
    "GOAL",
    "PROBLEM",
    "ESCALATION",
    "TWIST",
    "RESOLUTION",
    "PUNCHLINE",
]


# ============================================================
# ARGUMENTS
# ============================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate visual prompts from an original Hindi short-video script."
    )

    parser.add_argument(
        "video_id",
        nargs="?",
        default=DEFAULT_VIDEO_ID,
        help=f"Video ID. Default: {DEFAULT_VIDEO_ID}",
    )

    parser.add_argument(
        "--attempts",
        type=int,
        default=3,
        help="Maximum Ollama attempts. Default: 3.",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=900,
        help="Ollama timeout in seconds. Default: 900.",
    )

    return parser.parse_args()


# ============================================================
# PATHS
# ============================================================

def paths_for(video_id: str) -> tuple[Path, Path]:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", video_id):
        raise ValueError(
            "video_id may contain only letters, numbers, underscores, and hyphens."
        )

    input_path = (
        Path("data")
        / "scripts"
        / f"{video_id}_original_script.json"
    )

    output_path = (
        Path("data")
        / "visuals"
        / f"{video_id}_visual_prompts.json"
    )

    return input_path, output_path


# ============================================================
# LOAD SCRIPT
# ============================================================

def load_script(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Script file not found: {path}"
        )

    try:
        data = json.loads(
            path.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON in script file: {error}"
        ) from error

    if not isinstance(data, dict):
        raise ValueError(
            "Script JSON must contain an object."
        )

    return data


# ============================================================
# SCRIPT VALIDATION
# ============================================================

def validate_script(data: dict[str, Any]) -> None:

    required_fields = [
        "title",
        "hook",
        "story",
        "characters",
        "scenes",
        "ending",
    ]

    for field in required_fields:
        if field not in data:
            raise ValueError(
                f"Script is missing required field: {field}"
            )

    characters = data["characters"]

    if (
        not isinstance(characters, list)
        or not characters
        or not isinstance(characters[0], dict)
    ):
        raise ValueError(
            "'characters' must contain at least one character."
        )

    scenes = data["scenes"]

    if not isinstance(scenes, list):
        raise ValueError(
            "'scenes' must be a list."
        )

    if len(scenes) != 8:
        raise ValueError(
            f"Expected exactly 8 scenes, found {len(scenes)}."
        )

    for index, scene in enumerate(scenes, start=1):

        if not isinstance(scene, dict):
            raise ValueError(
                f"Scene {index} must be an object."
            )

        if scene.get("scene") != index:
            raise ValueError(
                f"Scene numbering error. Expected {index}."
            )

        expected_purpose = EXPECTED_PURPOSES[index - 1]

        if scene.get("purpose") != expected_purpose:
            raise ValueError(
                f"Scene {index} must have purpose "
                f"{expected_purpose}."
            )

        for field in [
            "duration",
            "visual",
            "narration",
        ]:
            if field not in scene:
                raise ValueError(
                    f"Scene {index} is missing '{field}'."
                )


# ============================================================
# CHARACTER BIBLE
# ============================================================

def build_character_bible(data: dict[str, Any]) -> str:
    characters = data["characters"]

    lines = []

    for character in characters:

        name = str(
            character.get("name", "")
        ).strip()

        description = str(
            character.get("description", "")
        ).strip()

        lines.append(
            f"Character name: {name}\n"
            f"Appearance/personality: {description}"
        )

    return "\n\n".join(lines)


# ============================================================
# BUILD OLLAMA PROMPT
# ============================================================

def build_prompt(data: dict[str, Any]) -> str:

    character_bible = build_character_bible(data)

    scenes_text = []

    for scene in data["scenes"]:

        scenes_text.append(
            f"""
SCENE {scene["scene"]}
Purpose: {scene["purpose"]}
Duration: {scene["duration"]} seconds

Original visual idea:
{scene["visual"]}

Narration:
{scene["narration"]}
""".strip()
        )

    all_scenes = "\n\n".join(scenes_text)

    return f"""
You are a professional visual development director for
high-quality Hindi children's vertical short videos.

Your task is to convert an existing ORIGINAL story into
production-ready visual prompts.

DO NOT rewrite the story.

DO NOT change the characters.

DO NOT invent a different story.

Your job is to make the existing story visually producible.

============================================================
VIDEO
============================================================

Title:
{data["title"]}

Hook:
{data["hook"]}

Story:
{data["story"]}

Ending:
{data["ending"]}

============================================================
CHARACTER BIBLE
============================================================

The following character appearance MUST remain visually
consistent across all eight scenes.

{character_bible}

============================================================
SCENES
============================================================

{all_scenes}

============================================================
VISUAL STYLE
============================================================

Create a colourful, polished children's animation style.

The final video is:

- Vertical 9:16
- Family friendly
- Bright
- Cinematic
- Expressive
- Playful
- High visual clarity
- Suitable for children
- No scary imagery
- No violence
- No realistic injuries
- No text inside the generated image
- No watermark
- No logo

Think of a high-quality modern animated children's short.

============================================================
CHARACTER CONSISTENCY
============================================================

Every scene must preserve:

- Same character identity
- Same face
- Same body proportions
- Same clothing
- Same colours
- Same accessories
- Same age/size
- Same visual style

Do NOT randomly change clothing or appearance.

============================================================
EACH SCENE
============================================================

For every scene create:

1. image_prompt
2. video_prompt
3. camera
4. lighting
5. emotion
6. action
7. environment
8. key_props
9. continuity_notes

IMAGE PROMPT:

Describe exactly what should appear in a single
9:16 frame.

Include:

character + environment + action + important prop +
emotion + composition + lighting + visual style.

VIDEO PROMPT:

Describe how the image should be animated for approximately
the scene duration.

Include:

character movement + object movement + camera movement +
facial expression + environmental motion.

Keep the animation simple enough for an AI video generator.

CAMERA:

Examples:

- close-up
- medium shot
- wide shot
- low angle
- overhead
- tracking shot
- push-in
- pull-back

Do not use complicated cinematography.

============================================================
IMPORTANT STORY RULE
============================================================

Each scene must visually represent its own story beat.

Scene 1 = HOOK
Immediately interesting visual.

Scene 2 = SETUP
Clearly establish character and situation.

Scene 3 = GOAL
Clearly show what the character wants.

Scene 4 = PROBLEM
Introduce a visible obstacle.

Scene 5 = ESCALATION
Make the obstacle bigger or funnier.

Scene 6 = TWIST
Reveal something unexpected.

Scene 7 = RESOLUTION
Clearly show the solution working.

Scene 8 = PUNCHLINE
Show a NEW funny visual event.

Scene 8 must NOT simply repeat Scene 7.

============================================================
OUTPUT
============================================================

Return ONLY valid JSON.

Use exactly this structure:

{{
  "video_id": "provided video id",

  "title": "Hindi title",

  "aspect_ratio": "9:16",

  "style": {{
    "overall": "consistent animation style",
    "lighting": "consistent lighting style",
    "color": "bright children's palette",
    "quality": "high quality cinematic children's animation"
  }},

  "character_bible": [
    {{
      "name": "character name",
      "appearance": "very detailed consistent appearance",
      "personality": "personality",
      "clothing": "clothing and accessories",
      "colors": "important colors",
      "consistency_rule": "must remain identical across all scenes"
    }}
  ],

  "scenes": [
    {{
      "scene": 1,
      "purpose": "HOOK",
      "duration": 5,
      "image_prompt": "detailed image generation prompt",
      "video_prompt": "detailed animation prompt",
      "camera": "camera direction",
      "lighting": "lighting direction",
      "emotion": "character emotion",
      "action": "main visible action",
      "environment": "environment description",
      "key_props": [
        "important prop"
      ],
      "continuity_notes": "how character continuity is preserved"
    }},

    {{
      "scene": 2,
      "purpose": "SETUP",
      "duration": 5,
      "image_prompt": "...",
      "video_prompt": "...",
      "camera": "...",
      "lighting": "...",
      "emotion": "...",
      "action": "...",
      "environment": "...",
      "key_props": [],
      "continuity_notes": "..."
    }},

    {{
      "scene": 3,
      "purpose": "GOAL",
      "duration": 5,
      "image_prompt": "...",
      "video_prompt": "...",
      "camera": "...",
      "lighting": "...",
      "emotion": "...",
      "action": "...",
      "environment": "...",
      "key_props": [],
      "continuity_notes": "..."
    }},

    {{
      "scene": 4,
      "purpose": "PROBLEM",
      "duration": 5,
      "image_prompt": "...",
      "video_prompt": "...",
      "camera": "...",
      "lighting": "...",
      "emotion": "...",
      "action": "...",
      "environment": "...",
      "key_props": [],
      "continuity_notes": "..."
    }},

    {{
      "scene": 5,
      "purpose": "ESCALATION",
      "duration": 5,
      "image_prompt": "...",
      "video_prompt": "...",
      "camera": "...",
      "lighting": "...",
      "emotion": "...",
      "action": "...",
      "environment": "...",
      "key_props": [],
      "continuity_notes": "..."
    }},

    {{
      "scene": 6,
      "purpose": "TWIST",
      "duration": 5,
      "image_prompt": "...",
      "video_prompt": "...",
      "camera": "...",
      "lighting": "...",
      "emotion": "...",
      "action": "...",
      "environment": "...",
      "key_props": [],
      "continuity_notes": "..."
    }},

    {{
      "scene": 7,
      "purpose": "RESOLUTION",
      "duration": 5,
      "image_prompt": "...",
      "video_prompt": "...",
      "camera": "...",
      "lighting": "...",
      "emotion": "...",
      "action": "...",
      "environment": "...",
      "key_props": [],
      "continuity_notes": "..."
    }},

    {{
      "scene": 8,
      "purpose": "PUNCHLINE",
      "duration": 5,
      "image_prompt": "...",
      "video_prompt": "...",
      "camera": "...",
      "lighting": "...",
      "emotion": "...",
      "action": "...",
      "environment": "...",
      "key_props": [],
      "continuity_notes": "..."
    }}
  ]
}}

FINAL CHECK:

- Exactly 8 scenes.
- Correct scene numbers 1–8.
- Correct purposes.
- Character appearance remains consistent.
- Each scene has a different visual event.
- Scene 4 is different from Scene 5.
- Scene 5 is different from Scene 6.
- Scene 6 is different from Scene 7.
- Scene 7 solves the problem.
- Scene 8 introduces a new funny event.
- No text inside images.
- No watermark.
- No logo.
- Family friendly.
- Vertical 9:16.
- Return JSON only.
"""


# ============================================================
# OLLAMA
# ============================================================

def ask_ollama(
    prompt: str,
    timeout: int,
) -> str:

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.65,
                    "top_p": 0.9,
                    "num_predict": 5000,
                    "num_ctx": 8192,
                },
            },
            timeout=timeout,
        )

        response.raise_for_status()

    except requests.exceptions.ConnectionError as error:
        raise RuntimeError(
            "Could not connect to Ollama. "
            "Make sure Ollama is running."
        ) from error

    except requests.exceptions.Timeout as error:
        raise RuntimeError(
            "Ollama took too long to respond."
        ) from error

    except requests.exceptions.RequestException as error:
        raise RuntimeError(
            f"Ollama request failed: {error}"
        ) from error

    generated = response.json().get(
        "response",
        ""
    ).strip()

    if not generated:
        raise RuntimeError(
            "Ollama returned an empty response."
        )

    # Remove accidental Markdown fences.
    generated = (
        generated
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )

    return generated


# ============================================================
# VISUAL OUTPUT VALIDATION
# ============================================================

def require_string(
    data: dict[str, Any],
    field: str,
    minimum: int = 1,
) -> str:

    value = data.get(field)

    if (
        not isinstance(value, str)
        or len(value.strip()) < minimum
    ):
        raise ValueError(
            f"'{field}' must be a string "
            f"of at least {minimum} characters."
        )

    return value.strip()


def validate_visual_prompts(
    data: Any,
) -> None:

    if not isinstance(data, dict):
        raise ValueError(
            "Visual output must be a JSON object."
        )

    require_string(
        data,
        "title",
        2,
    )

    if data.get("aspect_ratio") != "9:16":
        raise ValueError(
            "aspect_ratio must be 9:16."
        )

    style = data.get("style")

    if not isinstance(style, dict):
        raise ValueError(
            "'style' must be an object."
        )

    character_bible = data.get(
        "character_bible"
    )

    if (
        not isinstance(character_bible, list)
        or not character_bible
    ):
        raise ValueError(
            "'character_bible' must be a non-empty list."
        )

    for index, character in enumerate(
        character_bible,
        start=1,
    ):

        if not isinstance(character, dict):
            raise ValueError(
                f"Character {index} must be an object."
            )

        require_string(
            character,
            "name",
            2,
        )

        require_string(
            character,
            "appearance",
            20,
        )

        require_string(
            character,
            "personality",
            5,
        )

        require_string(
            character,
            "clothing",
            5,
        )

        require_string(
            character,
            "colors",
            5,
        )

    scenes = data.get("scenes")

    if (
        not isinstance(scenes, list)
        or len(scenes) != 8
    ):
        raise ValueError(
            "'scenes' must contain exactly 8 scenes."
        )

    for index, scene in enumerate(
        scenes,
        start=1,
    ):

        if not isinstance(scene, dict):
            raise ValueError(
                f"Scene {index} must be an object."
            )

        if scene.get("scene") != index:
            raise ValueError(
                f"Scene numbering error at {index}."
            )

        expected_purpose = (
            EXPECTED_PURPOSES[index - 1]
        )

        if scene.get("purpose") != expected_purpose:
            raise ValueError(
                f"Scene {index} must have purpose "
                f"{expected_purpose}."
            )

        duration = scene.get("duration")

        if (
            not isinstance(duration, (int, float))
            or isinstance(duration, bool)
            or duration < 4
            or duration > 7
        ):
            raise ValueError(
                f"Scene {index} duration must be "
                "between 4 and 7 seconds."
            )

        required_fields = [
            "image_prompt",
            "video_prompt",
            "camera",
            "lighting",
            "emotion",
            "action",
            "environment",
            "continuity_notes",
        ]

        for field in required_fields:

            require_string(
                scene,
                field,
                5,
            )

        key_props = scene.get(
            "key_props"
        )

        if not isinstance(
            key_props,
            list,
        ):
            raise ValueError(
                f"Scene {index} key_props "
                "must be a list."
            )

    # Duration check.
    total_duration = sum(
        float(scene["duration"])
        for scene in scenes
    )

    if not 35 <= total_duration <= 50:
        raise ValueError(
            f"Total duration must be 35–50 seconds. "
            f"Got {total_duration:.1f}."
        )


# ============================================================
# SAVE
# ============================================================

def save_output(
    output_path: Path,
    data: dict[str, Any],
) -> None:

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    args = parse_args()

    if args.attempts < 1:
        raise ValueError(
            "--attempts must be at least 1."
        )

    if args.timeout < 30:
        raise ValueError(
            "--timeout must be at least 30 seconds."
        )

    input_path, output_path = paths_for(
        args.video_id
    )

    print(
        f"Loading script: {input_path}"
    )

    script = load_script(
        input_path
    )

    print("Validating source script...")

    validate_script(
        script
    )

    print(
        f"Script loaded: {script['title']}"
    )

    prompt = build_prompt(
        script
    )

    last_error = ""

    for attempt in range(
        1,
        args.attempts + 1,
    ):

        print(
            f"Generating visual prompts with "
            f"{MODEL} "
            f"(attempt {attempt}/{args.attempts})..."
        )

        try:

            raw = ask_ollama(
                prompt,
                args.timeout,
            )

            print(
                "Response received from Ollama."
            )

            data = json.loads(
                raw
            )

            validate_visual_prompts(
                data
            )

        except json.JSONDecodeError as error:

            last_error = (
                f"Invalid JSON: {error}"
            )

            print(
                f"Rejected: {last_error}"
            )

            rejected_path = (
                output_path.parent
                / f"{args.video_id}_visual_rejected_attempt_{attempt}.txt"
            )

            rejected_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            rejected_path.write_text(
                raw if "raw" in locals() else "",
                encoding="utf-8",
            )

            continue

        except ValueError as error:

            last_error = str(error)

            print(
                f"Rejected: {last_error}"
            )

            rejected_path = (
                output_path.parent
                / f"{args.video_id}_visual_rejected_attempt_{attempt}.json"
            )

            rejected_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            rejected_path.write_text(
                raw if "raw" in locals() else "",
                encoding="utf-8",
            )

            continue

        print(
            "Visual prompts validated successfully."
        )

        save_output(
            output_path,
            data,
        )

        total_duration = sum(
            float(scene["duration"])
            for scene in data["scenes"]
        )

        print(
            f"Validated: 8 scenes, "
            f"{total_duration:.1f} seconds."
        )

        print(
            f"Character: "
            f"{data['character_bible'][0]['name']}"
        )

        print(
            f"Saved to: {output_path}"
        )

        return

    raise RuntimeError(
        "Could not generate valid visual prompts "
        f"after {args.attempts} attempts. "
        f"Last issue: {last_error}"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:
        main()

    except (
        FileNotFoundError,
        RuntimeError,
        ValueError,
    ) as error:

        print(
            f"ERROR: {error}",
            file=sys.stderr,
        )

        sys.exit(1)