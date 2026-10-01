# Narration assembly protocol

Turnproof's demo narration is rendered as bounded units instead of one opaque
text-to-speech request. This prevents a long request from timing out and avoids
the uneven pauses produced by paragraph-level synthesis.

1. Normalize the script and split only at sentence boundaries.
2. Pack adjacent sentences up to 220 characters and four sentences per unit.
3. Render every unit with the same voice, owner, quality tier, and speaking rate.
4. Write each response atomically and require a mono, 16-bit WAV containing
   detectable speech.
5. Measure the first and last voiced sample. Retain 80 milliseconds of edge air
   and place a fixed 160-millisecond breath between units.
6. Cache each proven unit by its text hash so an interrupted run resumes without
   changing completed audio.
7. Emit a JSON receipt containing the render settings and SHA-256 hashes for
   every unit and the assembled narration.
8. Run silence detection over the result before timing or recording the visual
   demonstration.

The implementation is [`scripts/generate_narration.py`](../scripts/generate_narration.py).
Its default renderer is a licensed stock Microsoft neural voice supplied by
`edge-tts`. An internal Vox-compatible endpoint remains available only when the
selected voice has documented consent and provenance; it is configured through
`--endpoint` or `TURNPROOF_VOX_URL`, with its token supplied by
`VOX_PROXY_TOKEN` or the local DevLathe credential resolver. Secrets and
endpoint addresses are never written to the receipt.

Celebrity, character, public-figure, and unclear-provenance cloned voices are
ineligible for public submission media, even when they exist in a private voice
catalog.
