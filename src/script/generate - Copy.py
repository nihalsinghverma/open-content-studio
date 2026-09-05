"""Generate an original Hindi children's script from a video analysis.

Usage: python -m src.script.generate JeLIYZJ3hfM
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
MIN_DURATION, MAX_DURATION = 35.0, 50.0
SCENE_PURPOSES = [
    "HOOK", "SETUP", "GOAL", "PROBLEM",
    "ESCALATION", "TWIST", "RESOLUTION", "PUNCHLINE",
]
ORIGINAL_STORY_SEEDS = (
    "मुख्य पात्र गुग्गू, बैंगनी टोपी पहनने वाला नन्हा बादल-मिस्त्री है। उसे सूर्यास्त से पहले "
    "पहाड़ी गाँव की इंद्रधनुषी घंटी ठीक करनी है, लेकिन हवा उसके चमकते पेंच उड़ा देती है।",
    "मुख्य पात्र टिक्की, पीली रेनकोट पहने रोबोट-चिड़िया है। उसे बारिश शुरू होने से पहले "
    "पार्क का खोया मौसम-पंखा ढूँढकर चालू करना है, लेकिन शरारती हवा उसके नक्शे को उलझा देती है।",
    "मुख्य पात्र मीरा, हरे स्कार्फ वाली छोटी जादुई गिलहरी है। उसे रात होने से पहले "
    "जंगल की बुझी जुगनू-लालटेन जलानी है, लेकिन उसकी रोशनी की चाबी पतंग के साथ उड़ जाती है।",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an original Hindi children's short script from an analysis file."
    )
    parser.add_argument(
        "video_id", nargs="?", default=DEFAULT_VIDEO_ID,
        help=f"Video ID used for input/output filenames (default: {DEFAULT_VIDEO_ID}).",
    )
    parser.add_argument(
        "--attempts", type=int, default=3,
        help="Maximum Ollama attempts when a response fails validation (default: 3).",
    )
    parser.add_argument(
        "--timeout", type=int, default=900,
        help="Seconds to wait for each Ollama response (default: 900).",
    )
    return parser.parse_args()


def paths_for(video_id: str) -> tuple[Path, Path]:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", video_id):
        raise ValueError("video_id may contain only letters, numbers, underscores, and hyphens.")
    return (
        Path("data/analysis") / f"{video_id}_analysis.txt",
        Path("data/scripts") / f"{video_id}_original_script.json",
    )


def load_analysis(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Analysis file not found: {path}")
    analysis = path.read_text(encoding="utf-8").strip()
    if not analysis:
        raise ValueError(f"Analysis file is empty: {path}")
    return analysis


def story_seed_for(video_id: str) -> str:
    """Choose a repeatable original premise without exposing source plot details."""
    return ORIGINAL_STORY_SEEDS[sum(map(ord, video_id)) % len(ORIGINAL_STORY_SEEDS)]


def build_prompt(story_seed: str, feedback: str = "") -> str:
    revision_note = ""
    if feedback:
        revision_note = f"""
YOUR PREVIOUS DRAFT FAILED THESE CHECKS:
{feedback}
Create a new, better story. Do not repair it by merely changing a few words.
"""
    return f"""
You are the lead writer for a colourful, original Hindi children's vertical short.
Write a complete 35–50 second story that is safe, visual, funny, and easy to
understand when heard once.

The source analysis has already been reduced to these safe production traits:
simple child-friendly pacing, colourful visual comedy, a gentle emotional arc,
and a satisfying final joke. Do NOT use any source plot, character, food,
dialogue, lyric, title, or phrase. Specifically, do not make a monkey, a child
eating food, sweets, drinking, overindulgence, or a food-consequence story.

Use this ORIGINAL STORY SEED as the foundation. Keep its named main character
and core goal; invent fresh scene actions that follow it:
{story_seed}

Before writing JSON, silently plan one cause-and-effect chain:
HOOK -> SETUP -> GOAL -> PROBLEM -> ESCALATION -> TWIST -> RESOLUTION -> PUNCHLINE.
Every scene must change the situation. The main character must do a different,
visible action in every scene. The problem must grow before the twist; the
twist must make the resolution possible; the punchline must be a final visual
joke, not a moral repeated from the narration.

Visual continuity rules:
- Keep the named main character's colours, clothing/accessory, size, and
  setting consistent unless the story itself changes them.
- Each visual must state: character, setting, distinct action, key prop, and
  emotion/camera-worthy detail. Write 10–18 Hindi words per visual.
- Do not use vague visuals such as "character is happy" or repeat a visual.

Narration rules:
- Natural, spoken Hindi for children; one short sentence per scene (6–14 words).
- Narration must describe or advance that scene, not repeat the visual word for word.
- Give each narration a distinct sentence and event. Avoid awkward, literal,
  or ungrammatical Hindi.

