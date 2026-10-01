#!/usr/bin/env python3
"""Generate continuous narration through Armada's internal Vox/F5 rail."""

from __future__ import annotations

import argparse
from array import array
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import urllib.request
import wave

MAX_SEGMENT_CHARS = 220
MAX_SEGMENT_SENTENCES = 4
JOIN_SILENCE_SECONDS = 0.16
EDGE_SILENCE_SECONDS = 0.08
VOICE_THRESHOLD = 260


def segments(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
    result: list[str] = []
    current = ""
    sentence_count = 0
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip()
        if current and (
            len(candidate) > MAX_SEGMENT_CHARS
            or sentence_count >= MAX_SEGMENT_SENTENCES
        ):
            result.append(current)
            current = sentence
            sentence_count = 1
        else:
            current = candidate
            sentence_count += 1
    if current:
        result.append(current)
    return result


def generate_vox(
    text: str,
    voice: str,
    speed: float,
    owner: str,
    quality: str,
    endpoint: str,
    token: str,
    target: Path,
) -> None:
    payload = {
        "text": text,
        "voice_ref": voice,
        "persona": voice,
        "owner": owner,
        "quality": quality,
        "rate": speed,
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Vox-Proxy-Token": token,
            "X-Vox-User": owner,
        },
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        audio = response.read()
    if not audio.startswith(b"RIFF"):
        raise RuntimeError("internal Vox/F5 rail returned non-WAV data")
    pending = target.with_suffix(".pending.wav")
    pending.write_bytes(audio)
    pending.replace(target)


def generate_edge(
    text: str, voice: str, speed: float, edge_cli: str, target: Path
) -> None:
    """Render one unit with a licensed stock Microsoft neural voice."""
    media = target.with_suffix(".pending.mp3")
    rate = round((speed - 1.0) * 100)
    subprocess.run(
        [
            edge_cli,
            "--voice", voice,
            f"--rate={rate:+d}%",
            "--text", text,
            "--write-media", str(media),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    try:
        import imageio_ffmpeg

        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        pending = target.with_suffix(".pending.wav")
        subprocess.run(
            [
                ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(media), "-ac", "1", "-ar", "24000", str(pending),
            ],
            check=True,
        )
        pending.replace(target)
    finally:
        media.unlink(missing_ok=True)


def voiced_bounds(samples: array, rate: int) -> tuple[int, int]:
    window = max(1, rate // 100)
    active = [
        index
        for index in range(0, len(samples), window)
        if max((abs(value) for value in samples[index:index + window]), default=0)
        >= VOICE_THRESHOLD
    ]
    if not active:
        raise RuntimeError("generated segment contains no detectable speech")
    edge = int(rate * EDGE_SILENCE_SECONDS)
    return max(0, active[0] - edge), min(len(samples), active[-1] + window + edge)


def valid_wav(path: Path) -> bool:
    try:
        with wave.open(str(path), "rb") as source:
            samples = array("h", source.readframes(source.getnframes()))
            voiced_bounds(samples, source.getframerate())
        return True
    except (EOFError, OSError, RuntimeError, wave.Error):
        return False


def join(parts: list[Path], target: Path) -> float:
    combined = array("h")
    params = None
    rate = 0
    for index, part in enumerate(parts):
        with wave.open(str(part), "rb") as source:
            if source.getnchannels() != 1 or source.getsampwidth() != 2:
                raise RuntimeError(f"unexpected WAV format in {part}")
            current = (source.getnchannels(), source.getsampwidth(), source.getframerate())
            if params is None:
                params, rate = current, source.getframerate()
            elif current != params:
                raise RuntimeError(f"inconsistent WAV format in {part}")
            samples = array("h", source.readframes(source.getnframes()))
        start, end = voiced_bounds(samples, rate)
        if index:
            combined.extend([0] * int(rate * JOIN_SILENCE_SECONDS))
        combined.extend(samples[start:end])
    target.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(target), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(combined.tobytes())
    return len(combined) / rate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", type=Path, default=Path("scripts/demo_narration.txt"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--voice", default="en-US-BrianMultilingualNeural")
    parser.add_argument("--owner", default="robin")
    parser.add_argument("--speed", type=float, default=1.04)
    parser.add_argument("--quality", choices=("fast", "good", "best"), default="fast")
    parser.add_argument("--endpoint", default=os.environ.get("TURNPROOF_VOX_URL"))
    parser.add_argument("--engine", choices=("edge", "vox"), default="edge")
    parser.add_argument("--edge-cli", default=shutil.which("edge-tts"))
    args = parser.parse_args()
    token = None
    if args.engine == "vox":
        if not args.endpoint:
            parser.error("--endpoint or TURNPROOF_VOX_URL is required for Vox")
        token = os.environ.get("VOX_PROXY_TOKEN")
        if not token:
            try:
                from devlathe.core.credential_resolver import require

                token = require("VOX_PROXY_TOKEN")
            except (ImportError, RuntimeError) as error:
                parser.error(f"VOX_PROXY_TOKEN is unavailable: {error}")
    elif not args.edge_cli:
        parser.error("edge-tts was not found; pass --edge-cli")

    parts_dir = args.output.parent / f".{args.output.stem}-parts"
    parts_dir.mkdir(parents=True, exist_ok=True)
    chunks = segments(args.script.read_text())
    parts: list[Path] = []
    for index, text in enumerate(chunks):
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:12]
        part = parts_dir / f"part-{index:02d}-{text_hash}.wav"
        if valid_wav(part):
            print(f"reused {index + 1}/{len(chunks)}: {len(text)} characters", flush=True)
            parts.append(part)
            continue
        print(f"rendering {index + 1}/{len(chunks)}: {len(text)} characters", flush=True)
        if args.engine == "vox":
            generate_vox(
                text, args.voice, args.speed, args.owner, args.quality,
                args.endpoint, token, part,
            )
        else:
            generate_edge(text, args.voice, args.speed, args.edge_cli, part)
        parts.append(part)
        print(f"generated {index + 1}/{len(chunks)}", flush=True)
    duration = join(parts, args.output)
    receipt = {
        "engine": "stock_edge_neural" if args.engine == "edge" else "internal_vox_f5",
        "voice": args.voice,
        "owner": args.owner,
        "quality": args.quality,
        "speed": args.speed,
        "join_silence_seconds": JOIN_SILENCE_SECONDS,
        "edge_silence_seconds": EDGE_SILENCE_SECONDS,
        "duration_seconds": round(duration, 3),
        "output_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
        "segments": [
            {
                "index": index,
                "text": text,
                "characters": len(text),
                "sha256": hashlib.sha256(parts[index].read_bytes()).hexdigest(),
            }
            for index, text in enumerate(chunks)
        ],
    }
    args.output.with_suffix(".json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"joined {len(parts)} segments into {args.output} ({duration:.2f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
