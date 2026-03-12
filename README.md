#  Dreamer-Lite

> **Identity-aware portrait variation with ComfyUI + SD 1.5 + IPAdapter — runs on 4 GB VRAM**

This is a **trimmed-down companion** to [Dreamer](https://github.com/ssgali/Dreamer/tree/main) — same ideas, much lower hardware bar.

---

## 🖥️ Hardware Requirements

| | Minimum | This Repo Targets |
|--|---------|-------------------|
| GPU VRAM | 4 GB | **4 GB**  |
| RAM | 8 GB | 16 GB recommended |
| Storage | 8 GB free | 10 GB free |
| GPU | GTX 1650 / RX 580 | RTX 3060 / any 4 GB card |
| CPU fallback |  slow but works | — |

> **No GPU?** ComfyUI can run on CPU with `--cpu` flag. Expect ~5–10 min per image.

---

##  What This Demonstrates

This repo is designed as a **hands-on introduction** to three core concepts in modern diffusion pipelines:

```
1. Denoising Diffusion  →  How SD 1.5 generates images from noise
2. Image Conditioning  →  How IPAdapter injects a reference image's "look"
3. Prompt Steering     →  How text guides the denoising process
```

The task: **take one portrait photo → generate 5 expression variations** while keeping the person recognizable.

```
Input Photo
    │
    ├──► IPAdapter (image conditioning — "look like this person")
    │         weight: 0.6–0.75
    │
    ├──► Text Prompt (expression steering)
    │         "gentle smile", "neutral", "confident" ...
    │
    ▼
SD 1.5 UNet  (30 denoising steps @ 512×512)
    │
    ▼
Output Portrait  (5 variations, ~45 seconds each on 4 GB GPU)
```

---

##  Quick Start (5 Steps)

### 1. Install ComfyUI

```bash
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI

# IMPORTANT for 4 GB VRAM — install with fp16 PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
```

### 2. Clone This Repo

```bash
cd ..
git clone https://github.com/ssgali/Dreamer/tree/Dreamer-lite
cd Dreamer
pip install -r requirements.txt
```

### 3. Install the One Required Custom Node

```bash
python scripts/setup.py
# Installs ComfyUI-IPAdapter-plus into ComfyUI/custom_nodes/
```

### 4. Download Models (~3.5 GB total)

```bash
python scripts/download_models.py
# Downloads SD 1.5, IPAdapter ViT-H, CLIP Vision encoder
```

### 5. Generate Portraits

```bash
# Start ComfyUI in low-VRAM mode
cd ../ComfyUI
python main.py --listen --lowvram

# In a new terminal, run generation
cd ../portrait-diffusion-lite
python scripts/run.py --input examples/portrait.jpg --count 5
```

Results saved to `outputs/`.

---

##  Repository Structure

```
portrait-diffusion-lite/
│
├── workflows/
│   ├── sd15_ipadapter_lite.json        ← Main workflow (drag into ComfyUI)
│   └── sd15_img2img_simple.json        ← Even simpler: no IPAdapter needed
│
├── scripts/
│   ├── run.py                          ← One-command generation CLI
│   ├── setup.py                        ← Install required ComfyUI node
│   └── download_models.py              ← Fetch model weights
│
├── configs/
│   └── expressions.yaml               ← Edit expression prompts here
│
├── docs/
│   ├── HOW_IT_WORKS.md                ← Plain-English explanation of the pipeline
│   ├── VRAM_TIPS.md                   ← Tricks to stay under 4 GB
│   └── NEXT_STEPS.md                  ← Where to go after this demo
│
├── examples/
│   └── portrait.jpg                   ← Drop your own photo here
│
├── requirements.txt
├── LICENSE
└── README.md
```

---

##  Workflows

### `sd15_ipadapter_lite.json` — Main Demo
**SD 1.5 + IPAdapter ViT-H at 512×512.**
This is the recommended starting point. Load it in ComfyUI and you'll see every node explained with labels.

- Resolution: `512×512`
- Steps: `25`
- IPAdapter weight: `0.65`
- Peak VRAM: ~3.2 GB

### `sd15_img2img_simple.json` — Zero-Dependency Fallback
**Pure img2img — no custom nodes needed at all.**
If IPAdapter gives you trouble, this workflow uses only built-in ComfyUI nodes. Lower identity preservation but always works.

- Resolution: `512×512`
- Denoise: `0.55`
- Peak VRAM: ~2.1 GB

---

##  Tuning for Your Hardware

### 4 GB VRAM (target)
```bash
python main.py --listen --lowvram
```
All settings in `configs/expressions.yaml` are pre-tuned for this.

### 6–8 GB VRAM (more headroom)
Increase resolution and steps:
```yaml
# configs/expressions.yaml
generation:
  width: 768
  height: 768
  steps: 30
```

### CPU only (no GPU)
```bash
python main.py --listen --cpu
```
Expect 5–15 minutes per image. Use `steps: 15` to keep it reasonable.

---

##  How It Actually Works

See [`docs/HOW_IT_WORKS.md`](docs/HOW_IT_WORKS.md) for a plain-English walkthrough.

**The short version:**

1. **Stable Diffusion 1.5** is a trained neural network that has learned to reverse a noise-adding process. At inference time it starts from random noise and gradually *denoises* it toward an image matching your prompt — over 25 steps.

2. **IPAdapter** conditions the denoising process on a *reference image* by projecting it into the same feature space as the text prompt. This makes the output look like a variation of your input rather than a random person matching the text.

3. **Expression prompts** steer *which kind* of variation gets generated — the text and image conditioning act together at each denoising step.

---

##  What to Expect

| Setting | Time/image | VRAM | Identity preservation |
|---------|-----------|------|----------------------|
| Default (512, steps=25, ipadapter=0.65) | ~40–60s | ~3.2 GB | Good |
| Fast (512, steps=15, ipadapter=0.65) | ~20–30s | ~3.0 GB | Good |
| Higher quality (768, steps=30) | ~90–120s | ~5.5 GB | Very good |
| Img2img only (no IPAdapter) | ~25–40s | ~2.1 GB | Moderate |

---
