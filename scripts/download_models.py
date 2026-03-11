"""
download_models.py
------------------
Downloads all required model weights into the correct
ComfyUI model directories.
"""

import hashlib
import os
import sys
from pathlib import Path

try:
    from huggingface_hub import hf_hub_download, snapshot_download
except ImportError:
    print("Installing huggingface_hub...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub"], check=True)
    from huggingface_hub import hf_hub_download, snapshot_download

MODELS = [
    # ─── SDXL Base ────────────────────────────────────────────────────────────
    {
        "name": "SDXL Base 1.0",
        "repo_id": "stabilityai/stable-diffusion-xl-base-1.0",
        "filename": "sd_xl_base_1.0.safetensors",
        "dest_subdir": "checkpoints",
        "required": True,
    },
    # ─── IPAdapter ────────────────────────────────────────────────────────────
    {
        "name": "IPAdapter FaceID Plus v2 (SDXL)",
        "repo_id": "h94/IP-Adapter-FaceID",
        "filename": "ip-adapter-faceid-plusv2_sdxl.bin",
        "dest_subdir": "ipadapter",
        "required": True,
    },
    {
        "name": "IPAdapter CLIP Vision ViT-H",
        "repo_id": "h94/IP-Adapter",
        "filename": "models/image_encoder/model.safetensors",
        "dest_subdir": "clip_vision",
        "dest_filename": "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors",
        "required": True,
    },
    # ─── ControlNet ───────────────────────────────────────────────────────────
    {
        "name": "ControlNet OpenPose (SD1.5)",
        "repo_id": "lllyasviel/ControlNet-v1-1",
        "filename": "control_v11p_sd15_openpose.pth",
        "dest_subdir": "controlnet",
        "required": False,
        "note": "Optional — only needed for pose-locked generation",
    },
    {
        "name": "ControlNet OpenPose (SDXL)",
        "repo_id": "thibaud/controlnet-openpose-sdxl-1.0",
        "filename": "OpenPoseXL2.safetensors",
        "dest_subdir": "controlnet",
        "required": False,
    },
    # ─── InsightFace ──────────────────────────────────────────────────────────
    {
        "name": "InsightFace buffalo_l",
        "repo_id": "deepinsight/insightface",
        "filename": "models/buffalo_l.zip",
        "dest_subdir": "insightface/models",
        "required": True,
        "note": "Required for IPAdapter FaceID",
    },
    # ─── CodeFormer ───────────────────────────────────────────────────────────
    {
        "name": "CodeFormer",
        "repo_id": "sczhou/CodeFormer",
        "filename": "weights/CodeFormer/codeformer.pth",
        "dest_subdir": "facerestore_models",
        "dest_filename": "codeformer.pth",
        "required": False,
        "note": "Optional post-processing — highly recommended for quality",
    },
    # ─── VAE ──────────────────────────────────────────────────────────────────
    {
        "name": "SDXL VAE",
        "repo_id": "madebyollin/sdxl-vae-fp16-fix",
        "filename": "sdxl_vae.safetensors",
        "dest_subdir": "vae",
        "required": False,
        "note": "Fixes fp16 NaN issues — recommended",
    },
]


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
        print(f"  ⏭️  Skipping optional: {model['name']}")
        return True

    dest_dir = models_dir / model["dest_subdir"]
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_filename = model.get("dest_filename", Path(model["filename"]).name)
    dest_path = dest_dir / dest_filename

    if dest_path.exists():
        print(f"  ⏭️  {model['name']} already downloaded — skipping")
        return True

    print(f"  ⬇️  Downloading {model['name']}...")
    if model.get("note"):
        print(f"     Note: {model['note']}")

    try:
        local_path = hf_hub_download(
            repo_id=model["repo_id"],
            filename=model["filename"],
            local_dir=str(dest_dir),
        )
        # Rename if needed
        if Path(local_path).name != dest_filename:
            Path(local_path).rename(dest_path)

        print(f"  ✅ Downloaded → {dest_path}")
        return True
    except Exception as e:
        print(f"  ❌ Failed to download {model['name']}: {e}")
        return False


def main():
    print("📥 Dreamer — Model Download")
    print("=" * 50)

    skip_optional = "--required-only" in sys.argv

    try:
        models_dir = find_comfyui_models_dir()
        print(f"✅ Models directory: {models_dir}\n")
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)

    success = 0
    for model in MODELS:
        required_str = "required" if model.get("required") else "optional"
        print(f"\n[{required_str.upper()}] {model['name']}")
        if download_model(model, models_dir, skip_optional):
            success += 1

    print(f"\n{'='*50}")
    print(f"✅ {success}/{len(MODELS)} models ready")
    print("\nAll set! Run ComfyUI and load a workflow from workflows/")


if __name__ == "__main__":
    main()
