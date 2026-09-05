"""Generate an original Hindi children's script from a video analysis.

Usage:
    python -m src.script.generate JeLIYZJ3hfM
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import requests


MODEL = "qwen2.5:7b"
OLLAMA_URL = "http://localhost:11434/api/generate"

DEFAULT_VIDEO_ID = "JeLIYZJ3hfM"

MIN_DURATION = 35.0
MAX_DURATION = 50.0

SCENE_PURPOSES = [
    "HOOK",
    "SETUP",
    "GOAL",
    "PROBLEM",
    "ESCALATION",
    "TWIST",
    "RESOLUTION",
    "PUNCHLINE",
]


# These are deliberately unrelated to the source video's plot.
ORIGINAL_STORY_SEEDS = (
    (
        "मुख्य पात्र गुग्गू, बैंगनी टोपी पहनने वाला नन्हा बादल-मिस्त्री है। "
        "उसे सूर्यास्त से पहले पहाड़ी गाँव की इंद्रधनुषी घंटी ठीक करनी है, "
        "लेकिन हवा उसके चमकते पेंच उड़ा देती है।"
    ),
    (
        "मुख्य पात्र टिक्की, पीली रेनकोट पहने रोबोट-चिड़िया है। "
        "उसे बारिश शुरू होने से पहले पार्क का खोया मौसम-पंखा ढूँढकर चालू करना है, "
        "लेकिन शरारती हवा उसका नक्शा उलझा देती है।"
    ),
    (
        "मुख्य पात्र मीरा, हरे स्कार्फ वाली छोटी जादुई गिलहरी है। "
        "उसे रात होने से पहले जंगल की बुझी जुगनू-लालटेन जलानी है, "
        "लेकिन उसकी रोशनी की चाबी पतंग के साथ उड़ जाती है।"
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate an original Hindi children's short "
            "script from an analysis file."
        )
    )

    parser.add_argument(
        "video_id",
        nargs="?",
        default=DEFAULT_VIDEO_ID,
        help=(
            "Video ID used for input/output filenames "
            f"(default: {DEFAULT_VIDEO_ID})."
        ),
    )

    parser.add_argument(
        "--attempts",
        type=int,
        default=3,
        help=(
            "Maximum Ollama attempts when a response fails "
            "validation (default: 3)."
        ),
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=900,
        help="Seconds to wait for each Ollama response (default: 900).",
    )

    return parser.parse_args()


def paths_for(video_id: str) -> tuple[Path, Path]:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", video_id):
        raise ValueError(
            "video_id may contain only letters, numbers, "
            "underscores, and hyphens."
        )

    analysis_path = (
        Path("data") / "analysis" / f"{video_id}_analysis.txt"
    )

    output_path = (
        Path("data") / "scripts" / f"{video_id}_original_script.json"
    )

    return analysis_path, output_path


def load_analysis(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(
            f"Analysis file not found: {path}"
        )

    analysis = path.read_text(encoding="utf-8").strip()

    if not analysis:
        raise ValueError(
            f"Analysis file is empty: {path}"
        )

    return analysis


def story_seed_for(video_id: str) -> str:
    """Choose a repeatable original premise."""

    index = sum(map(ord, video_id)) % len(ORIGINAL_STORY_SEEDS)

    return ORIGINAL_STORY_SEEDS[index]


def build_prompt(
    story_seed: str,
    feedback: str = "",
) -> str:

    revision_note = ""

    if feedback:
        revision_note = f"""
YOUR PREVIOUS DRAFT FAILED THESE CHECKS:

{feedback}

Create a new, better story.

Do not repair it by merely changing a few words.
Change the problematic story elements while preserving
the overall quality and structure.
"""

    return f"""
You are the lead writer for a colourful, original Hindi
children's vertical short.

Write a complete 35–50 second story that is:

- safe
- visual
- funny
- innocent
- easy to understand when heard once
- suitable for children and families

The source analysis has already been reduced to safe
production traits:

- simple child-friendly pacing
- colourful visual comedy
- gentle emotional arc
- satisfying final joke
- strong visual storytelling

IMPORTANT:

Do NOT use any source plot, character, food, dialogue,
lyric, title, phrase, or sequence.

Specifically DO NOT create:

- a monkey story
- a child eating food
- sweets
- drinking
- overeating
- food consequences
- copied lyrics
- copied dialogue

