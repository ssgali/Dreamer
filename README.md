# Dreamer

> **Identity-preserving portrait generation using ComfyUI, SDXL, IPAdapter, and ControlNet**

---

## What Is This?

**Dreamer** is a modular, extensible pipeline for generating high-quality portrait variations from a single input image — while **preserving facial identity**. Built on top of [ComfyUI](https://github.com/comfyanonymous/ComfyUI) with SDXL, IPAdapter, and ControlNet, it allows you to:

- Generate **5–20 portrait variations** in a single batch
- Preserve subject **identity and likeness** across generations
- Control **expression, lighting, style, and background** independently
- Export **ComfyUI-native JSON workflows** that are drag-and-drop ready
- Run **headless batch generation** via Python scripts (no UI needed)

---

## Example Results

| Input | Gentle Smile | Confident | Neutral | Relaxed |
|-------|-------------|-----------|---------|---------|
| ![input](assets/demo/input.jpg) | ![v1](assets/demo/v1.jpg) | ![v2](assets/demo/v2.jpg) | ![v3](assets/demo/v3.jpg) | ![v4](assets/demo/v4.jpg) |

> *All outputs generated from a single input photo using the IPAdapter + ControlNet OpenPose pipeline.*

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Dreamer                                   │
│                                                             │
│  Input Image                                                │
│      │                                                      │
│      ├──► InsightFace Embedding ──► IPAdapter Face ID       │
│      │         (identity lock)                              │
│      │                                                      │
│      ├──► OpenPose Extraction ──► ControlNet Conditioning   │
│      │         (pose lock)                                  │
│      │                                                      │
│      └──► CLIP Vision ──► Image Prompt Conditioning         │
│                                                             │
│  Text Prompts (expression, style, lighting)                 │
│      │                                                      │
│      ▼                                                      │
│  SDXL UNet ──► Latent Space ──► VAE Decode                  │
│                                                             │
│  Post-Processing                                            │
│      ├──► CodeFormer (face restoration)                     │
│      └──► GFPGAN (enhancement, optional)                    │
│                                                             │
│  Output: 5–20 portrait variations @ 1024×1024               │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Components

| Component | Role | Why It Matters |
|-----------|------|----------------|
| **SDXL** | Base generation model | High-res, photorealistic outputs |
| **IPAdapter FaceID** | Identity conditioning | Preserves facial features across generations |
| **ControlNet OpenPose** | Pose conditioning | Keeps head orientation consistent |
| **InsightFace** | Face embedding extraction | Feeds identity vector to IPAdapter |
| **CodeFormer** | Post-processing | Restores and sharpens facial details |
| **ComfyUI** | Workflow orchestration | Visual, node-based pipeline management |

---

## Quick Start

### 1. Prerequisites

```bash
# Python 3.10+
python --version

# ComfyUI (install if not present)
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI
pip install -r requirements.txt
```

### 2. Clone This Repo

```bash
git clone https://github.com/ssgali/Dreamer
cd Dreamer
pip install -r requirements.txt
```

### 3. Install ComfyUI Custom Nodes

```bash
# Run our setup script (installs all required custom nodes automatically)
python scripts/setup_nodes.py
```

This installs:
- `ComfyUI-IPAdapter-plus`
- `ComfyUI-ControlNet-Aux`
- `ComfyUI_InstantID`
- `ComfyUI-CodeFormer`
- `ComfyUI-Impact-Pack`

### 4. Download Required Models

```bash
python scripts/download_models.py
```

This fetches:
- `sd_xl_base_1.0.safetensors` (SDXL)
- `ip-adapter-faceid-plusv2_sdxl.bin` (IPAdapter)
- `control_v11p_sd15_openpose.pth` (ControlNet)
- `codeformer.pth` (face restoration)

### 5. Run Generation

```bash
# Using Python script (headless)
python scripts/generate_portraits.py \
  --input examples/portrait.jpg \
  --output outputs/ \
  --count 10 \
  --expressions "gentle smile,confident,neutral,relaxed,thoughtful"

# Or drag-and-drop a workflow into ComfyUI
# See: workflows/sdxl_ipadapter_portrait.json
```

---

## Repository Structure

```
Dreamer/
│
├── workflows/                    # ComfyUI JSON workflows (drag & drop ready)
│   ├── sdxl_ipadapter_portrait.json       # Main pipeline: IPAdapter + SDXL
│   ├── instantid_portrait.json            # InstantID variant
│   ├── controlnet_openpose_batch.json     # Pose-locked batch generation
│   └── full_pipeline_codeformer.json      # With CodeFormer post-processing
│
├── scripts/                      # Python automation scripts
│   ├── generate_portraits.py              # Main CLI generation script
│   ├── setup_nodes.py                     # Auto-install ComfyUI custom nodes
│   ├── download_models.py                 # Download required model weights
│   ├── batch_runner.py                    # Headless ComfyUI API runner
│   └── face_crop_preprocess.py            # Input preprocessing utilities
│
├── configs/                      # Generation config files
│   ├── default_expressions.yaml          # Expression prompt templates
│   ├── lighting_presets.yaml             # Lighting style presets
│   └── pipeline_config.yaml              # Main pipeline configuration
│
├── notebooks/                    # Jupyter exploration notebooks
│   ├── 01_pipeline_walkthrough.ipynb     # Step-by-step tutorial
│   ├── 02_ipadapter_strength_sweep.ipynb # Hyperparameter exploration
│   └── 03_expression_interpolation.ipynb # Latent interpolation experiments
│
├── docs/                         # Documentation
│   ├── SETUP.md                          # Detailed setup guide
│   ├── WORKFLOWS.md                      # Workflow documentation
│   ├── MODEL_NOTES.md                    # Model selection notes
│   └── FUTURE_DIRECTIONS.md             # Research roadmap
│
├── assets/
│   └── demo/                            # Demo images
│
├── examples/                     # Example inputs
│   └── portrait.jpg
│
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Workflows

### 1. `sdxl_ipadapter_portrait.json` — Recommended
The primary pipeline. Uses **IPAdapter FaceID v2** for identity conditioning and **SDXL** for generation. Best balance of identity preservation and variation quality.

**Parameters to tune:**
- `ipadapter_weight`: `0.7–0.85` (higher = more identity-locked)
- `cfg_scale`: `6–8`
- `denoise`: `0.55–0.75` (lower = more conservative variation)

### 2. `instantid_portrait.json` — Strongest Identity
Uses **InstantID** which provides tighter face binding. Recommended when identity preservation is the top priority over stylistic freedom.

### 3. `controlnet_openpose_batch.json` — Pose Control
Adds OpenPose skeleton extraction to lock the head pose. Combine with IPAdapter for both identity and pose control simultaneously.

### 4. `full_pipeline_codeformer.json` — Production Quality
Full pipeline with CodeFormer post-processing for the cleanest final outputs. ~20% slower but noticeably sharper face details.

---

## Expression Prompt Guide

Expression changes are driven by **positive prompt injection**. Use our built-in presets or write your own:

```yaml
# configs/default_expressions.yaml
expressions:
  gentle_smile: "with a gentle, warm smile, soft expression"
  confident: "with a confident expression, slight smile, strong gaze"
  neutral: "with a neutral, relaxed expression, calm eyes"
  relaxed: "with a relaxed, natural expression, soft eyes"
  thoughtful: "looking thoughtful, slight contemplative expression"
  joyful: "with a bright joyful smile, eyes slightly squinted"
```

---

## Python API

```python
from scripts.generate_portraits import PortraitPipeline

pipeline = PortraitPipeline(
    workflow="workflows/sdxl_ipadapter_portrait.json",
    comfyui_url="http://127.0.0.1:8188"
)

results = pipeline.generate(
    input_image="examples/portrait.jpg",
    expressions=["gentle smile", "confident", "neutral"],
    count=9,          # total images
    seed_range=(0, 9999),
    output_dir="outputs/"
)

print(f"Generated {len(results)} portraits → {results}")
```

---

## Model Comparison

| Method | Identity Score | Variation Quality | Speed | Notes |
|--------|---------------|-------------------|-------|-------|
| IPAdapter FaceID v2 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Fast | Best overall |
| InstantID | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Medium | Best identity |
| IP-Adapter + ControlNet | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Medium | Pose-controlled |
| Vanilla img2img | ⭐⭐ | ⭐⭐⭐⭐⭐ | Fast | No identity lock |

---

## Future Directions

See [`docs/FUTURE_DIRECTIONS.md`](docs/FUTURE_DIRECTIONS.md) for the full roadmap. Key areas:

- **Video Portrait Generation** — Animate expressions using [LivePortrait](https://github.com/KwaiVGI/LivePortrait) or DiffusedHeads
- **3D-Consistent Multi-View Generation** — Generate portraits from multiple angles with consistent identity using Zero123++ or SyncDreamer
- **LoRA Fine-tuning per Subject** — Auto-train a subject-specific LoRA from 5–10 reference images for ultra-tight identity lock
- **Real-time Web Demo** — Gradio/Streamlit app with ComfyUI backend for browser-based generation
- **Emotion Slider (Latent Control)** — Smooth interpolation between expression states in latent space
- **Style Transfer Preservation** — Apply artistic styles while keeping identity (e.g., oil painting portrait)

---

