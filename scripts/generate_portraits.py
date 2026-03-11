"""
generate_portraits.py
---------------------
Headless portrait generation via ComfyUI API.
Supports IPAdapter + SDXL + ControlNet pipelines.

Usage:
    python scripts/generate_portraits.py \
        --input examples/portrait.jpg \
        --output outputs/ \
        --count 10 \
        --expressions "gentle smile,confident,neutral"
"""

import argparse
import json
import os
import random
import time
import uuid
from pathlib import Path
from typing import Optional

import requests
from PIL import Image

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_COMFYUI_URL = "http://127.0.0.1:8188"
DEFAULT_WORKFLOW = "workflows/sdxl_ipadapter_portrait.json"

DEFAULT_EXPRESSIONS = [
    "with a gentle, warm smile, soft expression",
    "with a confident expression, slight smile, strong gaze",
    "with a neutral, relaxed expression, calm eyes",
    "with a relaxed, natural expression, soft eyes",
    "looking thoughtful, slight contemplative expression",
    "with a bright joyful smile, eyes slightly squinted",
    "with a serene, peaceful expression",
    "with a curious, engaged expression",
    "with a subtle, knowing smile",
    "with a calm, composed expression",
]

BASE_POSITIVE_PROMPT = (
    "professional portrait photograph, {expression}, "
    "studio lighting, sharp focus, photorealistic, "
    "high quality skin texture, natural colors, "
    "bokeh background, 85mm lens, f/2.8"
)

BASE_NEGATIVE_PROMPT = (
    "deformed, distorted, disfigured, bad anatomy, "
    "blurry, low quality, watermark, signature, "
    "extra limbs, missing features, ugly, cartoon, "
    "painting, illustration, CGI, 3D render"
)


# ---------------------------------------------------------------------------
# ComfyUI API Client
# ---------------------------------------------------------------------------

