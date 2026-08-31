from __future__ import annotations

import io
from typing import Any


def frames_to_gif(frames: list[Any], duration_ms: int = 60) -> bytes:
    """Encode Pillow images when a mission needs visual evidence."""
    if not frames:
        return b""
    stream = io.BytesIO()
    frames[0].save(
        stream,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
    )
    return stream.getvalue()

