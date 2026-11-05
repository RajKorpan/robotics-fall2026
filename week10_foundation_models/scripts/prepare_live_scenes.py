"""Resize the documented CC0 workbench original without altering scene content."""
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT / "runtime" / "workbench_original.jpg"
    if not source.is_file():
        raise SystemExit("Download the original described in assets/live_vision/README.md first.")
    photo = Image.open(source).convert("RGB")
    photo.thumbnail((720,540))
    photo.save(ROOT / "assets" / "live_vision" / "workbench.jpg", quality=94)


if __name__ == "__main__":
    main()
