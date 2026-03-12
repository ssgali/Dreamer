"""
setup_nodes.py
--------------
Automatically installs required ComfyUI custom nodes
into the ComfyUI/custom_nodes directory.
"""

import os
import subprocess
import sys
from pathlib import Path

CUSTOM_NODES = [
    {
        "name": "ComfyUI-IPAdapter-plus",
        "url": "https://github.com/cubiq/ComfyUI_IPAdapter_plus.git",
        "description": "IPAdapter conditioning — identity preservation from reference images",
    },
    {
        "name": "ComfyUI-ControlNet-Aux",
        "url": "https://github.com/Fannovel16/comfyui_controlnet_aux.git",
        "description": "OpenPose, depth, canny preprocessors for ControlNet",
    },
    {
        "name": "ComfyUI_InstantID",
        "url": "https://github.com/cubiq/ComfyUI_InstantID.git",
        "description": "InstantID — strongest face identity binding",
    },
    {
        "name": "ComfyUI-CodeFormer",
        "url": "https://github.com/Gourieff/ComfyUI-ReActor.git",
        "description": "Face restoration and enhancement post-processing",
    },
    {
        "name": "ComfyUI-Impact-Pack",
        "url": "https://github.com/ltdrdata/ComfyUI-Impact-Pack.git",
        "description": "Face detection, segmentation, and masking utilities",
    },
    {
        "name": "ComfyUI-WD14-Tagger",
        "url": "https://github.com/pythongosssss/ComfyUI-WD14-Tagger.git",
        "description": "Auto-tagging for prompt assistance",
    },
]


def find_comfyui_root() -> Path:
    """Try to locate the ComfyUI installation directory."""
    candidates = [
        Path("../ComfyUI"),
        Path("../../ComfyUI"),
        Path(os.environ.get("COMFYUI_PATH", "")),
        Path.home() / "ComfyUI",
    ]
    for candidate in candidates:
        if candidate.exists() and (candidate / "main.py").exists():
            return candidate.resolve()
    raise FileNotFoundError(
        "Could not find ComfyUI installation. "
        "Set COMFYUI_PATH environment variable or install ComfyUI adjacent to this repo."
    )


def install_node(node: dict, custom_nodes_dir: Path) -> bool:
    dest = custom_nodes_dir / node["name"]
    if dest.exists():
        print(f"  ⏭️  {node['name']} already installed — skipping")
        return True

    print(f"     Installing {node['name']}...")
    print(f"     {node['description']}")
    result = subprocess.run(
        ["git", "clone", node["url"], str(dest)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"     Failed: {result.stderr}")
        return False

    # Install node-specific requirements if present
    req_file = dest / "requirements.txt"
    if req_file.exists():
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
            capture_output=True,
        )

    print(f"     Installed {node['name']}")
    return True


def main():
    print("   Dreamer — Node Setup")
    print("=" * 50)

    try:
        comfyui_root = find_comfyui_root()
        print(f"   Found ComfyUI at: {comfyui_root}\n")
    except FileNotFoundError as e:
        print(f"   {e}")
        sys.exit(1)

    custom_nodes_dir = comfyui_root / "custom_nodes"
    custom_nodes_dir.mkdir(exist_ok=True)

    success = 0
    for node in CUSTOM_NODES:
        if install_node(node, custom_nodes_dir):
            success += 1

    print(f"\n{'='*50}")
    print(f"   Setup complete: {success}/{len(CUSTOM_NODES)} nodes installed")
    print(f"\nNext step: python scripts/download_models.py")


if __name__ == "__main__":
    main()
