"""
setup.py
--------
Installs the one required ComfyUI custom node:
  → ComfyUI-IPAdapter-plus (cubiq)

Run this once before using the ipadapter workflow.
The img2img workflow works without any setup.
"""

import os
import subprocess
import sys
from pathlib import Path


def find_comfyui() -> Path:
    candidates = [
        Path("../ComfyUI"),
        Path("../../ComfyUI"),
        Path(os.environ.get("COMFYUI_PATH", "___nonexistent___")),
        Path.home() / "ComfyUI",
    ]
    for c in candidates:
        if c.exists() and (c / "main.py").exists():
            return c.resolve()
    raise FileNotFoundError(
        "\n  Could not find ComfyUI.\n"
        "    Either:\n"
        "      (a) Place this repo next to your ComfyUI folder, or\n"
        "      (b) Set the COMFYUI_PATH environment variable\n"
        "          export COMFYUI_PATH=/path/to/ComfyUI\n"
    )


def install_ipadapter(comfyui_root: Path):
    dest = comfyui_root / "custom_nodes" / "ComfyUI_IPAdapter_plus"

    if dest.exists():
        print(f"  ComfyUI_IPAdapter_plus already installed at:\n    {dest}")
        return

    print("  Installing ComfyUI_IPAdapter_plus...")
    result = subprocess.run(
        ["git", "clone", "https://github.com/cubiq/ComfyUI_IPAdapter_plus.git", str(dest)],
        capture_output=True, text=True,
    )

    if result.returncode != 0:
        print(f"  git clone failed:\n{result.stderr}")
        print("\n    Manual install:\n")
        print(f"    cd {comfyui_root / 'custom_nodes'}")
        print("    git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus.git")
        sys.exit(1)

    # Install node requirements
    req = dest / "requirements.txt"
    if req.exists():
        print("    Installing node dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req)], check=False)

    print(f"  Installed → {dest}")


def main():
    print("  Dreamer-Lite — Setup")
    print("=" * 40)

    try:
        comfyui = find_comfyui()
        print(f"  ComfyUI found at: {comfyui}\n")
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)

    install_ipadapter(comfyui)

    print("\n  Setup complete!")
    print("\nNext step:")
    print("    python scripts/download_models.py\n")


if __name__ == "__main__":
    main()