JSON rules:
- Return JSON only, with no Markdown or commentary.
- Exactly eight scenes, numbered 1 through 8.
- Use purposes exactly in this order: {", ".join(SCENE_PURPOSES)}.
- Use durations of 4–7 seconds whose total is 35–50 seconds.
- `characters` contains a main-character object with `name` and `description`.

{revision_note}
Return exactly this JSON shape:
{{
  "title": "short original Hindi title",
  "hook": "Hindi hook that creates curiosity",
  "story": "one coherent Hindi summary of the complete original story",
  "characters": [{{"name": "Hindi name", "description": "consistent appearance and personality"}}],
  "scenes": [
    {{"scene": 1, "duration": 5, "purpose": "HOOK", "visual": "Hindi visual", "narration": "Hindi narration"}},
    {{"scene": 2, "duration": 5, "purpose": "SETUP", "visual": "Hindi visual", "narration": "Hindi narration"}},
    {{"scene": 3, "duration": 5, "purpose": "GOAL", "visual": "Hindi visual", "narration": "Hindi narration"}},
    {{"scene": 4, "duration": 5, "purpose": "PROBLEM", "visual": "Hindi visual", "narration": "Hindi narration"}},
    {{"scene": 5, "duration": 5, "purpose": "ESCALATION", "visual": "Hindi visual", "narration": "Hindi narration"}},
    {{"scene": 6, "duration": 5, "purpose": "TWIST", "visual": "Hindi visual", "narration": "Hindi narration"}},
    {{"scene": 7, "duration": 5, "purpose": "RESOLUTION", "visual": "Hindi visual", "narration": "Hindi narration"}},
    {{"scene": 8, "duration": 5, "purpose": "PUNCHLINE", "visual": "Hindi visual", "narration": "Hindi narration"}}
  ],
  "ending": "Hindi punchline",
  "lesson": "optional, light Hindi takeaway"
}}
"""


def build_repair_prompt(draft: str, error: str) -> str:
    """Ask the model to repair a valid-but-rejected JSON draft, not restart it."""
    return f"""
You are editing a Hindi children's-short JSON draft. Return ONLY one complete,
valid JSON object—no Markdown or explanation.

The draft was rejected for this exact reason:
{error}

Repair the draft directly. Preserve its coherent character, story, eight-scene
shape, scene numbering, purpose order, and 35–50 second duration unless a
change is needed to fix the rejection. Make the smallest meaningful rewrite
that fixes the issue. Every visual and narration must remain a distinct,
natural Hindi event. Do not use monkey, food-eating, sweets, drinking, or
overindulgence plots.

Scene 7 (RESOLUTION) must visibly show the solution working. Scene 8
(PUNCHLINE) must then introduce a NEW prop, action, reaction, or comic reveal;
it must not simply show the solution again with a different sentence.