Use this ORIGINAL STORY SEED as the foundation.

Keep its named main character and core goal:

{story_seed}

Before producing JSON, silently plan this cause-and-effect chain:

HOOK
->
SETUP
->
GOAL
->
PROBLEM
->
ESCALATION
->
TWIST
->
RESOLUTION
->
PUNCHLINE

Every scene must change the situation.

The main character must perform a different visible action
in every scene.

The problem must grow before the twist.

The twist must make the resolution possible.

The punchline must be a final visual joke.

Do NOT turn the punchline into a repeated moral.

========================
VISUAL CONTINUITY
========================

Keep the main character visually consistent across all scenes.

Keep consistent:

- character colours
- clothing
- accessories
- size
- personality
- environment style

Every visual must include:

1. character
2. setting
3. distinct action
4. important prop
5. emotion or camera-worthy detail

Each visual should be approximately 10–18 Hindi words.

Do NOT use vague descriptions such as:

"character is happy"

Every scene must have a genuinely different visual event.

========================
NARRATION
========================

Use natural spoken Hindi.

Each scene should contain:

- one short sentence
- approximately 6–14 Hindi words
- simple vocabulary
- child-friendly language

Narration must advance the story.

Do NOT simply describe the visual word-for-word.

Every scene must have different narration.

Scene 4 must be different from Scene 5.

Scene 5 must be different from Scene 6.

Scene 6 must be different from Scene 7.

========================
JSON REQUIREMENTS
========================

Return JSON only.

No Markdown.

No explanation.

Exactly 8 scenes.

Scene purposes must be exactly:

HOOK
SETUP
GOAL
PROBLEM
ESCALATION
TWIST
RESOLUTION
PUNCHLINE

Scene numbers must be:

1
2
3
4
5
6
7
8

Each scene duration must be between 4 and 7 seconds.

Total duration must be between 35 and 50 seconds.

The characters array must contain at least one
main-character object.

========================
OUTPUT FORMAT
========================

Return exactly this structure:

{{
  "title": "short original Hindi title",

  "hook": "Hindi hook that creates curiosity",

  "story": "one coherent Hindi summary of the complete original story",

  "characters": [
    {{
      "name": "Hindi character name",
      "description": "consistent appearance and personality"
    }}
  ],

  "scenes": [
    {{
      "scene": 1,
      "duration": 5,
      "purpose": "HOOK",
      "visual": "Hindi visual description",
      "narration": "Hindi narration"
    }},
    {{
      "scene": 2,
      "duration": 5,
      "purpose": "SETUP",
      "visual": "Hindi visual description",
      "narration": "Hindi narration"
    }},
    {{
      "scene": 3,
      "duration": 5,
      "purpose": "GOAL",
      "visual": "Hindi visual description",
      "narration": "Hindi narration"
    }},
    {{
      "scene": 4,
      "duration": 5,
      "purpose": "PROBLEM",
      "visual": "Hindi visual description",
      "narration": "Hindi narration"
    }},
    {{
      "scene": 5,
      "duration": 5,
      "purpose": "ESCALATION",
      "visual": "Hindi visual description",
      "narration": "Hindi narration"
    }},
    {{
      "scene": 6,
      "duration": 5,
      "purpose": "TWIST",
      "visual": "Hindi visual description",
      "narration": "Hindi narration"
    }},
    {{
      "scene": 7,
      "duration": 5,
      "purpose": "RESOLUTION",
      "visual": "Hindi visual description",
      "narration": "Hindi narration"
    }},
    {{
      "scene": 8,
      "duration": 5,
      "purpose": "PUNCHLINE",
      "visual": "Hindi visual description",
      "narration": "Hindi narration"
    }}
  ],

  "ending": "Hindi punchline",

  "lesson": "optional light Hindi takeaway"
}}

FINAL CHECK:

- Exactly 8 scenes.
- Every scene is different.
- Every scene moves the story forward.
- No repeated scene descriptions.
- No copied lyrics.
- No copied sentences.
- No monkey.
- No food-eating story.
- No sweets.
- No drinking.
- No overindulgence.
- No source character.
- No source plot.
- No source dialogue.
- Total duration approximately 40 seconds.
- Valid JSON only.

{revision_note}
"""


def build_repair_prompt(
    draft: str,
    error: str,
) -> str:

    return f"""
You are editing a Hindi children's-short JSON draft.

