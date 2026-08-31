from __future__ import annotations

from collections import deque
from pathlib import Path


def read_pgm(path: Path) -> tuple[int, int, int, list[int]]:
    data = path.read_bytes(); index = 0
    def token():
        nonlocal index
        while index < len(data):
            if data[index:index + 1] == b"#":
                while index < len(data) and data[index:index + 1] not in (b"\n", b"\r"): index += 1
            if index < len(data) and data[index:index + 1].isspace(): index += 1
            else: break
        start = index
        while index < len(data) and not data[index:index + 1].isspace(): index += 1
        return data[start:index]
    magic = token(); width = int(token()); height = int(token()); maximum = int(token())
    if magic == b"P2": pixels = [int(token()) for _ in range(width * height)]
    elif magic == b"P5":
        while index < len(data) and data[index:index + 1].isspace(): index += 1
        raw = data[index:index + width * height * (2 if maximum > 255 else 1)]
        pixels = list(raw) if maximum <= 255 else [int.from_bytes(raw[i:i + 2], "big") for i in range(0, len(raw), 2)]
    else: raise ValueError("Only P2 and P5 PGM maps are supported")
    if len(pixels) != width * height: raise ValueError("PGM pixel count does not match dimensions")
    return width, height, maximum, pixels


def _components(mask: list[bool], width: int, height: int) -> list[int]:
    seen = set(); sizes = []
    for start, enabled in enumerate(mask):
        if not enabled or start in seen: continue
        queue = deque([start]); seen.add(start); size = 0
        while queue:
            cell = queue.popleft(); size += 1; x, y = cell % width, cell // width
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                neighbor = ny * width + nx
                if 0 <= nx < width and 0 <= ny < height and mask[neighbor] and neighbor not in seen: seen.add(neighbor); queue.append(neighbor)
        sizes.append(size)
    return sizes


def analyze_pixels(width: int, height: int, maximum: int, pixels: list[int], resolution: float) -> dict:
    scale = maximum / 255.0
    occupied = [value <= 65 * scale for value in pixels]
    free = [value >= 250 * scale for value in pixels]
    unknown = [not a and not b for a, b in zip(occupied, free)]
    components = _components(occupied, width, height); occupied_count = sum(occupied); known = occupied_count + sum(free)
    speckles = sum(size for size in components if size <= 3)
    border = [x for x in range(width)] + [(height - 1) * width + x for x in range(width)] + [y * width for y in range(1, height - 1)] + [y * width + width - 1 for y in range(1, height - 1)]
    return {
        "width": width, "height": height, "resolution": resolution,
        "map_area_m2": width * height * resolution * resolution,
        "known_fraction": known / len(pixels), "unknown_fraction": sum(unknown) / len(pixels),
        "occupied_fraction": occupied_count / len(pixels), "free_fraction": sum(free) / len(pixels),
        "occupied_components": len(components), "largest_component_cells": max(components, default=0),
        "speckle_fraction": speckles / max(1, occupied_count),
        "border_contact_fraction": sum(occupied[cell] for cell in border) / max(1, len(border)),
    }


def quality_score(metrics: dict) -> float:
    coverage = min(1.0, metrics["known_fraction"] / 0.55)
    continuity = 1.0 - min(1.0, metrics["speckle_fraction"] / 0.12)
    clipping = 1.0 - min(1.0, metrics["border_contact_fraction"] / 0.35)
    return round(100 * (0.55 * coverage + 0.30 * continuity + 0.15 * clipping), 1)