REJECTED DRAFT:
---
{draft}
---
"""


def ask_ollama(prompt: str, timeout: int) -> str:
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL, "prompt": prompt, "stream": False, "format": "json",
                # Eight short scenes need a bounded response. This avoids a slow
                # CPU-hosted model continuing to elaborate after the JSON is complete.
                "options": {
                    "temperature": 0.85,
                    "top_p": 0.9,
                    "num_predict": 2400,
                    # A repair includes the prior JSON as input as well as a
                    # complete replacement as output; 4096 tokens can truncate it.
                    "num_ctx": 8192,
                },
            },
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError as error:
        raise RuntimeError("Could not connect to Ollama. Start Ollama and confirm the model exists.") from error
    except requests.exceptions.Timeout as error:
        raise RuntimeError("Ollama took too long to respond.") from error
    except requests.exceptions.RequestException as error:
        raise RuntimeError(f"Ollama request failed: {error}") from error

    generated = response.json().get("response", "").strip()
    if not generated:
        raise RuntimeError("Ollama returned an empty response.")
    return generated.removeprefix("```json").removeprefix("```").removesuffix("```").strip()


def require_string(data: dict[str, Any], field: str, minimum: int = 1) -> str:
    value = data.get(field)
    if not isinstance(value, str) or len(value.strip()) < minimum:
        raise ValueError(f"'{field}' must be a string of at least {minimum} characters.")
    return value.strip()


def word_set(text: str) -> set[str]:
    return {word for word in re.findall(r"[\w\u0900-\u097F]+", text.lower()) if len(word) > 1}


def similarity(left: str, right: str) -> float:
    left_words, right_words = word_set(left), word_set(right)
    return len(left_words & right_words) / max(1, len(left_words | right_words))


def validate_script(data: Any) -> float:
    if not isinstance(data, dict):
        raise ValueError("Top-level JSON value must be an object.")
    for field, minimum in (
        ("title", 4), ("hook", 10), ("story", 40), ("ending", 6), ("lesson", 2)
    ):
        require_string(data, field, minimum)

    characters = data.get("characters")
    if not isinstance(characters, list) or not characters or not isinstance(characters[0], dict):
        raise ValueError("'characters' must begin with a main-character object.")
    require_string(characters[0], "name", 2)
    require_string(characters[0], "description", 15)

    scenes = data.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != 8:
        raise ValueError("'scenes' must be a list of exactly 8 scenes.")

    total_duration = 0.0
    visuals, narrations = [], []
    for index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            raise ValueError(f"Scene {index} must be an object.")
        if scene.get("scene") != index:
            raise ValueError(f"Scene numbering error: expected {index}.")
        if scene.get("purpose") != SCENE_PURPOSES[index - 1]:
            raise ValueError(f"Scene {index} must have purpose {SCENE_PURPOSES[index - 1]}.")
        duration = scene.get("duration")
        if not isinstance(duration, (int, float)) or isinstance(duration, bool) or not 4 <= duration <= 7:
            raise ValueError(f"Scene {index} duration must be a number from 4 to 7 seconds.")
        total_duration += float(duration)
        visuals.append(require_string(scene, "visual", 20))
        narrations.append(require_string(scene, "narration", 12))

    if not MIN_DURATION <= total_duration <= MAX_DURATION:
        raise ValueError(
            f"Total duration must be {MIN_DURATION:.0f}–{MAX_DURATION:.0f} seconds, got {total_duration:.1f}."
        )
    for label, texts in (("visual", visuals), ("narration", narrations)):
        for left in range(len(texts)):
            for right in range(left + 1, len(texts)):
                # Scenes naturally share a named character and setting. Flag
                # near-duplicates, not ordinary story continuity.
                if similarity(texts[left], texts[right]) > 0.82:
                    raise ValueError(f"Scenes {left + 1} and {right + 1} have overly similar {label}s.")

    combined = " ".join([data["title"], data["story"], *visuals, *narrations]).lower()
    banned = ("बंदर", "monkey", "रोज़ा", "roza", "मिठाई", "sweet", "खाना खा", "eating food")
    present = [term for term in banned if term in combined]
    if present:
        raise ValueError("Draft reuses source-plot terms: " + ", ".join(present))
    return total_duration


def main() -> None:
    args = parse_args()
    analysis_path, output_path = paths_for(args.video_id)
    if args.attempts < 1:
        raise ValueError("--attempts must be at least 1.")
    if args.timeout < 30:
        raise ValueError("--timeout must be at least 30 seconds.")
    print(f"Loading analysis: {analysis_path}")
    # Load and verify the analysis file as a pipeline input, but do not send
    # source plot details to the writer: that caused the local model to copy it.
    load_analysis(analysis_path)
    story_seed = story_seed_for(args.video_id)
    feedback = ""
    rejected_draft = ""
    last_error = ""
    for attempt in range(1, args.attempts + 1):
        print(f"Generating original script with {MODEL} (attempt {attempt}/{args.attempts})...")
        prompt = (
            build_repair_prompt(rejected_draft, feedback)
            if rejected_draft
            else build_prompt(story_seed, feedback)
        )
        raw = ask_ollama(prompt, args.timeout)
        try:
            data = json.loads(raw)
            total_duration = validate_script(data)
        except json.JSONDecodeError as error:
            last_error = str(error)
            feedback = last_error
            rejected_draft = ""
            rejected_path = output_path.parent / f"{args.video_id}_rejected_attempt_{attempt}.txt"
            rejected_path.parent.mkdir(parents=True, exist_ok=True)
            rejected_path.write_text(raw, encoding="utf-8")
            print(f"Rejected draft saved to: {rejected_path}")
            print(f"Draft rejected: {last_error}")
            continue
        except ValueError as error:
            last_error = str(error)
            feedback = last_error
            rejected_draft = raw
            rejected_path = output_path.parent / f"{args.video_id}_rejected_attempt_{attempt}.json"
            rejected_path.parent.mkdir(parents=True, exist_ok=True)
            rejected_path.write_text(raw, encoding="utf-8")
            print(f"Rejected draft saved to: {rejected_path}")
            print(f"Draft rejected: {last_error}")
            continue
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Validated: 8 distinct scenes, {total_duration:.1f} seconds.")
        print(f"Title: {data['title']}")
        print(f"Saved to: {output_path}")
        return
    raise RuntimeError(
        f"No acceptable script was generated after {args.attempts} attempt(s). Last issue: {last_error}"
    )


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
