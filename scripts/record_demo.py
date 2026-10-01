#!/usr/bin/env python3
"""Capture the paced Turnproof browser demo through Chrome DevTools.

The script expects Chromium to be running with remote debugging on port 9222
and the Turnproof server to be available on port 8765. It records deterministic
viewport frames and encodes them with the supplied narration using the bundled
imageio-ffmpeg binary.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

import imageio_ffmpeg
import websockets


async def capture_frames(endpoint: str, target: Path, seconds: float, fps: int, url: str) -> int:
    with urllib.request.urlopen(f"{endpoint}/json", timeout=10) as response:
        pages = json.load(response)
    page = next(item for item in pages if item.get("type") == "page")
    target.mkdir(parents=True, exist_ok=True)
    request_id = 0

    async with websockets.connect(page["webSocketDebuggerUrl"], max_size=4_000_000) as socket:
        async def command(method: str, params: dict | None = None) -> dict:
            nonlocal request_id
            request_id += 1
            own_id = request_id
            await socket.send(json.dumps({"id": own_id, "method": method, "params": params or {}}))
            while True:
                message = json.loads(await socket.recv())
                if message.get("id") == own_id:
                    if "error" in message:
                        raise RuntimeError(message["error"])
                    return message.get("result", {})

        await command("Page.enable")
        await command("Emulation.setDeviceMetricsOverride", {
            "width": 1440, "height": 960, "deviceScaleFactor": 1, "mobile": False,
        })
        await command("Page.navigate", {"url": url})
        await asyncio.sleep(0.5)
        interval = 1 / fps
        started = time.monotonic()
        frame = 0
        while time.monotonic() - started < seconds:
            due = started + frame * interval
            await asyncio.sleep(max(0, due - time.monotonic()))
            result = await command("Page.captureScreenshot", {
                "format": "jpeg", "quality": 88, "fromSurface": True,
                "captureBeyondViewport": False,
            })
            (target / f"frame-{frame:04d}.jpg").write_bytes(base64.b64decode(result["data"]))
            frame += 1
        return frame


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--narration", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=68)
    parser.add_argument("--fps", type=int, default=2)
    parser.add_argument("--endpoint", default="http://127.0.0.1:9222")
    parser.add_argument("--url", default="http://127.0.0.1:8765/?video=1")
    args = parser.parse_args()

    frames = Path(tempfile.mkdtemp(prefix="turnproof-video-frames-"))
    try:
        count = asyncio.run(capture_frames(args.endpoint, frames, args.seconds, args.fps, args.url))
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            ffmpeg, "-y", "-framerate", str(args.fps),
            "-i", str(frames / "frame-%04d.jpg"),
            "-i", str(args.narration),
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
            "-shortest", "-movflags", "+faststart", str(args.output),
        ], check=True)
        print(f"Captured {count} frames -> {args.output}")
        return 0
    finally:
        shutil.rmtree(frames, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