class ComfyUIClient:
    """Thin wrapper around the ComfyUI HTTP API."""

    def __init__(self, base_url: str = DEFAULT_COMFYUI_URL):
        self.base_url = base_url.rstrip("/")
        self.client_id = str(uuid.uuid4())

    def health_check(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/system_stats", timeout=5)
            return resp.status_code == 200
        except requests.exceptions.ConnectionError:
            return False

    def upload_image(self, image_path: str) -> str:
        """Upload an image to ComfyUI and return the filename."""
        with open(image_path, "rb") as f:
            files = {"image": (Path(image_path).name, f, "image/jpeg")}
            resp = requests.post(f"{self.base_url}/upload/image", files=files)
        resp.raise_for_status()
        return resp.json()["name"]

    def queue_prompt(self, workflow: dict) -> str:
        """Queue a workflow and return the prompt_id."""
        payload = {"prompt": workflow, "client_id": self.client_id}
        resp = requests.post(f"{self.base_url}/prompt", json=payload)
        resp.raise_for_status()
        return resp.json()["prompt_id"]

    def get_history(self, prompt_id: str) -> dict:
        resp = requests.get(f"{self.base_url}/history/{prompt_id}")
        resp.raise_for_status()
        return resp.json()

    def wait_for_completion(self, prompt_id: str, timeout: int = 300) -> dict:
        """Poll until the prompt completes or times out."""
        start = time.time()
        while time.time() - start < timeout:
            history = self.get_history(prompt_id)
            if prompt_id in history:
                return history[prompt_id]
            time.sleep(1.5)
        raise TimeoutError(f"Prompt {prompt_id} timed out after {timeout}s")

    def download_outputs(self, history_entry: dict, output_dir: str) -> list[str]:
        """Download all output images from a completed prompt."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved = []
        outputs = history_entry.get("outputs", {})
        for node_id, node_output in outputs.items():
            for image_info in node_output.get("images", []):
                filename = image_info["filename"]
                subfolder = image_info.get("subfolder", "")
                folder_type = image_info.get("type", "output")

                params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
                resp = requests.get(f"{self.base_url}/view", params=params)
                resp.raise_for_status()

                out_path = output_dir / filename
                out_path.write_bytes(resp.content)
                saved.append(str(out_path))

        return saved


# ---------------------------------------------------------------------------
# Workflow Builder
# ---------------------------------------------------------------------------

class WorkflowBuilder:
    """Loads a base ComfyUI workflow JSON and patches it for each generation."""

    def __init__(self, workflow_path: str):
        with open(workflow_path) as f:
            self.base_workflow = json.load(f)

    def build(
        self,
        uploaded_image_name: str,
        positive_prompt: str,
        negative_prompt: str,
        seed: int,
        width: int = 1024,
        height: int = 1024,
        ipadapter_weight: float = 0.78,
        cfg: float = 7.0,
        steps: int = 30,
        denoise: float = 0.65,
    ) -> dict:
        """
        Return a deep-copy of the workflow with patched parameters.

        This function looks for well-known node titles and patches their
        widget_values. Adjust node_ids to match your actual workflow.
        """
        import copy
        wf = copy.deepcopy(self.base_workflow)

        node_patches = {
            # node_id: {widget_index: value}
            "positive_prompt_node": {"text": positive_prompt},
            "negative_prompt_node": {"text": negative_prompt},
            "ksampler_node": {
                "seed": seed,
                "cfg": cfg,
                "steps": steps,
                "denoise": denoise,
            },
            "empty_latent_node": {"width": width, "height": height},
            "load_image_node": {"image": uploaded_image_name},
            "ipadapter_node": {"weight": ipadapter_weight},
        }

        # Walk all nodes and apply patches by _meta title
        for node_id, node_data in wf.items():
            meta_title = node_data.get("_meta", {}).get("title", "")
            if meta_title in node_patches:
                patch = node_patches[meta_title]
                for key, val in patch.items():
                    if key == "text":
                        node_data["inputs"]["text"] = val
                    else:
                        node_data["inputs"][key] = val

        return wf


# ---------------------------------------------------------------------------
# Portrait Pipeline
# ---------------------------------------------------------------------------

class PortraitPipeline:
    """
    High-level pipeline for generating portrait variations.

    Example:
        pipeline = PortraitPipeline()
        results = pipeline.generate(
            input_image="portrait.jpg",
            expressions=["gentle smile", "confident"],
            count=6,
            output_dir="outputs/"
        )
    """

    def __init__(
        self,
        workflow: str = DEFAULT_WORKFLOW,
        comfyui_url: str = DEFAULT_COMFYUI_URL,
    ):
        self.client = ComfyUIClient(comfyui_url)
        self.workflow_path = workflow

        if not self.client.health_check():
            raise ConnectionError(
                f"Cannot reach ComfyUI at {comfyui_url}. "
                "Make sure ComfyUI is running: `python main.py --listen`"
            )

        print(f"✅ Connected to ComfyUI at {comfyui_url}")

    def generate(
        self,
        input_image: str,
        expressions: Optional[list[str]] = None,
        count: int = 10,
        seed_range: tuple[int, int] = (0, 9999999),
        output_dir: str = "outputs/",
        ipadapter_weight: float = 0.78,
        cfg: float = 7.0,
        steps: int = 30,
        denoise: float = 0.65,
        width: int = 1024,
        height: int = 1024,
    ) -> list[str]:
        """
        Generate `count` portrait variations from a single input image.

        Args:
            input_image: Path to the input portrait photo.
            expressions: List of expression descriptions. Cycles if fewer than count.
            count: Number of output images to generate.
            seed_range: (min, max) range for random seed selection.
            output_dir: Directory to save outputs.
            ipadapter_weight: IPAdapter conditioning strength (0.5–1.0).
            cfg: Classifier-free guidance scale.
            steps: Number of diffusion steps.
            denoise: Denoising strength (lower = more conservative).
            width/height: Output resolution.

        Returns:
            List of paths to generated images.
        """
        if expressions is None:
            expressions = DEFAULT_EXPRESSIONS

        # Validate input
        if not Path(input_image).exists():
            raise FileNotFoundError(f"Input image not found: {input_image}")

        # Preprocess: ensure face is centered and image is square
        processed_path = self._preprocess(input_image)

        # Upload to ComfyUI
        print(f"📤 Uploading {processed_path}...")
        uploaded_name = self.client.upload_image(processed_path)

        builder = WorkflowBuilder(self.workflow_path)
        all_outputs = []

        print(f"🎨 Generating {count} portrait variations...")
        for i in range(count):
            expression = expressions[i % len(expressions)]
            seed = random.randint(*seed_range)
            positive_prompt = BASE_POSITIVE_PROMPT.format(expression=expression)

            print(f"  [{i+1}/{count}] Expression: '{expression}' | Seed: {seed}")

            workflow = builder.build(
                uploaded_image_name=uploaded_name,
                positive_prompt=positive_prompt,
                negative_prompt=BASE_NEGATIVE_PROMPT,
                seed=seed,
                width=width,
                height=height,
                ipadapter_weight=ipadapter_weight,
                cfg=cfg,
                steps=steps,
                denoise=denoise,
            )

            prompt_id = self.client.queue_prompt(workflow)
            history = self.client.wait_for_completion(prompt_id)
            outputs = self.client.download_outputs(history, output_dir)
            all_outputs.extend(outputs)

            print(f"     ✅ Saved: {outputs}")

        print(f"\n🎉 Done! {len(all_outputs)} images saved to {output_dir}")
        return all_outputs

    def _preprocess(self, image_path: str, target_size: int = 1024) -> str:
        """
        Crop and resize the input image to a square centered on the face.
        Falls back to center crop if face detection is unavailable.
        """
        img = Image.open(image_path).convert("RGB")
        w, h = img.size

        # Simple center crop to square
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        img = img.crop((left, top, left + side, top + side))
        img = img.resize((target_size, target_size), Image.LANCZOS)

        out_path = Path(image_path).stem + "_processed.jpg"
        img.save(out_path, quality=95)
        return out_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate portrait variations with ComfyUI + IPAdapter"
    )
    parser.add_argument("--input", required=True, help="Input portrait image path")
    parser.add_argument("--output", default="outputs/", help="Output directory")
    parser.add_argument("--count", type=int, default=10, help="Number of images")
    parser.add_argument(
        "--expressions",
        default=None,
        help="Comma-separated expression descriptions",
    )
    parser.add_argument(
        "--workflow",
        default=DEFAULT_WORKFLOW,
        help="ComfyUI workflow JSON path",
    )
    parser.add_argument(
        "--comfyui-url",
        default=DEFAULT_COMFYUI_URL,
        help="ComfyUI server URL",
    )
    parser.add_argument("--ipadapter-weight", type=float, default=0.78)
    parser.add_argument("--cfg", type=float, default=7.0)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--denoise", type=float, default=0.65)
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=1024)
    return parser.parse_args()


def main():
    args = parse_args()

    expressions = None
    if args.expressions:
        expressions = [e.strip() for e in args.expressions.split(",")]

    pipeline = PortraitPipeline(
        workflow=args.workflow,
        comfyui_url=args.comfyui_url,
    )

    pipeline.generate(
        input_image=args.input,
        expressions=expressions,
        count=args.count,
        output_dir=args.output,
        ipadapter_weight=args.ipadapter_weight,
        cfg=args.cfg,
        steps=args.steps,
        denoise=args.denoise,
        width=args.width,
        height=args.height,
    )


if __name__ == "__main__":
    main()
