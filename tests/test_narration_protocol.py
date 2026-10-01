from array import array
from pathlib import Path
import sys
import wave


sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from generate_narration import MAX_SEGMENT_CHARS, segments, valid_wav  # noqa: E402


def write_wav(path: Path, samples: array, rate: int = 24_000) -> None:
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(samples.tobytes())


def test_segments_preserve_sentence_order_and_stay_bounded():
    script = "One short sentence. A second sentence follows. " + "x" * 180 + ". Final line."
    chunks = segments(script)
    assert " ".join(chunks) == script
    assert all(len(chunk) <= MAX_SEGMENT_CHARS for chunk in chunks)


def test_wav_validation_requires_detectable_speech(tmp_path):
    silent = tmp_path / "silent.wav"
    voiced = tmp_path / "voiced.wav"
    write_wav(silent, array("h", [0] * 24_000))
    write_wav(voiced, array("h", [0] * 2_400 + [1_000] * 4_800 + [0] * 2_400))
    assert valid_wav(silent) is False
    assert valid_wav(voiced) is True
