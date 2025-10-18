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
    logo_path: Optional[str] = None,
    logo_scale: float = 0.10,
) -> np.ndarray:
    """
    Create text overlay with same style as image generator.
    Includes logo in top-right corner (EXACT same as generate_image_api.py).
    Returns RGBA numpy array.
    """
    # Create transparent overlay
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    if not headline:
        return np.array(overlay)
    
    # Font sizes - ajustados según el aspecto del video
    # Si es horizontal (width > height), usar fuentes más grandes
    if width > height:
        # Formato horizontal (como las imágenes)
        main_font_size = max(12, int(height * 0.06))
        side_font_size = max(8, int(height * 0.03))
    else:
        # Formato vertical (9:16)
        main_font_size = max(12, int(height * 0.038))
        side_font_size = max(8, int(height * 0.022))
    
    font_bold = _load_font_for_video(main_font_size, bold=True)
    font_reg = _load_font_for_video(main_font_size, bold=False)
    font_side = _load_font_for_video(side_font_size, bold=False)
    
    # Draw watermark on left side
    # Ajustar bar_width según formato (igual que generate_image_api.py)
    if width > height:
        # Formato horizontal
        bar_width = int(width * 0.07)
    else:
        # Formato vertical
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
    
    # Load and paste logo in top-right corner (EXACT SAME as generate_image_api.py)
    # IMPORTANTE: Preservar colores originales del logo
    logo_image = None
    if logo_path:
        try:
            # Cargar logo SIN convertir primero, para preservar colores
            logo_temp = Image.open(logo_path)
            # Si tiene transparencia, mantenerla; si no, agregarla
            if logo_temp.mode == 'RGBA':
                logo_image = logo_temp
            elif logo_temp.mode == 'RGB':
                # Crear canal alpha basado en la imagen
                logo_image = logo_temp.convert('RGBA')
            else:
                logo_image = logo_temp.convert('RGBA')
        except Exception as e:
            print(f"⚠️  No se pudo cargar logo desde {logo_path}: {e}")
    
    if logo_image is None:
        # Try to load default logo from current directory or script directory
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_paths = [
            'El_Dia.png',
            os.path.join(script_dir, 'El_Dia.png'),
            '/Users/fcolabbe/Downloads/imagen/El_Dia.png'
        ]
        for path in default_paths:
            try:
                # Cargar logo preservando colores originales
                logo_temp = Image.open(path)
                if logo_temp.mode == 'RGBA':
                    logo_image = logo_temp
                elif logo_temp.mode == 'RGB':
                    logo_image = logo_temp.convert('RGBA')
                else:
                    logo_image = logo_temp.convert('RGBA')
                print(f"✅ Logo cargado desde: {path} (modo: {logo_temp.mode})")
                break
            except:
                continue
    
    if logo_image is not None:
        logo_w = int(width * logo_scale)
        # Maintain aspect ratio
        logo_h = int(logo_w * logo_image.height / logo_image.width)
        # Resize con LANCZOS para mejor calidad y preservar colores
        logo_resized = logo_image.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
        # Paste usando el logo como máscara de transparencia para preservar colores
        overlay.paste(logo_resized, (width - logo_w - 10, 10), logo_resized)
        print(f"📸 Logo añadido: {logo_w}x{logo_h} en esquina superior derecha")
    else:
        print("⚠️  Logo no encontrado, video sin logo")
    
    # Process text with highlights (EXACT SAME LOGIC as generate_image_api.py)
    # Ajustar available_width según formato (igual que generate_image_api.py)
    if width > height:
        # Formato horizontal
        available_width = width - bar_width - 20
    else:
        # Formato vertical
        available_width = width - bar_width - 10
    
    draw_dummy = ImageDraw.Draw(Image.new('RGB', (10, 10)))
    
    # Create a character-by-character map of which characters are highlighted
    highlight_mask = [False] * len(headline)
    if highlight and highlight in headline:
        highlight_start = headline.find(highlight)
        highlight_end = highlight_start + len(highlight)
        for i in range(highlight_start, highlight_end):
            if i < len(headline):
                highlight_mask[i] = True
    
    # Word-based wrapping that preserves exact highlight positions and doesn't cut words
    def wrap_text_with_highlights(text, highlight_mask, font, max_width):
        """Wrap text by words while preserving exact character-level highlight information."""
        
        def calculate_real_width(text_str, highlights_list):
            """Calculate the REAL width as it will be drawn, char by char with correct fonts."""
            total_width = 0
            for i, char in enumerate(text_str):
                is_highlighted = i < len(highlights_list) and highlights_list[i]
                char_font = font_bold if is_highlighted else font_reg
                total_width += draw_dummy.textlength(char, font=char_font)
            return total_width
        
        lines = []
        words = text.split()  # Split by whitespace
        
        current_line_words = []
        current_line_highlights = []
        char_position = 0
        
        for word in words:
            # Find the word's position in the original text
            word_start = text.find(word, char_position)
            word_end = word_start + len(word)
            
            # Get highlight info for this word
            word_highlight_chars = []
            for i in range(word_start, word_end):
                if i < len(highlight_mask):
                    word_highlight_chars.append(highlight_mask[i])
                else:
                    word_highlight_chars.append(False)
            
            # Build candidate line with proper spacing
            if current_line_words:
                candidate_text = " ".join(current_line_words + [word])
                candidate_highlights = current_line_highlights + [False] + word_highlight_chars  # False for space
            else:
                candidate_text = word
                candidate_highlights = word_highlight_chars
            
            # Calculate REAL width as it will be rendered
            candidate_width = calculate_real_width(candidate_text, candidate_highlights)
            
            # Be VERY conservative - use 80% of available width with safety margin
            if candidate_width * 1.15 <= max_width:  # 15% safety margin
                current_line_words.append(word)
                if current_line_highlights:
                    current_line_highlights.append(False)  # Add space highlight
                current_line_highlights.extend(word_highlight_chars)
            else:
                # Line is full, save it and start new line
                if current_line_words:
                    line_text = " ".join(current_line_words)
                    lines.append((line_text, current_line_highlights))
                
                # Start new line with current word
                current_line_words = [word]
                current_line_highlights = word_highlight_chars
            
            # Update character position
            char_position = word_end
        
        # Add the last line
        if current_line_words:
            line_text = " ".join(current_line_words)
            lines.append((line_text, current_line_highlights))
        
        return lines
    
    # Wrap the headline with variable line widths - calculate real width char by char
    # Usar el mismo wrap_factor que generate_image_api.py
    wrap_factor = 0.85  # Factor estándar para todos los formatos
    wrapped_lines = wrap_text_with_highlights(headline, highlight_mask, font_reg, available_width * wrap_factor)
    
    # Calculate dimensions for each line
    padding_x = 20
    padding_y = 10
    line_spacing = 8
    line_heights = []
    line_widths = []
    
    # Helper function to calculate real width char by char (same logic as in wrapping)
    def calculate_line_real_width(text_str, highlights_list):
        """Calculate the REAL width as it will be drawn, char by char with correct fonts."""
        total_width = 0
        for i, char in enumerate(text_str):
            is_highlighted = i < len(highlights_list) and highlights_list[i]
            char_font = font_bold if is_highlighted else font_reg
            total_width += draw_dummy.textlength(char, font=char_font)
        return total_width
    
    for line_text, line_highlights in wrapped_lines:
        # Calculate REAL width considering bold and regular characters
        real_width = calculate_line_real_width(line_text, line_highlights)
        line_widths.append(real_width)
        
        # Height can use regular font as reference
        bbox = draw_dummy.textbbox((0, 0), line_text, font=font_reg)
        line_heights.append(bbox[3] - bbox[1])
    
    # Calculate total height
    total_boxes_height = sum(h + 2 * padding_y for h in line_heights)
    total_boxes_height += line_spacing * (len(wrapped_lines) - 1)
    start_y = height - total_boxes_height - 20
    current_y = start_y
    
    # Draw each line with variable width and centered
    for idx, (line_text, line_highlights) in enumerate(wrapped_lines):
        text_w = line_widths[idx]
        text_h = line_heights[idx]
        box_w = text_w + 2 * padding_x
        box_h = text_h + 2 * padding_y
        
        # Center each line individually within the available space
        x = bar_width + (available_width - box_w) // 2
        y = current_y
        
        # Draw box
        draw.rectangle([x, y, x + box_w, y + box_h], fill=box_color)
        
        # Draw text character by character with appropriate colors and fonts
        text_x = x + padding_x
        
        # Calculate baseline offset to align bold and regular text
        regular_bbox = draw_dummy.textbbox((0, 0), "Ay", font=font_reg)
        bold_bbox = draw_dummy.textbbox((0, 0), "Ay", font=font_bold)
        regular_baseline = regular_bbox[3]  # bottom of regular font
        bold_baseline = bold_bbox[3]  # bottom of bold font
        baseline_offset = regular_baseline - bold_baseline
        
        # Calculate vertical centering - get actual text height
        text_bbox = draw_dummy.textbbox((0, 0), line_text, font=font_reg)
        actual_text_height = text_bbox[3] - text_bbox[1]
        
        # Center text vertically in the box
        text_y_offset = y + padding_y + (box_h - 2 * padding_y - actual_text_height) // 2
        
        for char_idx, char in enumerate(line_text):
            # Check if this character is highlighted
            is_highlighted = char_idx < len(line_highlights) and line_highlights[char_idx]
            color = highlight_color if is_highlighted else text_color
            font = font_bold if is_highlighted else font_reg
            
            # Adjust Y position for bold text to align with regular text + vertical centering
            y_position = text_y_offset + (baseline_offset if is_highlighted else 0)
            
            # Draw the character
            draw.text((text_x, y_position), char, font=font, fill=color)
            
            # Move x position (use the correct font for width calculation)
            char_width = draw_dummy.textlength(char, font=font)
            text_x += char_width
        
        # Move to next line
        current_y += box_h + line_spacing
    
    return np.array(overlay)


