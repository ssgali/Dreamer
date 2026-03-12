"""
download_models.py
------------------
Downloads all required model weights into the correct
ComfyUI model directories.
"""


import os
import sys
import shutil
import json
from pathlib import Path
from huggingface_hub import hf_hub_download



with open(r"scripts/MODELS.json", 'r') as fp:
    MODELS = json.load(fp) 

# ─────────────────────────────────────────────
# Locate ComfyUI models folder
# ─────────────────────────────────────────────
def find_comfyui_models_dir() -> Path:
    env = os.environ.get("COMFYUI_PATH")

    candidates = [
        Path("../ComfyUI/models"),
        Path("../../ComfyUI/models"),
        Path(env + "/models") if env else None,
        Path.home() / "ComfyUI/models",
    ]

    for c in candidates:
        if c and c.exists():
            return c.resolve()

    raise FileNotFoundError(
        "Could not find ComfyUI models directory.\n"
        "Set COMFYUI_PATH or run script next to ComfyUI."
    )

# ─────────────────────────────────────────────
# Safe file download
# ─────────────────────────────────────────────
def download_file(repo_id, hf_path, dest_file, retries=3):

    for attempt in range(retries):

        try:
            cached = hf_hub_download(
                repo_id=repo_id,
                filename=hf_path,
            )

            shutil.copy2(cached, dest_file)
            return True

        except Exception as e:
            if attempt == retries - 1:
                print(f"      Failed after {retries} attempts: {e}")
                return False

            print("      Retry downloading...")

# ─────────────────────────────────────────────
# Download model
# ─────────────────────────────────────────────
def download_model(model, models_dir, skip_optional=False):

    if not model.get("required", True) and skip_optional:
        print(f"   Skipping optional: {model['name']}")
        return True

    dest_dir = models_dir / model["dest_subdir"]
    dest_dir.mkdir(parents=True, exist_ok=True)

    files = model["filename"]
    if isinstance(files, str):
        files = [files]

    print(f"   Downloading {model['name']}...")

    success = True

    for hf_path in files:

        # Determine destination filename
        if "dest_filename" in model and len(files) == 1:
            filename = model["dest_filename"]
        else:
            filename = Path(hf_path).name

        dest_file = dest_dir / filename

        # Skip existing
        if dest_file.exists():
            print(f"     ✔ Exists → {dest_file}")
            continue

        print(f"     ⬇ {filename}")

        if not download_file(model["repo_id"], hf_path, dest_file):
            success = False

    return success

# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():

    print("Dreamer — Model Downloader")
    print("=" * 50)

    skip_optional = "--required-only" in sys.argv

    try:
        models_dir = find_comfyui_models_dir()
        print(f"Models directory: {models_dir}\n")
    except Exception as e:
        print(e)
        sys.exit(1)

    success = 0

    for model in MODELS:

        label = "required" if model.get("required") else "optional"
        print(f"\n[{label.upper()}] {model['name']}")

        if download_model(model, models_dir, skip_optional):
            success += 1

    print("\n" + "=" * 50)
    print(f"{success}/{len(MODELS)} models ready")


if __name__ == "__main__":
    main()