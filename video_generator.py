"""
Video Generator with Pan & Scan Effect
Generates cinematic videos from images with text overlays
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio
from typing import Optional, Tuple
import platform


def load_image_cv2(image_path_or_pil) -> np.ndarray:
    """Load image from path or PIL Image, return as BGR numpy array."""
    if isinstance(image_path_or_pil, str):
        img = cv2.imread(image_path_or_pil)
        if img is None:
            raise ValueError(f"Could not load image: {image_path_or_pil}")
        return img
    elif isinstance(image_path_or_pil, Image.Image):
        # Convert PIL to OpenCV BGR
        img_rgb = np.array(image_path_or_pil.convert('RGB'))
        return cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    else:
        raise ValueError("Input must be file path or PIL Image")


def resize_cover(img: np.ndarray, target_w: int, target_h: int) -> np.ndarray:
    """Resize image to cover target dimensions (like CSS background-size: cover)."""
    h, w = img.shape[:2]
    scale = max(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    
    # Center crop
    x = (new_w - target_w) // 2
    y = (new_h - target_h) // 2
    return resized[y:y+target_h, x:x+target_w]


def smoothstep(x: float) -> float:
    """Smooth easing function (ease-in-out)."""
    return x * x * (3 - 2 * x)


def make_affine_matrix(tx: float, ty: float, zoom: float, angle: float, cx: float, cy: float) -> np.ndarray:
    """Create 2D affine transformation matrix."""
    A = np.eye(3, dtype=np.float32)
    
    # Translate to origin
    A[0, 2] = -cx
    A[1, 2] = -cy
    
    # Scale (zoom)
    S = np.eye(3, dtype=np.float32)
    S[0, 0] = zoom
    S[1, 1] = zoom
    A = S @ A
    
    # Rotate
    if angle != 0:
        rad = np.deg2rad(angle)
        cos_a, sin_a = np.cos(rad), np.sin(rad)
        R = np.array([
            [cos_a, -sin_a, 0],
            [sin_a, cos_a, 0],
            [0, 0, 1]
        ], dtype=np.float32)
        A = R @ A
    
    # Translate back + pan
    A[0, 2] += cx + tx
    A[1, 2] += cy + ty
    
    return A


def affine_to_perspective(A: np.ndarray) -> np.ndarray:
    """Convert 3x3 affine to OpenCV 2x3 perspective matrix."""
    return A[:2, :]


def apply_transform(img: np.ndarray, M: np.ndarray, output_size: Tuple[int, int]) -> np.ndarray:
    """Apply affine transformation to image."""
    return cv2.warpAffine(img, M, output_size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def apply_overlay(base: np.ndarray, overlay: np.ndarray) -> np.ndarray:
    """Apply RGBA overlay onto BGR base image."""
    if overlay.shape[2] == 4:  # RGBA
        alpha = overlay[:, :, 3:4] / 255.0
        overlay_rgb = overlay[:, :, :3]
        base = base * (1 - alpha) + overlay_rgb * alpha
    else:  # RGB
        base = overlay
    return base.astype(np.uint8)


def _load_font_for_video(size: int, bold: bool = False):
    """Load font for video overlay (similar to image generator)."""
    system = platform.system()
    
    # Try system fonts based on OS
    if system == "Darwin":  # macOS
        font_paths = [
            ("/System/Library/Fonts/Helvetica.ttc", 0 if not bold else 1),
            ("/System/Library/Fonts/SFNSText.ttf", None),
            ("/Library/Fonts/Arial.ttf", None),
        ]
    else:  # Linux
        font_paths = [
            ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", None),
            ("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", None),
        ]
    
    for font_path, index in font_paths:
        try:
            if index is not None:
                return ImageFont.truetype(font_path, size, index=index)
            else:
                return ImageFont.truetype(font_path, size)
        except:
            continue
    
    # Fallback
    try:
        return ImageFont.load_default()
    except:
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)


def create_text_overlay(
    width: int,
    height: int,
    headline: Optional[str] = None,
    highlight: Optional[str] = None,
    watermark: str = "diarioeldia.cl",
    highlight_color: Tuple[int, int, int] = (0, 64, 145),
    text_color: Tuple[int, int, int] = (0, 0, 0),
    box_color: Tuple[int, int, int, int] = (255, 255, 255, 230),
) -> np.ndarray:
    """
    Create text overlay with same style as image generator.
    Returns RGBA numpy array.
    """
    # Create transparent overlay
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    if not headline:
        return np.array(overlay)
    
    # Font sizes for video (9:16 format - 1080x1920)
    main_font_size = max(12, int(height * 0.038))
    side_font_size = max(8, int(height * 0.022))
    
    font_bold = _load_font_for_video(main_font_size, bold=True)
    font_reg = _load_font_for_video(main_font_size, bold=False)
    font_side = _load_font_for_video(side_font_size, bold=False)
    
    # Draw watermark on left side
    bar_width = int(width * 0.05)
    temp = Image.new('RGBA', (height, bar_width), (0, 0, 0, 0))
    draw_temp = ImageDraw.Draw(temp)
    phrase = watermark + '   '
    phrase_width = draw_temp.textlength(phrase, font=font_side)
    repeats = int((height / phrase_width)) + 3
    full_text = phrase * repeats
    y_offset = (bar_width - font_side.getbbox('Ay')[3]) // 2
    draw_temp.text((0, y_offset), full_text, font=font_side, fill=(255, 255, 255, 150))
    vertical_img = temp.rotate(90, expand=True)
    overlay.paste(vertical_img, (0, 0), vertical_img)
    
    # Process text with highlights (simplified version)
    available_width = width - bar_width - 10
    
    # Simple word wrapping (without cutting words)
    words = headline.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font_reg)
        test_width = bbox[2] - bbox[0]
        
        if test_width <= available_width * 0.90:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(" ".join(current_line))
    
    # Calculate text position (centered vertically)
    padding_x = 20
    padding_y = 10
    line_spacing = 8
    line_height = font_reg.getbbox('Ay')[3]
    total_height = len(lines) * (line_height + 2 * padding_y + line_spacing)
    start_y = (height - total_height) // 2
    
    # Draw text boxes
    current_y = start_y
    
    for line_text in lines:
        # Calculate line dimensions
        bbox = draw.textbbox((0, 0), line_text, font=font_reg)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        box_w = text_w + 2 * padding_x
        box_h = text_h + 2 * padding_y
        
        # Center horizontally
        x = bar_width + (available_width - box_w) // 2
        y = current_y
        
        # Draw box
        draw.rectangle([x, y, x + box_w, y + box_h], fill=box_color)
        
        # Draw text with highlights
        text_x = x + padding_x
        text_y = y + padding_y
        
        if highlight and highlight in line_text:
            # Split and draw with highlight
            parts = line_text.split(highlight)
            for i, part in enumerate(parts):
                if i > 0:
                    # Draw highlight
                    draw.text((text_x, text_y), highlight, font=font_bold, fill=highlight_color)
                    text_x += draw.textlength(highlight, font=font_bold)
                # Draw regular part
                if part:
                    draw.text((text_x, text_y), part, font=font_reg, fill=text_color)
                    text_x += draw.textlength(part, font=font_reg)
        else:
            # Draw regular text
            draw.text((text_x, text_y), line_text, font=font_reg, fill=text_color)
        
        current_y += box_h + line_spacing
    
    return np.array(overlay)


def make_pan_scan_video(
    output_path: str,
    image_input,  # Can be path (str) or PIL Image
    headline: Optional[str] = None,
    highlight: Optional[str] = None,
    duration: float = 5.0,
    out_w: int = 1080,
    out_h: int = 1920,
    fps: int = 30,
    direction: str = "left-to-right",
    zoom_start: float = 1.0,
    zoom_end: float = 1.0,
    ease_in_out: bool = True,
    audio_path: Optional[str] = None,
):
    """
    Generate a video file with cinematic Pan & Scan effect.
    
    Args:
        output_path: Path where to save the video file
        image_input: Image path (str) or PIL Image object
        headline: Text headline to overlay
        highlight: Part of headline to highlight in bold/color
        duration: Video duration in seconds
        out_w: Output video width (default 1080 for 9:16)
        out_h: Output video height (default 1920 for 9:16)
        fps: Frames per second
        direction: Pan direction
            - "left-to-right", "right-to-left"
            - "top-to-bottom", "bottom-to-top"
            - "diagonal-tl-br", "diagonal-tr-bl"
            - "zoom-in", "zoom-out"
        zoom_start: Initial zoom level
        zoom_end: Final zoom level
        ease_in_out: Apply smooth easing
        audio_path: Optional path to audio file (mp3, wav, etc.)
    """
    base = load_image_cv2(image_input)
    
    # Calculate margins based on direction
    if direction in ["left-to-right", "right-to-left"]:
        margin_w = 1.25
        margin_h = 1.0
    elif direction in ["top-to-bottom", "bottom-to-top"]:
        margin_w = 1.0
        margin_h = 1.25
    elif "diagonal" in direction:
        margin_w = 1.20
        margin_h = 1.20
    else:  # zoom
        margin_w = 1.15
        margin_h = 1.15
    
    base_cov = resize_cover(base, int(out_w * margin_w), int(out_h * margin_h))
    H, W = base_cov.shape[:2]
    cx, cy = W / 2.0, H / 2.0
    
    max_pan_x = (W - out_w) / 2.0 * 0.7
    max_pan_y = (H - out_h) / 2.0 * 0.7
    
    # Create static text overlay
    text_overlay = create_text_overlay(out_w, out_h, headline, highlight)
    
    # Calculate total frames
    total_frames = int(duration * fps)
    
    # Generate all frames
    frames = []
    for frame_num in range(total_frames):
        t = frame_num / fps
        p = t / duration
        
        if ease_in_out:
            p = smoothstep(p)
        
        zoom = zoom_start + (zoom_end - zoom_start) * p
        
        # Calculate pan based on direction
        if direction == "left-to-right":
            tx = -max_pan_x + (2 * max_pan_x * p)
            ty = 0
        elif direction == "right-to-left":
            tx = max_pan_x - (2 * max_pan_x * p)
            ty = 0
        elif direction == "top-to-bottom":
            tx = 0
            ty = -max_pan_y + (2 * max_pan_y * p)
        elif direction == "bottom-to-top":
            tx = 0
            ty = max_pan_y - (2 * max_pan_y * p)
        elif direction == "diagonal-tl-br":
            tx = -max_pan_x + (2 * max_pan_x * p)
            ty = -max_pan_y + (2 * max_pan_y * p)
        elif direction == "diagonal-tr-bl":
            tx = max_pan_x - (2 * max_pan_x * p)
            ty = -max_pan_y + (2 * max_pan_y * p)
        elif direction == "zoom-in":
            tx = 0
            ty = 0
            zoom = 1.0 + (0.2 * p)
        elif direction == "zoom-out":
            tx = 0
            ty = 0
            zoom = 1.2 - (0.2 * p)
        else:
            tx = 0
            ty = 0
        
        # Apply transform
        A = make_affine_matrix(tx, ty, zoom, 0, cx, cy)
        M = affine_to_perspective(A)
        frame = apply_transform(base_cov, M, (W, H))
        
        # Center crop
        x0 = (W - out_w) // 2
        y0 = (H - out_h) // 2
        frame = frame[y0:y0 + out_h, x0:x0 + out_w]
        
        # Apply text overlay
        frame = apply_overlay(frame, text_overlay)
        
        # Convert BGR to RGB
        frame_rgb = frame[:, :, ::-1]
        frames.append(frame_rgb)
    
    # Write video using imageio with ffmpeg
    if audio_path:
        # Si hay audio, primero guardamos el video sin audio
        temp_video_path = output_path.replace('.mp4', '_temp.mp4')
        imageio.mimsave(
            temp_video_path,
            frames,
            fps=fps,
            codec='libx264',
            pixelformat='yuv420p',
            output_params=['-crf', '23', '-preset', 'medium']
        )
        
        # Luego mezclamos video con audio usando ffmpeg
        import subprocess
        import os
        
        try:
            # Comando ffmpeg para mezclar video y audio
            cmd = [
                'ffmpeg',
                '-y',  # Sobrescribir archivo de salida
                '-i', temp_video_path,  # Video input
                '-i', audio_path,  # Audio input
                '-c:v', 'copy',  # Copiar video sin re-encodear
                '-c:a', 'aac',  # Codec de audio
                '-b:a', '192k',  # Bitrate de audio
                '-shortest',  # Terminar cuando el stream más corto termine
                output_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Eliminar video temporal
            os.remove(temp_video_path)
            
        except subprocess.CalledProcessError as e:
            # Si falla, renombrar el video temporal como salida
            import shutil
            shutil.move(temp_video_path, output_path)
            print(f"Warning: Could not add audio. Video saved without audio: {e}")
        except FileNotFoundError:
            # ffmpeg no está instalado
            import shutil
            shutil.move(temp_video_path, output_path)
            print("Warning: ffmpeg not found. Video saved without audio.")
    else:
        # Sin audio, guardar directamente
        imageio.mimsave(
            output_path,
            frames,
            fps=fps,
            codec='libx264',
            pixelformat='yuv420p',
            output_params=['-crf', '23', '-preset', 'medium']
        )

