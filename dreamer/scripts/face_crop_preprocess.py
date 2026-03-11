"""
face_crop_preprocess.py
-----------------------
Detects and crops a face from an input image,
centering it for optimal diffusion model input.

Falls back to center-crop if InsightFace is unavailable.
"""

import sys
from pathlib import Path
import numpy as np
from PIL import Image


def try_insightface_crop(image_path: str, padding: float = 0.35) -> tuple | None:
    """
    Use InsightFace to detect the face bounding box.
    Returns (x1, y1, x2, y2) or None if detection fails.
    """
    try:
        import insightface
        from insightface.app import FaceAnalysis
    except ImportError:
        return None

    try:
        app = FaceAnalysis(providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
        app.prepare(ctx_id=0, det_size=(640, 640))

        img = np.array(Image.open(image_path).convert("RGB"))
        faces = app.get(img)

        if not faces:
            print("  ⚠️  No face detected by InsightFace — falling back to center crop")
            return None

        # Use the largest detected face
        face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        x1, y1, x2, y2 = face.bbox.astype(int)

        # Add padding around face
        w, h = x2 - x1, y2 - y1
        pad_x = int(w * padding)
        pad_y = int(h * padding)

        img_h, img_w = img.shape[:2]
        x1 = max(0, x1 - pad_x)
        y1 = max(0, y1 - pad_y * 2)  # extra headroom above
        x2 = min(img_w, x2 + pad_x)
        y2 = min(img_h, y2 + pad_y)

        return (x1, y1, x2, y2)

    except Exception as e:
        print(f"  ⚠️  InsightFace error: {e} — falling back to center crop")
        return None


def center_crop_square(image: Image.Image) -> Image.Image:
    """Simple center crop to square."""
    w, h = image.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return image.crop((left, top, left + side, top + side))


def preprocess(
    input_path: str,
    output_path: str | None = None,
    target_size: int = 1024,
    use_face_detection: bool = True,
) -> str:
    """
    Crop and resize input image, centering on detected face.

    Args:
        input_path: Input image path.
        output_path: Output path. If None, appends '_processed' to input stem.
        target_size: Output resolution (square).
        use_face_detection: Whether to use InsightFace for smart cropping.

    Returns:
        Path to processed image.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    if output_path is None:
        output_path = input_path.stem + "_processed.jpg"

    img = Image.open(input_path).convert("RGB")
    print(f"📸 Input: {img.size[0]}×{img.size[1]} — {input_path.name}")

    # Try face-aware crop
    bbox = None
    if use_face_detection:
        bbox = try_insightface_crop(str(input_path))

    if bbox:
        x1, y1, x2, y2 = bbox
        # Make square crop around face
        crop_w = x2 - x1
        crop_h = y2 - y1
        side = max(crop_w, crop_h)
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        half = side // 2
        img = img.crop((
            max(0, cx - half),
            max(0, cy - half),
            min(img.width, cx + half),
            min(img.height, cy + half),
        ))
        print(f"  ✅ Face-aware crop applied")
    else:
        img = center_crop_square(img)
        print(f"  ℹ️  Center crop applied")

    img = img.resize((target_size, target_size), Image.LANCZOS)
    img.save(output_path, quality=95)
    print(f"  💾 Saved: {output_path} ({target_size}×{target_size})")

    return str(output_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Preprocess portrait for generation")
    parser.add_argument("--input", required=True, help="Input image path")
    parser.add_argument("--output", default=None, help="Output image path")
    parser.add_argument("--size", type=int, default=1024, help="Output size (square)")
    parser.add_argument("--no-face-detect", action="store_true")
    args = parser.parse_args()

    preprocess(
        args.input,
        args.output,
        target_size=args.size,
        use_face_detection=not args.no_face_detect,
    )
