
from PIL import Image, ImageDraw
from typing import Optional, Dict, Tuple
import os
import argparse

RatioW, RatioH = 4, 5  # 4:5 exact

def _clamp(v, lo, hi):
    return max(lo, min(v, hi))

def _round_int(x: float) -> int:
    return int(round(x))

def _compute_4x5_box_within(W: int, H: int, roi: Tuple[int,int,int,int], anchor: str="center") -> Tuple[int,int,int,int]:
    """
    Given an original image size (W,H) and a ROI (x,y,w,h),
    compute the largest 4:5 box that fits entirely inside the ROI.
    `anchor` can be "center", "topleft", or "top".
    Returns (x,y,w,h) in pixels.
    """
    x0, y0, rw, rh = roi
    x0 = _clamp(x0, 0, W-1)
    y0 = _clamp(y0, 0, H-1)
    rw = _clamp(rw, 1, W - x0)
    rh = _clamp(rh, 1, H - y0)

    # Start from ROI height and compute width for 4:5
    target_w_from_h = (RatioW / RatioH) * rh
    if target_w_from_h <= rw:
        tw = _round_int(target_w_from_h)
        th = _round_int((RatioH / RatioW) * tw)
    else:
        # width is limiting
        tw = rw
        th = _round_int((RatioH / RatioW) * tw)
        if th > rh:
            tw = _round_int((RatioW / RatioH) * rh)
            th = _round_int((RatioH / RatioW) * tw)

    # position inside ROI
    if anchor == "topleft":
        cx, cy = x0, y0
    elif anchor == "top":
        cx = x0 + (rw - tw)//2
        cy = y0
    else:  # center
        cx = x0 + (rw - tw)//2
        cy = y0 + (rh - th)//2

    return (cx, cy, tw, th)

def crop_to_4x5(
    image_path: str,
    _img: Optional[Image.Image] = None,
    save: Optional[bool] = False,
    out_path: Optional[str] = None,
    rel_box: Optional[Dict[str, float]] = None,
    abs_box: Optional[Dict[str, int]] = None,
    anchor: str = "center",
    overlay_path: Optional[str] = None,
    resize_to: Optional[Tuple[int,int]] = None
) -> Dict:
    """
    Crop an image to exact 4:5 within a given ROI (relative or absolute).
    - rel_box: {"x":0..1,"y":0..1,"w":0..1,"h":0..1} relative to original size
    - abs_box: {"x":int,"y":int,"w":int,"h":int} in pixels
    If neither ROI is given, the ROI is the full image.
    anchor: "center" | "topleft" | "top" for how to position 4:5 box within ROI.
    overlay_path: optional path to save an overlay preview with the crop rectangle.
    resize_to: optional (W,H) to resize the final crop (e.g., (1080,1350)).

    Returns a dict with details and output paths.
    """
    
    if (_img): img = _img
    else: img = Image.open(image_path).convert("RGB")
    W, H = img.size

    # Define ROI
    if rel_box is not None:
        x = _round_int(rel_box.get("x", 0) * W)
        y = _round_int(rel_box.get("y", 0) * H)
        w = _round_int(rel_box.get("w", 1) * W)
        h = _round_int(rel_box.get("h", 1) * H)
        roi = (x, y, w, h)
    elif abs_box is not None:
        roi = (abs_box.get("x", 0), abs_box.get("y", 0), abs_box.get("w", W), abs_box.get("h", H))
    else:
        roi = (0, 0, W, H)

    # Compute 4:5 box inside ROI
    x0, y0, cw, ch = _compute_4x5_box_within(W, H, roi, anchor=anchor)

    # Final crop
    crop = img.crop((x0, y0, x0 + cw, y0 + ch))

    # Optional resize (keeps 4:5)
    if resize_to is not None:
        crop = crop.resize(resize_to, Image.Resampling.LANCZOS)

    # Honestamente el resto no me interesa asi que fue
    # me quedo con la foto recortada gracias
    
    if (not save):
        return crop
    
    # Output paths
    if out_path is None:
        base, ext = os.path.splitext(os.path.basename(image_path))
        out_path = f"{base}_crop4x5{ext or '.jpg'}"
    crop.save(out_path, quality=95)

    # Optional overlay
    if overlay_path is not None:
        overlay = img.copy()
        draw = ImageDraw.Draw(overlay)
        draw.rectangle([x0, y0, x0 + cw, y0 + ch], outline=(255, 0, 0), width=4)
        overlay.save(overlay_path, quality=95)

    return {
        "original_size": (W, H),
        "roi": {"x": roi[0], "y": roi[1], "w": roi[2], "h": roi[3]},
        "crop_box": {"x": x0, "y": y0, "w": cw, "h": ch},
        "crop_size": (crop.size[0], crop.size[1]),
        "out_path": out_path,
        "overlay_path": overlay_path,
        "ratio": f"{RatioW}:{RatioH}"
    }

# ---------------- CLI ----------------

def main():
    parser = argparse.ArgumentParser(description="Crop image to exact 4:5 using relative or absolute ROI.")
    parser.add_argument("--image", required=True, help="Path to input image")
    parser.add_argument("--out", default=None, help="Path to save cropped image")
    parser.add_argument("--overlay", default=None, help="Path to save overlay preview")
    parser.add_argument("--anchor", default="center", choices=["center","topleft","top"], help="Anchor of 4:5 box within ROI")
    parser.add_argument("--resize", default=None, help="Optional resize WxH, e.g., 1080x1350")
    parser.add_argument("--rel", default=None, help='Relative ROI as x,y,w,h (0..1), e.g., 0.072,0,0.857,1')
    parser.add_argument("--abs", default=None, help='Absolute ROI as x,y,w,h in px, e.g., 86,0,1029,1286')
    args = parser.parse_args()

    rel_box = None
    abs_box = None

    if args.rel:
        x, y, w, h = [float(v.strip()) for v in args.rel.split(",")]
        rel_box = {"x": x, "y": y, "w": w, "h": h}
    if args.abs:
        x, y, w, h = [int(v.strip()) for v in args.abs.split(",")]
        abs_box = {"x": x, "y": y, "w": w, "h": h}

    resize_to = None
    if args.resize:
        W, H = [int(v.strip()) for v in args.resize.lower().split("x")]
        resize_to = (W, H)

    result = crop_to_4x5(
        image_path=args.image,
        save=True,
        out_path=args.out,
        rel_box=rel_box,
        abs_box=abs_box,
        anchor=args.anchor,
        overlay_path=args.overlay,
        resize_to=resize_to
    )
    print(result)

if __name__ == "__main__":
    main()
