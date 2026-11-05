"""Run once with the guide's Python. Subsequent model inference is offline."""
import json
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lab.local_config import MODEL_CONFIG, model_dir, model_python, runtime_dir


def main():
    if "--download-only" not in sys.argv:
        print("Preparing an isolated CPU model environment", flush=True)
        if not model_python().is_file():
            venv.EnvBuilder(with_pip=True).create(runtime_dir())
        subprocess.run([str(model_python()), "-m", "ensurepip", "--upgrade"], check=True)
        torch_index = [] if sys.platform == "darwin" else ["--index-url", "https://download.pytorch.org/whl/cpu"]
        subprocess.run([str(model_python()), "-m", "pip", "install", *torch_index, "torch==2.8.0"], check=True)
        subprocess.run([str(model_python()), "-m", "pip", "install", "-r", str(ROOT / "requirements-models.txt")], check=True)
        subprocess.run([str(model_python()), str(Path(__file__).resolve()), "--download-only"], check=True)
        return
    from huggingface_hub import snapshot_download
    for kind, config in MODEL_CONFIG.items():
        print("Downloading " + config["id"] + " at " + config["revision"], flush=True)
        folder = model_dir(kind)
        folder.mkdir(parents=True, exist_ok=True)
        snapshot_download(config["id"], revision=config["revision"], local_dir=folder,
                          allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model", "*.jinja"], max_workers=2)
        (folder / "course_model.json").write_text(json.dumps(config, indent=2))
    print("Both pinned models are downloaded. Run preflight to test local generation.", flush=True)


if __name__ == "__main__":
    main()
