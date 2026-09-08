import argparse
import json
from pathlib import Path


def load_visual_prompts(video_id):
    path = Path(f"data/visuals/{video_id}_visual_prompts.json")

    if not path.exists():
        raise FileNotFoundError(f"Visual prompts not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def generate_scene(video_id, scene_number):
    data = load_visual_prompts(video_id)

    scenes = data.get("scenes", [])

    scene = next(
        (s for s in scenes if s.get("scene") == scene_number),
        None
    )

    if scene is None:
        raise ValueError(f"Scene {scene_number} not found.")

    prompt = scene["image_prompt"]

    output_dir = Path("data/images")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{video_id}_scene_{scene_number:02d}_prompt.txt"

    output_file.write_text(prompt, encoding="utf-8")

    print(f"Scene {scene_number} prompt prepared.")
    print(f"Saved to: {output_file}")
    print()
    print("IMAGE PROMPT:")
    print(prompt)


def main():
    parser = argparse.ArgumentParser(
        description="Prepare image-generation prompts from visual prompts."
    )

    parser.add_argument("video_id")
    parser.add_argument("--scene", type=int, required=True)

    args = parser.parse_args()

    generate_scene(args.video_id, args.scene)


if __name__ == "__main__":
    main()
