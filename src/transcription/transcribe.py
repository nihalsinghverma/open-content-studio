from pathlib import Path
import sys

from faster_whisper import WhisperModel


def transcribe_audio(audio_path: str, model_size: str = "small"):
    audio_file = Path(audio_path)

    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_file}")

    output_dir = Path("data/transcripts")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{audio_file.stem}.txt"

    print(f"Loading Whisper model: {model_size}")
    
    model = WhisperModel(
        model_size,
        device="cpu",
        compute_type="int8",
    )

    print(f"Transcribing: {audio_file}")

    segments, info = model.transcribe(
        str(audio_file),
        beam_size=5,
    )

    print(f"Detected language: {info.language}")
    print(f"Language probability: {info.language_probability:.2f}")

    with open(output_file, "w", encoding="utf-8") as f:
        for segment in segments:
            text = segment.text.strip()

            if not text:
                continue

            line = f"[{segment.start:.2f} -> {segment.end:.2f}] {text}"

            print(line)
            f.write(line + "\n")

    print()
    print(f"Transcript saved to: {output_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print(
            'python -m src.transcription.transcribe '
            '"data/audio/example.mp3"'
        )
        sys.exit(1)

    audio_path = sys.argv[1]

    model_size = sys.argv[2] if len(sys.argv) > 2 else "small"

    transcribe_audio(audio_path, model_size)