def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file in seconds using ffmpeg."""
    import subprocess
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        # Si no se puede obtener la duración, retornar None
        return None


def make_pan_scan_video(
    output_path: str,
    image_input,  # Can be path (str) or PIL Image
    headline: Optional[str] = None,
    highlight: Optional[str] = None,
    duration: float = 5.0,
    out_w: Optional[int] = None,
    out_h: Optional[int] = None,
    fps: int = 30,
    direction: str = "left-to-right",
    zoom_start: float = 1.0,
    zoom_end: float = 1.0,
    ease_in_out: bool = True,
    audio_path: Optional[str] = None,
    keep_aspect: bool = True,
):
    """
    Generate a video file with cinematic Pan & Scan effect.
    
    Args:
        output_path: Path where to save the video file
        image_input: Image path (str) or PIL Image object
        headline: Text headline to overlay
        highlight: Part of headline to highlight in bold/color
        duration: Video duration in seconds (si hay audio, se ajusta a la duración del audio)
        out_w: Output video width (None = usar ancho original)
        out_h: Output video height (None = usar alto original)
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
            Si se proporciona, la duración del video se ajusta a la del audio
        keep_aspect: Si True, mantiene el aspecto original de la imagen (ignora out_w/out_h)
    """
    # Si hay audio, ajustar la duración del video a la duración del audio
    if audio_path:
        audio_duration = get_audio_duration(audio_path)
        if audio_duration:
            duration = audio_duration
            print(f"📏 Ajustando duración del video a {duration:.2f}s (duración del audio)")
    
    base = load_image_cv2(image_input)
    
    # Si keep_aspect es True, usar dimensiones originales de la imagen
    if keep_aspect:
        out_h, out_w = base.shape[:2]
        print(f"📐 Manteniendo aspecto original: {out_w}x{out_h}")
    elif out_w is None or out_h is None:
        # Si no se especifican dimensiones, usar las originales
        out_h, out_w = base.shape[:2]
        print(f"📐 Usando dimensiones originales: {out_w}x{out_h}")
    
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
            # No usamos -shortest porque el video ya tiene la duración del audio
            cmd = [
                'ffmpeg',
                '-y',  # Sobrescribir archivo de salida
                '-i', temp_video_path,  # Video input
                '-i', audio_path,  # Audio input
                '-c:v', 'copy',  # Copiar video sin re-encodear
                '-c:a', 'aac',  # Codec de audio
                '-b:a', '192k',  # Bitrate de audio
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

