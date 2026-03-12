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



with open(r"MODELS.json", 'r') as fp:
    MODELS = json.load(fp) 


def find_comfyui_models_dir() -> Path:
    candidates = [
        Path("../ComfyUI/models"),
        Path("../../ComfyUI/models"),
        Path(os.environ.get("COMFYUI_PATH", "") + "/models"),
        Path.home() / "ComfyUI/models",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError(
        "Could not find ComfyUI models directory. "
        "Set COMFYUI_PATH environment variable."
    )


def download_model(model: dict, models_dir: Path, skip_optional: bool = False) -> bool:
    if not model.get("required", True) and skip_optional:
        print(f"   Skipping optional: {model['name']}")
        return True

    dest_dir = models_dir / model["dest_subdir"]
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = Path(dest_dir) / model["dest_filename"]

    if dest_file.exists():
        print(f"✔ Already installed → {dest_file}")

    print(f"   Downloading {model['name']}...")
    if model.get("note"):
        print(f"     Note: {model['note']}")

    try:
        # Safely handle both single strings and lists
        files_to_download = model["filename"]
        if isinstance(files_to_download, str):
            files_to_download = [files_to_download]

        for file_path in files_to_download:
            # hf_hub_download automatically skips downloading if the file is already cached!
            local_path = hf_hub_download(
                repo_id=model["repo_id"],
                filename=file_path,
                local_dir=str(dest_dir),
            )
            print(f"     Ready → {local_path}")
            shutil.copy2(local_path, dest_file)
        return True
    except Exception as e:
        print(f"     Failed to download {model['name']}: {e}")
        return False


def main():
    print("   Dreamer — Model Download")
    print("=" * 50)

    skip_optional = "--required-only" in sys.argv

    try:
        models_dir = find_comfyui_models_dir()
        print(f"   Models directory: {models_dir}\n")
    except FileNotFoundError as e:
        print(f"   {e}")
        sys.exit(1)

    success = 0
    for model in MODELS:
        required_str = "required" if model.get("required") else "optional"
        print(f"\n[{required_str.upper()}] {model['name']}")
        if download_model(model, models_dir, skip_optional):
            success += 1

    print(f"\n{'='*50}")
    print(f"   {success}/{len(MODELS)} models ready")
    print("\nAll set! Run ComfyUI and load a workflow from workflows/")


if __name__ == "__main__":
    main()