Return ONLY one complete valid JSON object.

Do not use Markdown.
Do not provide explanation.

The draft was rejected for this exact reason:

{error}

Repair the draft directly.

Preserve:

- character
- story
- eight scenes
- scene numbering
- purpose order
- 35–50 second duration

unless a change is required to fix the rejection.

Every visual and narration must remain a distinct,
natural Hindi event.

Do NOT use:

- monkey
- food eating
- sweets
- drinking
- overeating
- food consequences

IMPORTANT:

Scene 7 (RESOLUTION) must visibly show the solution working.

Scene 8 (PUNCHLINE) must introduce a NEW:

- prop
- action
- reaction
- or comic reveal

It must NOT simply show the solution again.

REJECTED DRAFT:

---
{draft}
---

Return only the repaired JSON.
"""


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
                    "temperature": 0.85,
                    "top_p": 0.9,
                    "num_predict": 2400,
                    "num_ctx": 8192,
                },
            },
            timeout=timeout,
        )

        response.raise_for_status()

    except requests.exceptions.ConnectionError as error:
        raise RuntimeError(
            "Could not connect to Ollama. "
            "Start Ollama and confirm the model exists."
        ) from error

    except requests.exceptions.Timeout as error:
        raise RuntimeError(
            "Ollama took too long to respond."
        ) from error

    except requests.exceptions.RequestException as error:
        raise RuntimeError(
            f"Ollama request failed: {error}"
        ) from error

    generated = response.json().get("response", "").strip()

    if not generated:
        raise RuntimeError(
            "Ollama returned an empty response."
        )

    # Remove accidental Markdown fences.
    generated = generated.removeprefix("```json")
    generated = generated.removeprefix("```")
    generated = generated.removesuffix("```")

    return generated.strip()


def require_string(
    data: dict[str, Any],
    field: str,
    minimum: int = 1,
) -> str:

    value = data.get(field)

    if not isinstance(value, str):
        raise ValueError(
            f"'{field}' must be a string."
        )

    value = value.strip()

    if len(value) < minimum:
        raise ValueError(
            f"'{field}' must contain at least "
            f"{minimum} characters."
        )

    return value


def word_set(text: str) -> set[str]:
    return {
        word
        for word in re.findall(
            r"[\w\u0900-\u097F]+",
            text.lower(),
        )
        if len(word) > 1
    }


def similarity(
    left: str,
    right: str,
) -> float:

    left_words = word_set(left)
    right_words = word_set(right)

    return len(left_words & right_words) / max(
        1,
        len(left_words | right_words),
    )


def validate_script(data: Any) -> float:

    if not isinstance(data, dict):
        raise ValueError(
            "Top-level JSON value must be an object."
        )

    for field, minimum in (
        ("title", 4),
        ("hook", 10),
        ("story", 40),
        ("ending", 6),
        ("lesson", 2),
    ):
        require_string(data, field, minimum)

    characters = data.get("characters")

    if (
        not isinstance(characters, list)
        or not characters
        or not isinstance(characters[0], dict)
    ):
        raise ValueError(
            "'characters' must begin with a main-character object."
        )

    require_string(
        characters[0],
        "name",
        2,
    )

    require_string(
        characters[0],
        "description",
        15,
    )

    scenes = data.get("scenes")

    if not isinstance(scenes, list):
        raise ValueError(
            "'scenes' must be a list."
        )

    if len(scenes) != 8:
        raise ValueError(
            "'scenes' must contain exactly 8 scenes."
        )

    total_duration = 0.0

    visuals: list[str] = []
    narrations: list[str] = []

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
                f"Scene numbering error: expected {index}."
            )

        expected_purpose = SCENE_PURPOSES[index - 1]

        if scene.get("purpose") != expected_purpose:
            raise ValueError(
                f"Scene {index} must have purpose "
                f"{expected_purpose}."
            )

        duration = scene.get("duration")

        if (
            not isinstance(duration, (int, float))
            or isinstance(duration, bool)
            or not 4 <= duration <= 7
        ):
            raise ValueError(
                f"Scene {index} duration must be "
                "a number from 4 to 7 seconds."
            )

        total_duration += float(duration)

        visual = require_string(
            scene,
            "visual",
            20,
        )

        narration = require_string(
            scene,
            "narration",
            12,
        )

        visuals.append(visual)
        narrations.append(narration)

    if not MIN_DURATION <= total_duration <= MAX_DURATION:
        raise ValueError(
            f"Total duration must be "
            f"{MIN_DURATION:.0f}–{MAX_DURATION:.0f} seconds, "
            f"got {total_duration:.1f}."
        )

    # Detect near-duplicate visuals.
    for left in range(len(visuals)):
        for right in range(left + 1, len(visuals)):

            score = similarity(
                visuals[left],
                visuals[right],
            )

            if score > 0.82:
                raise ValueError(
                    f"Scenes {left + 1} and {right + 1} "
                    "have overly similar visuals."
                )

    # Detect near-duplicate narration.
    for left in range(len(narrations)):
        for right in range(left + 1, len(narrations)):

            score = similarity(
                narrations[left],
                narrations[right],
            )

            if score > 0.82:
                raise ValueError(
                    f"Scenes {left + 1} and {right + 1} "
                    "have overly similar narrations."
                )

    # Source-plot safety checks.
    combined = " ".join(
        [
            data["title"],
            data["hook"],
            data["story"],
            data["ending"],
            data["lesson"],
            *visuals,
            *narrations,
        ]
    ).lower()

    banned_terms = (
        "बंदर",
        "monkey",
        "रोज़ा",
        "roza",
        "मिठाई",
        "sweet",
        "खाना खा",
        "खाना खाने",
        "eating food",
        "पीना",
        "drinking",
    )

    present = [
        term
        for term in banned_terms
        if term in combined
    ]

    if present:
        raise ValueError(
            "Draft reuses source-plot terms: "
            + ", ".join(present)
        )

    return total_duration


def main() -> None:

    args = parse_args()

    analysis_path, output_path = paths_for(
        args.video_id
    )

    if args.attempts < 1:
        raise ValueError(
            "--attempts must be at least 1."
        )

    if args.timeout < 30:
        raise ValueError(
            "--timeout must be at least 30 seconds."
        )

    print(
        f"Loading analysis: {analysis_path}"
    )

    # We intentionally load the analysis to make sure
    # the pipeline input exists.
    #
    # The detailed source analysis is NOT sent to the
    # writer because the previous model was copying
    # source details.
    load_analysis(analysis_path)

    story_seed = story_seed_for(
        args.video_id
    )

    feedback = ""
    rejected_draft = ""
    last_error = ""

    for attempt in range(
        1,
        args.attempts + 1,
    ):

        print(
            f"Generating original script with "
            f"{MODEL} "
            f"(attempt {attempt}/{args.attempts})..."
        )

        if rejected_draft:

            prompt = build_repair_prompt(
                rejected_draft,
                feedback,
            )

        else:

            prompt = build_prompt(
                story_seed,
                feedback,
            )

        raw = ask_ollama(
            prompt,
            args.timeout,
        )

        try:

            data = json.loads(raw)

            total_duration = validate_script(
                data
            )

        except json.JSONDecodeError as error:

            last_error = str(error)
            feedback = last_error
            rejected_draft = ""

            rejected_path = (
                output_path.parent
                / f"{args.video_id}_rejected_attempt_{attempt}.txt"
            )

            rejected_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            rejected_path.write_text(
                raw,
                encoding="utf-8",
            )

            print(
                f"Rejected draft saved to: "
                f"{rejected_path}"
            )

            print(
                f"Draft rejected: {last_error}"
            )

            continue

        except ValueError as error:

            last_error = str(error)
            feedback = last_error
            rejected_draft = raw

            rejected_path = (
                output_path.parent
                / f"{args.video_id}_rejected_attempt_{attempt}.json"
            )

            rejected_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            rejected_path.write_text(
                raw,
                encoding="utf-8",
            )

            print(
                f"Rejected draft saved to: "
                f"{rejected_path}"
            )

            print(
                f"Draft rejected: {last_error}"
            )

            continue

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # IMPORTANT:
        # ensure_ascii=False keeps Hindi characters
        # as real UTF-8 characters.
        output_path.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        print(
            f"Validated: 8 distinct scenes, "
            f"{total_duration:.1f} seconds."
        )

        print(
            f"Title: {data['title']}"
        )

        print(
            f"Saved to: {output_path}"
        )

        return

    raise RuntimeError(
        f"No acceptable script was generated "
        f"after {args.attempts} attempt(s). "
        f"Last issue: {last_error}"
    )


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