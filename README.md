# Open Content Studio

> A local-first Python pipeline for analyzing short-form video content, extracting storytelling patterns, and generating original Hindi children's short-video scripts using a locally hosted Ollama LLM.

## Project Status

**Current stage: Script generation pipeline is working.**

The current flow is:

```text
Source Video / Audio
        ↓
Whisper Transcription
        ↓
Content Analysis
        ↓
Ollama (Qwen 2.5 7B)
        ↓
Original Script Generation
        ↓
Validated JSON Script
        ↓
Image Generator [NEXT]
        ↓
Voice / Captions / Video Assembly [PLANNED]
```

---

## 1. What This Project Does

Open Content Studio is being built as a modular AI-assisted short-video production pipeline.

The system takes an existing short-form video's audio/transcript and extracts **high-level storytelling characteristics**, such as:

- pacing
- target audience
- emotional structure
- hook style
- repetition patterns
- visual storytelling techniques
- narrative progression
- engagement patterns

Those characteristics are then used to create a **substantially different original story**.

The project is deliberately designed **not to rewrite or copy the source video**.

Generated stories use:

- new characters
- new premises
- new event sequences
- new narration
- new visuals
- new endings

The final story is stored as structured JSON so later stages can consume it automatically.

---

## 2. Technology Stack

| Component | Technology |
|---|---|
| Language | Python |
| Environment | Python `.venv` |
| Speech-to-text | Whisper |
| Local LLM runtime | Ollama |
| Current LLM | `qwen2.5:7b` |
| HTTP client | `requests` |
| Script format | JSON |
| OS | Windows |
| Shell | PowerShell / Git Bash |

---

## 3. Current Project Structure

```text
open-content-studio/
│
├── .venv/
│
├── data/
│   ├── audio/
│   │   └── <video_id>.mp3
│   │
│   ├── transcripts/
│   │   └── <video_id>.txt
│   │
│   ├── analysis/
│   │   └── <video_id>_analysis.txt
│   │
│   └── scripts/
│       ├── <video_id>_original_script.json
│       └── <video_id>_rejected_attempt_*.json
│
├── src/
│   ├── __init__.py
│   │
│   ├── transcription/
│   │   ├── __init__.py
│   │   └── transcribe.py
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   └── analyze.py
│   │
│   └── script/
│       ├── __init__.py
│       └── generate.py
│
├── README.md
└── ...
```

Additional modules will be added as the pipeline grows.

---

# 4. Pipeline

## Stage 1 — Source Audio

Source audio is stored under:

```text
data/audio/
```

Example:

```text
data/audio/JeLIYZJ3hfM.mp3
```

The video ID is used in filenames so outputs from different source videos remain associated.

---

## Stage 2 — Whisper Transcription

Whisper is used to convert the audio into timestamped text.

Example:

```powershell
python -m src.transcription.transcribe "data/audio/JeLIYZJ3hfM.mp3"
```

The transcription stage:

1. Loads Whisper.
2. Reads the audio.
3. Detects the spoken language.
4. Generates timestamped transcript segments.
5. Saves the transcript.

Output:

```text
data/transcripts/JeLIYZJ3hfM.txt
```

Example:

```text
[60.00 -> 64.10] ...
[64.38 -> 73.10] ...
[103.10 -> 113.10] ...
```

### Important observation

The source video did not have usable subtitles, so transcription is an important part of the pipeline.

Whisper can make recognition mistakes with:

- children's songs
- rhyming Hindi
- noisy audio
- unusual pronunciation
- music over speech
- low-confidence language detection

Therefore, the transcript is treated as an input signal rather than unquestionable ground truth.

---

# 5. Stage 3 — Content Analysis

The transcript is sent to the local Ollama model for analysis.

Example:

```powershell
python -m src.analysis.analyze
```

The analysis stage identifies useful storytelling characteristics, including:

- Main topic
- Target audience
- Core idea/story
- Hook
- Narrative structure
- Emotional elements
- Repetition patterns
- Potential visual scenes
- What makes the content engaging
- New short-video concepts inspired by the underlying storytelling idea

Output:

```text
data/analysis/JeLIYZJ3hfM_analysis.txt
```

The important design decision is that this analysis is used to understand **storytelling traits**, not to directly reproduce the source story.

---

# 6. Local LLM — Ollama

The project uses Ollama to run the LLM locally.

Current model:

```text
qwen2.5:7b
```

Check installed models:

```powershell
ollama list
```

The Python application communicates with Ollama through:

