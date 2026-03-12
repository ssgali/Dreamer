"""
generate_portraits.py
------
Single-command portrait variation generator.
Connects to a running ComfyUI instance and batches
through your configured expressions automatically.

Usage:
    python scripts/generate_portraits.py --input examples/portrait.jpg --count 5
    python scripts/generate_portraits.py --input portrait.jpg --workflow img2img  # no IPAdapter needed
    python scripts/generate_portraits.py --input portrait.jpg --count 5 --seed 1234
"""

import argparse
import json
import random
import time
import uuid
from pathlib import Path

import requests
import yaml

COMFYUI_URL = "http://127.0.0.1:8188"

WORKFLOW_MAP = {
    "ipadapter": "workflows/sd15_ipadapter_lite.json",
    "img2img":   "workflows/sd15_img2img_simple.json",
}

# Fallback expressions if config not found
FALLBACK_EXPRESSIONS = [
    "with a gentle warm smile, soft expression",
    "with a confident expression, slight smile",
    "with a neutral relaxed expression, calm eyes",
    "with a thoughtful contemplative expression",
    "with a bright joyful smile, eyes slightly squinted",
]


# ─── ComfyUI helpers ──────────────────────────────────────────────────────────

def check_comfyui(url: str = COMFYUI_URL) -> bool:
    try:
        r = requests.get(f"{url}/system_stats", timeout=4)
        return r.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def upload_image(path: str, url: str = COMFYUI_URL) -> str:
    with open(path, "rb") as f:
        r = requests.post(
            f"{url}/upload/image",
            files={"image": (Path(path).name, f, "image/jpeg")},
        )
    r.raise_for_status()
    return r.json()["name"]


def queue_prompt(workflow: dict, url: str = COMFYUI_URL) -> str:
    client_id = str(uuid.uuid4())
    r = requests.post(f"{url}/prompt", json={"prompt": workflow, "client_id": client_id})
    r.raise_for_status()
    return r.json()["prompt_id"]


def wait_and_download(prompt_id: str, output_dir: Path, url: str = COMFYUI_URL, timeout: int = 300) -> list[str]:
    """Poll history until done, then download all output images."""
    start = time.time()
    while time.time() - start < timeout:
        history = requests.get(f"{url}/history/{prompt_id}").json()
        if prompt_id in history:
            break
        time.sleep(1.5)
    else:
        raise TimeoutError(f"Timed out after {timeout}s waiting for {prompt_id}")

    output_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for node_output in history[prompt_id].get("outputs", {}).values():
        for img_info in node_output.get("images", []):
            params = {
                "filename": img_info["filename"],
                "subfolder": img_info.get("subfolder", ""),
                "type": img_info.get("type", "output"),
            }
            r = requests.get(f"{url}/view", params=params)
            r.raise_for_status()
            dest = output_dir / img_info["filename"]
            dest.write_bytes(r.content)
            saved.append(str(dest))
    return saved


# ─── Workflow patching ────────────────────────────────────────────────────────

def patch_workflow(workflow: dict, uploaded_name: str, expression: str, seed: int) -> dict:
    """
    Patch a loaded workflow dict with per-generation values.
    Finds nodes by their _meta title and updates the relevant inputs.
    """
    import copy
    wf = copy.deepcopy(workflow)

    for node in wf.values():
        title = node.get("_meta", {}).get("title", "")

        # Image input node
        if "Load Reference Portrait" in title or "Load Input Portrait" in title:
            node["inputs"]["image"] = uploaded_name

        # Positive prompt — build full prompt around the expression
        if "Positive Prompt" in title or "EDIT EXPRESSION" in title:
            node["inputs"]["text"] = (
                f"portrait photograph of a person, {expression}, "
                "studio lighting, sharp focus, photorealistic, 85mm lens, "
                "natural skin texture, soft background bokeh"
            )

        # KSampler — update seed
        if "KSampler" in title:
            node["inputs"]["seed"] = seed

    return wf


# ─── Main pipeline ────────────────────────────────────────────────────────────

def load_expressions() -> list[str]:
    config_path = Path("configs/expressions.yaml")
    if config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f)
        return [v["prompt"] for v in data.get("expressions", {}).values()]
    return FALLBACK_EXPRESSIONS


def run(
    input_image: str,
    count: int = 5,
    workflow_name: str = "ipadapter",
    output_dir: str = "outputs/",
    seed: int | None = None,
):
    # ── Sanity checks ──────────────────────────────────────────────────────────
    if not Path(input_image).exists():
        raise FileNotFoundError(f"Input image not found: {input_image}")

    if not check_comfyui():
        print("\n  Cannot reach ComfyUI at http://127.0.0.1:8188")
        print("    Start it first:\n")
        print("      cd ../ComfyUI")
        print("      python main.py --listen --lowvram\n")
        raise SystemExit(1)

    workflow_path = WORKFLOW_MAP.get(workflow_name)
    if not workflow_path or not Path(workflow_path).exists():
        raise FileNotFoundError(f"Workflow not found: {workflow_path}")

    with open(workflow_path) as f:
        base_workflow = json.load(f)

    expressions = load_expressions()
    output_path = Path(output_dir)

    print(f"\n  Dreamer-Lite")
    print(f"    Input   : {input_image}")
    print(f"    Workflow: {workflow_path}")
    print(f"    Count   : {count}")
    print(f"    Output  : {output_dir}")
    print()

    # ── Upload input image once ────────────────────────────────────────────────
    print("  Uploading input image...")
    uploaded_name = upload_image(input_image)
    print(f"    → {uploaded_name}")
    print()

    all_outputs = []

    for i in range(count):
        expression = expressions[i % len(expressions)]
        current_seed = seed if seed is not None else random.randint(0, 2**32 - 1)

        print(f"[{i+1}/{count}]  Expression : {expression}")
        print(f"         Seed       : {current_seed}")

        wf = patch_workflow(base_workflow, uploaded_name, expression, current_seed)
        prompt_id = queue_prompt(wf)

        t0 = time.time()
        outputs = wait_and_download(prompt_id, output_path)
        elapsed = time.time() - t0

        all_outputs.extend(outputs)
        for p in outputs:
            print(f"          {p}  ({elapsed:.0f}s)")
        print()

    print(f"  Done — {len(all_outputs)} images in {output_dir}")
    return all_outputs


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate portrait variations with SD 1.5 + IPAdapter on 4 GB VRAM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run.py --input portrait.jpg
  python scripts/run.py --input portrait.jpg --count 8 --workflow ipadapter
  python scripts/run.py --input portrait.jpg --workflow img2img  # no custom nodes
  python scripts/run.py --input portrait.jpg --seed 42           # reproducible
        """,
    )
    parser.add_argument("--input",    required=True,        help="Input portrait image path")
    parser.add_argument("--count",    type=int, default=5,  help="Number of variations to generate")
    parser.add_argument("--workflow", default="ipadapter",  choices=["ipadapter", "img2img"],
                        help="Which workflow to use (default: ipadapter)")
    parser.add_argument("--output",   default="outputs/",   help="Output directory")
    parser.add_argument("--seed",     type=int, default=None, help="Fixed seed for reproducibility")
    args = parser.parse_args()

    run(
        input_image=args.input,
        count=args.count,
        workflow_name=args.workflow,
        output_dir=args.output,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
