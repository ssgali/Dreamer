# 🔀 Workflow Reference

All workflows are in `workflows/` as ComfyUI-native JSON files. Drag and drop any of them into ComfyUI to load.

---

## `sdxl_ipadapter_portrait.json` ✅ Recommended

**Use this first.** The core pipeline with the best balance of identity fidelity and variation quality.

**Nodes:** LoadImage → InsightFace → IPAdapter FaceID v2 → SDXL → VAE Decode → SaveImage

**Key parameters:**
| Node | Parameter | Default | Notes |
|------|-----------|---------|-------|
| IPAdapter | `weight` | 0.78 | Lower = more creative, higher = more identity-locked |
| KSampler | `cfg` | 7.0 | 6–8 is the sweet spot for SDXL |
| KSampler | `denoise` | 0.65 | Lower = more conservative changes |
| KSampler | `steps` | 30 | Reduce to 20 for speed, 40 for quality |
| EmptyLatent | `width/height` | 1024 | Keep at 1024 for SDXL |

---

## `full_pipeline_codeformer.json` 🔥 Best Quality

Adds ControlNet OpenPose (pose lock) + CodeFormer face restoration. Slower but sharpest outputs.

**Nodes:** ... + OpenposePreprocessor → ControlNet → ... → CodeFormer → SaveImage

**Additional parameters:**
| Node | Parameter | Default | Notes |
|------|-----------|---------|-------|
| ControlNet | `strength` | 0.45 | Higher = more pose-locked |
| ControlNet | `end_percent` | 0.65 | Stop ControlNet influence at 65% of steps |
| CodeFormer | `fidelity_weight` | 0.7 | 0.0 = max restore, 1.0 = keep original |

---

## `instantid_portrait.json` 🎯 Strongest Identity

Uses InstantID for maximum facial identity binding. Less creative variation, tightest face match.

**When to use:** When identity preservation is the top priority and you don't need much variation.

---

## `controlnet_openpose_batch.json` 🧍 Pose-Locked

OpenPose skeleton extraction + ControlNet. Keeps head orientation identical across all generations.

**When to use:** When you need consistent head angle across your batch.

---

## Tips for Tuning

### IPAdapter Weight
- `0.5–0.65` — Creative, may drift from identity
- `0.70–0.82` — **Sweet spot** — preserves identity with good variation
- `0.85–1.0` — Strong identity lock, less creative freedom

### Denoise Strength
- `0.45–0.55` — Conservative — subtle changes, very identity-safe
- `0.60–0.70` — **Balanced**
- `0.75–0.85` — More dramatic changes, some identity risk

### Expression Prompting Tips
Append to the base positive prompt:
```
# Good expressions
"with a gentle, warm smile, soft lips slightly parted"
"with confident eyes, slight upward curve at mouth corners"
"with a serene expression, relaxed jaw"

# Avoid vague terms
"happy" → too generic, use "bright genuine smile, Duchenne smile"
"serious" → too generic, use "focused expression, direct neutral gaze, composed"
```