```text
http://localhost:11434/api/generate
```

This keeps the current generation pipeline local rather than requiring a cloud LLM API.

---

# 7. Stage 4 — Original Script Generation

The script generator reads the analysis and creates a completely new Hindi children's story.

Example:

```powershell
python -m src.script.generate JeLIYZJ3hfM --attempts 3 --timeout 900
```

The generated story is designed for:

- Hindi
- children and families
- vertical short-form video
- approximately 35–50 seconds
- colourful visuals
- simple spoken narration
- humour
- clear cause-and-effect storytelling

---

# 8. Originality Controls

A major design goal is avoiding the common failure mode where a smaller local model simply rewrites the source.

The generator explicitly tells the model not to reuse:

- source title
- source character
- source food/subject combination
- source event sequence
- original lyrics
- original sentences
- distinctive phrases
- original dialogue
- original plot

The current generator also avoids the source pattern that previously caused repetitive monkey/food stories.

Instead, it uses an independent story seed.

Examples of story-seed directions currently used include:

- a tiny cloud mechanic repairing a rainbow bell
- a robot bird searching for a lost weather fan
- a magical squirrel trying to relight a firefly lantern

This gives the model an independent creative foundation.

---

# 9. Eight-Scene Story Structure

Every generated script follows exactly eight story stages:

```text
1. HOOK
2. SETUP
3. GOAL
4. PROBLEM
5. ESCALATION
6. TWIST
7. RESOLUTION
8. PUNCHLINE
```

The intended progression is:

```text
HOOK
  ↓
SETUP
  ↓
GOAL
  ↓
PROBLEM
  ↓
ESCALATION
  ↓
TWIST
  ↓
RESOLUTION
  ↓
PUNCHLINE
```

Every scene must change the situation.

Every scene contains:

- scene number
- duration
- purpose
- visual description
- narration

This structure is especially useful because the future image/video pipeline can treat every scene as an individual production unit.

---

# 10. Script Validation

The generator validates the LLM output before saving it as a final script.

## JSON validation

The response must be valid JSON.

## Required fields

The script must contain:

```text
title
hook
story
characters
scenes
ending
lesson
```

## Character validation

At least one main character is required.

The first character must contain:

```text
name
description
```

## Scene validation

Exactly eight scenes are required.

Scene numbering must be:

```text
1 → 8
```

Purpose order must be:

```text
HOOK
SETUP
GOAL
PROBLEM
ESCALATION
TWIST
RESOLUTION
PUNCHLINE
```

## Duration validation

Each scene must be:

```text
4–7 seconds
```

Total duration must be:

```text
35–50 seconds
```

## Similarity validation

The generator compares scene text and rejects near-duplicate visuals or narration.

This helps catch local-model behaviour such as repeating the same action across several scenes.

## Source-pattern validation

The validator also blocks source-related plot terms/patterns that previously caused the model to reproduce the source concept.

---

# 11. Automatic Retry / Repair

The generator supports multiple attempts.

Example:

```powershell
python -m src.script.generate JeLIYZJ3hfM --attempts 3 --timeout 900
```

If a generated script fails validation:

1. The failed response is saved.
2. The validation error is captured.
3. The model receives the failure feedback.
4. A new draft is generated.
5. The new draft is validated again.

Rejected drafts are stored under:

```text
data/scripts/
```

For example:

```text
JeLIYZJ3hfM_rejected_attempt_1.json
```

This makes the pipeline easier to debug and prevents invalid output from entering later stages.

---

# 12. Final Script Output

A successful run produces:

```text
data/scripts/JeLIYZJ3hfM_original_script.json
```

The JSON has this general structure:

```json
{
  "title": "...",
  "hook": "...",
  "story": "...",
  "characters": [
    {
      "name": "...",
      "description": "..."
    }
  ],
  "scenes": [
    {
      "scene": 1,
      "duration": 5,
      "purpose": "HOOK",
      "visual": "...",
      "narration": "..."
    }
  ],
  "ending": "...",
  "lesson": "..."
}
```

There are exactly eight scene objects in the final output.

---

# 13. Example Successful Run

A successful generation currently looks like:

```text
Loading analysis: data/analysis/JeLIYZJ3hfM_analysis.txt
Generating original script with qwen2.5:7b (attempt 1/3)...
Validated: 8 distinct scenes, 40.0 seconds.
Title: ...
Saved to: data/scripts/JeLIYZJ3hfM_original_script.json
```

This confirms that the current script-generation stage is functioning end-to-end.

---

# 14. Why JSON?

