# 🔧 Setup Guide

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| GPU VRAM | 8 GB | 16+ GB |
| GPU | RTX 3060 | RTX 4090 / A100 |
| RAM | 16 GB | 32+ GB |
| Storage | 40 GB free | 80+ GB free |
| Python | 3.10 | 3.11 |
| CUDA | 11.8 | 12.1 |

> **Note**: SDXL generation at 1024×1024 requires at least 8 GB VRAM. For 8 GB cards, enable `--lowvram` mode in ComfyUI.

---

## Step-by-Step Installation

### 1. Install ComfyUI

```bash
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI
pip install -r requirements.txt
```

Test it works:
```bash
python main.py --listen
# Open http://localhost:8188 in browser
```

### 2. Clone This Repo

```bash
# Place adjacent to ComfyUI for auto-detection
cd ..  # back to parent directory
git clone https://github.com/yourusername/Dreamer
cd Dreamer
pip install -r requirements.txt
```

### 3. Install Custom Nodes

```bash
python scripts/setup_nodes.py
```

If any nodes fail to auto-install, install manually:

```bash
cd ../ComfyUI/custom_nodes
git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus.git
git clone https://github.com/Fannovel16/comfyui_controlnet_aux.git
# etc.
```

### 4. Download Models

```bash
# All models (recommended)
python scripts/download_models.py

# Required models only (faster, minimal setup)
python scripts/download_models.py --required-only
```

**Disk usage by model:**
- SDXL Base: ~6.5 GB
- IPAdapter FaceID v2: ~1.1 GB
- CLIP Vision: ~2.5 GB
- ControlNet OpenPose: ~1.4 GB
- CodeFormer: ~340 MB

### 5. Run ComfyUI

```bash
cd ../ComfyUI

# Standard (recommended)
python main.py --listen

# Low VRAM (8 GB cards)
python main.py --listen --lowvram

# Very low VRAM (6 GB cards)
python main.py --listen --lowvram --cpu-vae
```

### 6. Generate Portraits

```bash
cd ../Dreamer

python scripts/generate_portraits.py \
  --input examples/portrait.jpg \
  --output outputs/ \
  --count 10
```

---

## Troubleshooting

### "Cannot reach ComfyUI"
Make sure ComfyUI is running: `python main.py --listen` and accessible at `http://127.0.0.1:8188`

### CUDA out of memory
- Enable `--lowvram` in ComfyUI
- Reduce batch size
- Use `--fp16` flag

### IPAdapter not working
- Verify `ip-adapter-faceid-plusv2_sdxl.bin` is in `ComfyUI/models/ipadapter/`
- Make sure InsightFace is installed: `pip install insightface`

### Face not detected by InsightFace
- Input image must have a clear frontal or near-frontal face
- Minimum face size: ~200×200 pixels
- Run `scripts/face_crop_preprocess.py` to auto-crop and center
