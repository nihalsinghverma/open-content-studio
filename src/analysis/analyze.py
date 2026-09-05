import json
import argparse
import urllib.request
from pathlib import Path


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"


def ask_ollama(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(request) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result["response"]


def load_transcript(transcript_path: str) -> str:
    path = Path(transcript_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Transcript not found: {transcript_path}"
        )

    return path.read_text(encoding="utf-8")


def analyze_transcript(transcript: str) -> str:
    prompt = f"""
You are a content strategist analyzing a video transcript.

IMPORTANT:
We are NOT trying to copy the original video.
We want to understand its structure and create ORIGINAL content
inspired by the general idea.

Analyze the transcript and provide:

1. Main topic
2. Target audience
3. Core idea/story
4. Hook
5. Narrative structure
6. Emotional elements
7. Repetition or important patterns
8. Potential visual scenes
9. What makes this content engaging
10. Three ORIGINAL short-video concepts inspired by the
   underlying idea.

Do not reproduce the original wording.

TRANSCRIPT:
----------------
{transcript}
----------------
"""

    return ask_ollama(prompt)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze a transcript for original-content production traits."
    )
    parser.add_argument(
        "video_id",
        nargs="?",
        default="JeLIYZJ3hfM",
        help="Video ID used for transcript and analysis filenames.",
    )
    args = parser.parse_args()
    transcript_path = f"data/transcripts/{args.video_id}.txt"

    print("Loading transcript...")
    transcript = load_transcript(transcript_path)

    print("Sending transcript to Ollama...")
    result = analyze_transcript(transcript)

    output_path = Path("data/analysis")
    output_path.mkdir(parents=True, exist_ok=True)

    output_file = output_path / f"{args.video_id}_analysis.txt"
    output_file.write_text(result, encoding="utf-8")

    print("\nAnalysis:\n")
    print(result)

    print(f"\nSaved to: {output_file}")


if __name__ == "__main__":
    main()