JSON is being used as the interface between pipeline stages.

Instead of passing large blocks of unstructured text between programs, each stage can consume structured information.

Conceptually:

```text
Script JSON
    │
    ├── title
    ├── character
    ├── scene 1
    │     ├── visual
    │     └── narration
    ├── scene 2
    │     ├── visual
    │     └── narration
    └── ...
```

This will later allow automatic generation of:

- scene images
- animation/video prompts
- voice-over
- subtitles
- thumbnails
- final video timelines

---

# 15. Current Design Philosophy

## Local-first

The current LLM runs locally through Ollama.

## Modular

Each major task has its own Python module:

```text
transcription
analysis
script generation
image generation
video generation
audio
editing
export
```

## Structured

Intermediate outputs are saved to disk so each pipeline stage can be inspected independently.

## Automated

The eventual goal is:

```text
Input video
     ↓
Automatic analysis
     ↓
Original story
     ↓
Scene assets
     ↓
Voice
     ↓
Captions
     ↓
Final vertical video
```

---

# 16. Completed So Far

- [x] Python project environment
- [x] `.venv`
- [x] `src` package structure
- [x] Whisper transcription module
- [x] Timestamped transcript output
- [x] Ollama integration
- [x] Local Qwen model
- [x] Content analysis module
- [x] Analysis output storage
- [x] Original script generator
- [x] Structured JSON output
- [x] Eight-scene story structure
- [x] Duration validation
- [x] Scene uniqueness validation
- [x] Source-pattern/originality checks
- [x] Automatic retry mechanism
- [x] Rejected-draft debugging files

---

# 17. Next Major Stage — Image Generation

The next component will consume:

```text
data/scripts/<video_id>_original_script.json
```

and convert each scene's visual description into production-ready visual prompts.

Conceptually:

```text
Scene JSON
    ↓
Image Prompt Builder
    ↓
Image Generation Model
    ↓
Scene Image
```

The biggest technical requirement will be **character consistency**.

If the character is introduced as:

> a small magical squirrel wearing a green scarf

then that character should look consistent across all eight scenes.

The image-generation stage therefore needs to handle:

- character reference
- consistent appearance
- environment continuity
- scene-specific action
- camera composition
- vertical 9:16 framing
- child-friendly visual style

---

# 18. Planned Image Output

A likely future structure:

```text
data/
└── images/
    └── <video_id>/
        ├── character_reference.png
        ├── scene_01.png
        ├── scene_02.png
        ├── scene_03.png
        ├── scene_04.png
        ├── scene_05.png
        ├── scene_06.png
        ├── scene_07.png
        └── scene_08.png
```

The exact structure may change as the image pipeline is implemented.

---

# 19. Planned Video Pipeline

After image generation:

```text
Script JSON
    ↓
Character Reference
    ↓
8 Scene Images
    ↓
Animation / Image-to-Video
    ↓
Voice-over
    ↓
Captions
    ↓
Music / SFX
    ↓
Timeline Assembly
    ↓
Final 9:16 MP4
```

Possible video techniques:

- image-to-video generation
- camera movement
- zoom/pan
- transitions
- scene timing
- sound effects
- background music
- voice synchronization

The first implementation should remain simple and deterministic before adding advanced generative video.

---

# 20. Planned Voice-over

The script already contains scene-level Hindi narration.

This allows:

```text
Scene narration
      ↓
Hindi TTS
      ↓
Scene audio
      ↓
Timeline synchronization
```

Eventually, each scene can have its own audio segment so timing can be adjusted independently.

---

# 21. Planned Captions

The final video should support Hindi captions/subtitles.

The existing scene-level structure gives us approximate timing.

Future caption generation can use:

```text
scene duration
+
scene narration
```

to create formats such as:

```text
SRT
ASS
```

---

# 22. Planned GitHub Portfolio

This project is also intended to become a strong portfolio project.

It can demonstrate:

- Python engineering
- modular architecture
- local LLM integration
- speech-to-text
- prompt engineering
- structured generation
- validation
- automated retry logic
- generative AI
- multimedia processing
- reproducible pipelines

The development history should also show progressive milestones through Git commits.

Suggested milestones:

```text
Initial project structure
Add Whisper transcription
Add Ollama analysis
Add original script generation
Add JSON validation
Add automatic script repair
Add image generation
Add voice generation
Add video assembly
```

---

# 23. Git Workflow

Typical workflow:

```powershell
git status
git add .
git commit -m "Build script generation pipeline"
git push
```

The README should evolve together with the project.

---

# 24. Development Notes

The project is currently being developed on Windows using a Python virtual environment.

Activate it with:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run Python modules from the project root using:

```powershell
python -m <module>
```

Examples:

```powershell
python -m src.transcription.transcribe ...
python -m src.analysis.analyze
python -m src.script.generate ...
```

Using `python -m` is intentional because it lets Python resolve the `src` package correctly from the project root.

---

# 25. Troubleshooting

## `ModuleNotFoundError: No module named 'src.transcription'`

Make sure you are in:

```text
open-content-studio/
```

and that this structure exists:

```text
src/
├── __init__.py
└── transcription/
    ├── __init__.py
    └── transcribe.py
```

Then run:

```powershell
python -m src.transcription.transcribe ...
```

---

## `IndentationError`

If Python reports:

```text
IndentationError: unexpected indent
```

check for accidental spaces before top-level statements.

A module should normally start like:

```python
"""Module description."""

from __future__ import annotations
```

---

## `NameError: name 'analysis' is not defined`

If an f-string contains:

```python
{analysis}
```

Python expects a Python variable named `analysis`.

The current generator avoids this problem by loading the analysis file explicitly and controlling what is inserted into the prompt.

---

## Ollama connection error

Check that Ollama is running:

```powershell
ollama list
```

and that the model exists:

```text
qwen2.5:7b
```

---

# 26. Important Architecture Decision

The analysis stage and script-generation stage are deliberately separated.

Instead of:

```text
source transcript
      ↓
"rewrite this video"
```

the pipeline does:

```text
source transcript
      ↓
abstract storytelling analysis
      ↓
independent original premise
      ↓
new story
```

This reduces the tendency of a smaller local model to reproduce the source plot.

The generated script is then passed through deterministic Python validation.

---

# 27. Current Limitations

The system is functional but not production-complete.

Known limitations:

- Whisper transcription can contain Hindi recognition errors.
- Small local models can produce awkward Hindi.
- Story quality can vary between generations.
- Valid JSON does not guarantee creative quality.
- Text similarity checks are useful but are not a complete originality detector.
- Character consistency has not yet been solved for image generation.
- Image generation is not implemented yet.
- Video generation is not implemented yet.
- Hindi voice generation is not implemented yet.
- Caption generation is not implemented yet.
- Final video assembly is not implemented yet.
- Automated quality scoring will likely be needed later.

These are planned engineering stages, not failures of the current pipeline.

---

# 28. Roadmap

## Phase 1 — Content Understanding

- [x] Audio input
- [x] Whisper transcription
- [x] Content analysis
- [x] Local Ollama integration

## Phase 2 — Story Generation

- [x] Original story generation
- [x] Eight-scene structure
- [x] JSON output
- [x] Validation
- [x] Retry/repair mechanism

## Phase 3 — Visual Generation

- [ ] Character reference generation
- [ ] Scene image prompts
- [ ] Image generation
- [ ] Character consistency
- [ ] Vertical 9:16 assets

## Phase 4 — Audio

- [ ] Hindi TTS
- [ ] Voice selection
- [ ] Scene-level audio
- [ ] Sound effects
- [ ] Background music

## Phase 5 — Video

- [ ] Scene animation
- [ ] Timeline creation
- [ ] Captions
- [ ] Transitions
- [ ] Final MP4 rendering

## Phase 6 — Automation

- [ ] Single command for complete pipeline
- [ ] Batch processing
- [ ] Asset management
- [ ] Quality scoring
- [ ] Failure recovery
- [ ] Metadata generation

---

# 29. Long-Term Goal

The eventual goal is an end-to-end **AI-assisted short-video production studio**.

A future command could look like:

```powershell
python -m src.pipeline.run <video_id>
```

and produce:

```text
analysis
   ↓
original story
   ↓
character reference
   ↓
8 scene images
   ↓
voice-over
   ↓
captions
   ↓
music/SFX
   ↓
final vertical video
```

Each stage should remain independently testable.

---

# 30. Current Milestone

### Milestone achieved

> A source video's audio can be transcribed, analyzed locally, and transformed into a validated, original, structured Hindi children's story.

### Next milestone

> Build the image-generation stage that consumes the validated script JSON and produces consistent visual assets for all eight scenes.

---

## License

License details will be added when the GitHub repository structure is finalized.

## Disclaimer

This project is intended for creating original content inspired by high-level storytelling characteristics. Source material should not be copied, reproduced, or used in a way that violates copyright or other applicable rights.
