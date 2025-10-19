"""A small FastAPI application to generate a news-style composite image.

This module exposes a single API endpoint `/generate-image` that accepts
an image file along with the headline and a highlighted portion of that
headline. It returns a composite image where:

* The provided photo is used as the background.
* A vertical strip along the left edge displays a repeated watermark text
  (by default `diarioeldia.cl`).
* The supplied highlight text is rendered on its own line in a blue font.
* The remainder of the headline is wrapped across one or more lines,
  each rendered in black. Each line is drawn on its own white box, and
  the lengths of the boxes adjust to the length of the text.
* A logo is placed in the top-right corner; by default this module
  expects a file named ``El_Dia.png`` to reside in the same directory
  as this script. You can override it by uploading a separate logo.

The API returns the resulting image as a PNG.

Example usage (with curl):

  curl -X POST -F "headline=La rayuela se tomó Paihuano: clubes de la comuna y de Vicuña animaron cuadrangular" \\
       -F "highlight=La rayuela se tomó Paihuano:" \\
       -F "image=@/path/to/your/photo.jpg" \\
       http://localhost:8000/generate-image --output result.png

Note: This script relies on FastAPI and uvicorn for serving the API. To
run the server, execute this file directly:

  python generate_image_api.py

Then visit http://127.0.0.1:8000/docs for an interactive Swagger UI.
"""

from __future__ import annotations

import io
import os
import uuid
from datetime import datetime
from typing import Optional

import requests
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont

# Importar configuración
from config import BASE_URL, PUBLIC_IMAGES_DIR, APP_NAME, APP_DESCRIPTION
from video_generator import make_pan_scan_video, make_static_video_with_audio

app = FastAPI(title=APP_NAME, description=APP_DESCRIPTION)

# Crear directorio de imágenes públicas si no existe
os.makedirs(PUBLIC_IMAGES_DIR, exist_ok=True)

# Crear directorio de videos públicos
PUBLIC_VIDEOS_DIR = "/var/www/fastapi-image-generator/public/videos"
os.makedirs(PUBLIC_VIDEOS_DIR, exist_ok=True)


def _save_image_and_get_url(image: Image.Image) -> str:
    """Save image to public directory and return public URL."""
    # Generar nombre único para la imagen
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"generated_{timestamp}_{unique_id}.png"
    
    # Guardar imagen
    filepath = os.path.join(PUBLIC_IMAGES_DIR, filename)
    image.save(filepath, format='PNG')
    
    # Retornar URL pública
    return f"{BASE_URL}/public/images/{filename}"


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a font at the requested size.

    Attempts to load DejaVuSans on Linux or falls back to system fonts
    on macOS and other platforms.

    Args:
        size: Font size in points.
        bold: Whether to load the bold variant.

    Returns:
        A PIL ImageFont instance.
    """
    import platform
    import os
    
    system = platform.system()
    
    if system == "Linux":
        # Linux path for DejaVu fonts
        font_name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        font_path = f"/usr/share/fonts/truetype/dejavu/{font_name}"
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)
    elif system == "Darwin":  # macOS
        # macOS system fonts
        if bold:
            # Try Helvetica Bold or Arial Bold
            for font_name in ["Helvetica-Bold", "Arial Bold", "Arial-BoldMT"]:
                try:
                    return ImageFont.truetype(font_name, size)
                except:
                    continue
        else:
            # Try Helvetica or Arial
            for font_name in ["Helvetica", "Arial", "ArialMT"]:
                try:
                    return ImageFont.truetype(font_name, size)
                except:
                    continue
    
    # Fallback to default PIL font if nothing works
    try:
        return ImageFont.load_default()
    except:
        # Last resort: try to use any available TrueType font
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)


def _crop_to_4x5(
    img: Image.Image,
    rel_box: Optional[tuple[float, float, float, float]] = None,
    anchor: str = "center"
) -> Image.Image:
    """
    Crop an image to exact 4:5 ratio within a given ROI.
    
    Args:
        img: PIL Image to crop
        rel_box: Optional (x, y, w, h) relative coordinates (0..1)
        anchor: "center", "topleft", or "top" for positioning within ROI
    
    Returns:
        Cropped PIL Image in 4:5 ratio
    """
    RatioW, RatioH = 4, 5
    W, H = img.size
    
    # Define ROI
    if rel_box is not None:
        x = int(round(rel_box[0] * W))
        y = int(round(rel_box[1] * H))
        w = int(round(rel_box[2] * W))
        h = int(round(rel_box[3] * H))
        roi = (x, y, w, h)
    else:
        roi = (0, 0, W, H)
    
    x0, y0, rw, rh = roi
    x0 = max(0, min(x0, W-1))
    y0 = max(0, min(y0, H-1))
    rw = max(1, min(rw, W - x0))
    rh = max(1, min(rh, H - y0))
    
    # Compute 4:5 box dimensions
    target_w_from_h = (RatioW / RatioH) * rh
    if target_w_from_h <= rw:
        tw = int(round(target_w_from_h))
        th = int(round((RatioH / RatioW) * tw))
    else:
        tw = rw
        th = int(round((RatioH / RatioW) * tw))
        if th > rh:
            tw = int(round((RatioW / RatioH) * rh))
            th = int(round((RatioH / RatioW) * tw))
    
    # Position inside ROI
    if anchor == "topleft":
        cx, cy = x0, y0
    elif anchor == "top":
        cx = x0 + (rw - tw) // 2
        cy = y0
    else:  # center
        cx = x0 + (rw - tw) // 2
        cy = y0 + (rh - th) // 2
    
    # Crop and resize to 1080x1350
    crop = img.crop((cx, cy, cx + tw, cy + th))
    return crop.resize((1080, 1350), Image.Resampling.LANCZOS)


def _create_composite_image(
    base_image: Image.Image,
    headline: str,
    highlight: str,
    *,
    logo_image: Optional[Image.Image] = None,
    watermark_text: str = "diarioeldia.cl",
    highlight_color: tuple[int, int, int] = (0, 64, 145),
    text_color: tuple[int, int, int] = (0, 0, 0),
    box_color: tuple[int, int, int, int] = (255, 255, 255, 230),
    logo_scale: float = 0.10,
    instagram_format: bool = False,
    recorte: Optional[str] = None,
) -> Image.Image:
    """Compose a new image by drawing text and a logo over a base photograph.

    This helper encapsulates the layout logic used to build the final
    composite. It draws a watermark along the left edge, splits the
    headline into a highlighted segment and the remainder, wraps the
    remainder into lines, and draws irregularly sized boxes behind each
    line of text. A logo is also placed in the top-right corner.

    Args:
        base_image: The background photograph. It should be in RGB or RGBA mode.
        headline: The full headline to display on the image.
        highlight: The portion of the headline to emphasize (rendered in
            `highlight_color`). Only the first occurrence of this string
            will be removed from the remainder. If it is not found,
            `highlight` will be used as the highlighted line and the
            remainder will be the original headline.
        logo_image: A PIL image of the logo. If None, this function
            attempts to load ``El_Dia.png`` from the current directory.
        watermark_text: A short string to repeat vertically along the
            left-hand margin.
        highlight_color: RGB tuple for the highlighted line.
        text_color: RGB tuple for the non-highlight lines.
        box_color: RGBA tuple for the text box backgrounds. The fourth
            value controls transparency (0=transparent, 255=opaque).
        logo_scale: Fraction of the base image width to use as the logo
            width. Height is scaled to preserve aspect ratio.

    Returns:
        A new PIL Image containing the composed graphic.
    """
    # Ensure we are working on a copy in RGBA mode
    img = base_image.convert("RGBA").copy()
    
    # Resize para formato Instagram 4:5 (1080x1350) si es necesario
    if instagram_format:
        # Parse recorte parameter si existe (formato: "x,y,w,h" en valores 0..1)
        rel_box = None
        if recorte:
            try:
                parts = [float(v.strip()) for v in recorte.split(",")]
                if len(parts) == 4:
                    rel_box = tuple(parts)
            except (ValueError, AttributeError):
                # Si hay error en el formato, usar recorte centrado por defecto
                pass
        
        # Usar la función de recorte 4:5 avanzada
        img = _crop_to_4x5(img, rel_box=rel_box, anchor="center")
    
    width, height = img.size

    # Determine sizes for fonts relative to image height
    # Para Instagram usamos fuentes más pequeñas para mejor distribución del texto
    if instagram_format:
        main_font_size = max(12, int(height * 0.038))  # 37% más pequeño para Instagram
        side_font_size = max(8, int(height * 0.022))
    else:
        main_font_size = max(12, int(height * 0.06))  # tamaño normal para horizontal
        side_font_size = max(8, int(height * 0.03))

    # Load fonts
    font_bold = _load_font(main_font_size, bold=True)
    font_reg = _load_font(main_font_size, bold=False)
    font_side = _load_font(side_font_size, bold=False)

    # Prepare watermark along the left side
    # Para Instagram usamos barra lateral más delgada para más espacio de texto
    if instagram_format:
        bar_width = int(width * 0.05)  # Barra más delgada en Instagram
    else:
        bar_width = int(width * 0.07)  # Barra normal en horizontal
    # Create a temporary image for rendering horizontal watermark text
    temp = Image.new('RGBA', (height, bar_width), (0, 0, 0, 0))
    draw_temp = ImageDraw.Draw(temp)
    # Build a repeated string to fill the width when rotated
    phrase = watermark_text + '   '
    phrase_width = draw_temp.textlength(phrase, font=font_side)
    repeats = int((height / phrase_width)) + 3
    full_text = phrase * repeats
    y_offset = (bar_width - font_side.getbbox('Ay')[3]) // 2
    draw_temp.text((0, y_offset), full_text, font=font_side, fill=(255, 255, 255, 150))
    # Rotate to create vertical text and paste on base image
    vertical_img = temp.rotate(90, expand=True)
    img.paste(vertical_img, (0, 0), vertical_img)

    # Load or resize the logo
    if logo_image is None:
        try:
            # Attempt to load a default logo from the current directory
            logo_image = Image.open('El_Dia.png').convert('RGBA')
        except Exception:
            logo_image = None
    if logo_image is not None:
        logo_w = int(width * logo_scale)
        # Maintain aspect ratio
        logo_h = int(logo_w * logo_image.height / logo_image.width)
        logo_resized = logo_image.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
        # Paste the logo in the top right corner with a small margin
        img.paste(logo_resized, (width - logo_w - 10, 10), logo_resized)

    # Compute available width for text (excluding left bar and margins)
    # Para Instagram damos más espacio horizontal al texto
    if instagram_format:
        available_width = width - bar_width - 10  # Menos margen en Instagram
    else:
        available_width = width - bar_width - 20  # Margen normal en horizontal
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
    # Para Instagram usamos más ancho disponible (90% vs 85%)
    wrap_factor = 0.90 if instagram_format else 0.85
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
        
        # Create the box
        box_img = Image.new('RGBA', (int(box_w), int(box_h)), box_color)
        box_draw = ImageDraw.Draw(box_img)
        
        # Draw text character by character with appropriate colors and fonts
        text_x = padding_x
        
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
        text_y_offset = (box_h - actual_text_height) // 2
        
        for char_idx, char in enumerate(line_text):
            # Check if this character is highlighted
            is_highlighted = char_idx < len(line_highlights) and line_highlights[char_idx]
            color = highlight_color if is_highlighted else text_color
            font = font_bold if is_highlighted else font_reg
            
            # Adjust Y position for bold text to align with regular text + vertical centering
            y_position = text_y_offset + (baseline_offset if is_highlighted else 0)
            
            # Draw the character
            box_draw.text((text_x, y_position), char, font=font, fill=color)
            
            # Move x position (use the correct font for width calculation)
            char_width = draw_dummy.textlength(char, font=font)
            text_x += char_width
        
        # Paste onto the base image
        img.paste(box_img, (int(x), int(y)), box_img)
        
        # Move to next line
        current_y += box_h + line_spacing

    return img


@app.post("/generate-image", responses={
    200: {
        "description": "The generated image URL and metadata."
    },
    400: {"description": "Bad request"}
})
async def generate_image(
    headline: str = Form(..., description="Full headline to display."),
    highlight: str = Form(..., description="Substring of the headline to highlight."),
    image: UploadFile = File(..., description="Base photograph (PNG/JPEG)."),
    logo: Optional[UploadFile] = File(None, description="Optional logo file to override the default."),
    recorte: Optional[str] = Form(None, description="ROI for Instagram crop as 'x,y,w,h' (0..1), e.g., '0.14,0,0.72,1'")
):
    """Generate a composite image from user-supplied headline, highlight and photograph.

    This endpoint accepts multipart/form-data containing the headline,
    highlight, base image, and optionally a custom logo. It saves the
    generated image to a public directory and returns the public URL.

    Returns:
        JSON response containing the public URL of the generated image.
    """
    # Validate input lengths
    if not headline:
        raise HTTPException(status_code=400, detail="headline is required")
    if not highlight:
        raise HTTPException(status_code=400, detail="highlight is required")
    # Read the uploaded base image
    try:
        image_data = await image.read()
        base_img = Image.open(io.BytesIO(image_data)).convert('RGBA')
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read base image: {exc}")
    # Read the optional logo if provided
    logo_img: Optional[Image.Image] = None
    if logo is not None:
        try:
            logo_data = await logo.read()
            logo_img = Image.open(io.BytesIO(logo_data)).convert('RGBA')
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Could not read logo image: {exc}")
    
    # Generate the composite image (horizontal version)
    result_img = _create_composite_image(
        base_img,
        headline=headline,
        highlight=highlight,
        logo_image=logo_img,
        instagram_format=False,
        recorte=None,
    )
    
    # Generate the Instagram vertical version (4:5)
    result_img_instagram = _create_composite_image(
        base_img,
        headline=headline,
        highlight=highlight,
        logo_image=logo_img,
        instagram_format=True,
        recorte=recorte,
    )
    
    # Save both images and get public URLs
    image_url_horizontal = _save_image_and_get_url(result_img)
    image_url_instagram = _save_image_and_get_url(result_img_instagram)
    
    # Return JSON response with both URLs
    return {
        "success": True,
        "images": {
            "horizontal": {
                "url": image_url_horizontal,
                "format": "original",
                "description": "Imagen horizontal para web/Facebook"
            },
            "instagram": {
                "url": image_url_instagram,
                "format": "4:5",
                "dimensions": "1080x1350",
                "description": "Imagen vertical optimizada para Instagram"
            }
        },
        "headline": headline,
        "highlight": highlight,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/generate-image-from-url", responses={
    200: {
        "description": "The generated image URL and metadata."
    },
    400: {"description": "Bad request"}
})
async def generate_image_from_url(
    headline: str = Form(..., description="Full headline to display."),
    highlight: str = Form(..., description="Substring of the headline to highlight."),
    image_url: str = Form(..., description="URL of the base photograph."),
    logo_url: Optional[str] = Form(None, description="Optional URL of a custom logo file."),
    recorte: Optional[str] = Form(None, description="ROI for Instagram crop as 'x,y,w,h' (0..1), e.g., '0.14,0,0.72,1'")
):
    """Generate a composite image from user-supplied headline, highlight and image URL.

    This endpoint accepts a headline, highlight, image URL, and optionally a logo URL.
    It downloads the images from the URLs, saves the generated image to a public 
    directory and returns the public URL.

    Returns:
        JSON response containing the public URL of the generated image.
    """
    # Validate input lengths
    if not headline:
        raise HTTPException(status_code=400, detail="headline is required")
    if not highlight:
        raise HTTPException(status_code=400, detail="highlight is required")
    
    # Download the base image from URL
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        base_img = Image.open(io.BytesIO(response.content)).convert('RGBA')
    except requests.RequestException as exc:
        raise HTTPException(status_code=400, detail=f"Could not download image from URL: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not process downloaded image: {exc}")
    
    # Download the optional logo from URL
    logo_img: Optional[Image.Image] = None
    if logo_url is not None:
        try:
            logo_response = requests.get(logo_url, timeout=30)
            logo_response.raise_for_status()
            logo_img = Image.open(io.BytesIO(logo_response.content)).convert('RGBA')
        except requests.RequestException as exc:
            raise HTTPException(status_code=400, detail=f"Could not download logo from URL: {exc}")
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Could not process downloaded logo: {exc}")
    
    # Generate the composite image (horizontal version)
    result_img = _create_composite_image(
        base_img,
        headline=headline,
        highlight=highlight,
        logo_image=logo_img,
        instagram_format=False,
        recorte=None,
    )
    
    # Generate the Instagram vertical version (4:5)
    result_img_instagram = _create_composite_image(
        base_img,
        headline=headline,
        highlight=highlight,
        logo_image=logo_img,
        instagram_format=True,
        recorte=recorte,
    )
    
    # Save both images and get public URLs
    image_url_horizontal = _save_image_and_get_url(result_img)
    image_url_instagram = _save_image_and_get_url(result_img_instagram)
    
    # Return JSON response with both URLs
    return {
        "success": True,
        "images": {
            "horizontal": {
                "url": image_url_horizontal,
                "format": "original",
                "description": "Imagen horizontal para web/Facebook"
            },
            "instagram": {
                "url": image_url_instagram,
                "format": "4:5",
                "dimensions": "1080x1350",
                "description": "Imagen vertical optimizada para Instagram"
            }
        },
        "headline": headline,
        "highlight": highlight,
        "timestamp": datetime.now().isoformat()
    }


def _save_video_and_get_url(video_path: str) -> str:
    """Move video to public directory and return public URL."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"video_{timestamp}_{unique_id}.mp4"
    
    final_path = os.path.join(PUBLIC_VIDEOS_DIR, filename)
    
    # Move temp video to public directory
    import shutil
    shutil.move(video_path, final_path)
    
    return f"{BASE_URL}/public/videos/{filename}"


@app.post("/generate-video-from-url", responses={
    200: {
        "description": "The generated video URL and metadata."
    },
    400: {"description": "Bad request"}
})
async def generate_video_from_url(
    headline: str = Form(..., description="Full headline to display."),
    highlight: str = Form(..., description="Substring of the headline to highlight."),
    image_url: str = Form(..., description="URL of the base photograph."),
    duration: float = Form(5.0, description="Video duration in seconds (default: 5.0)"),
    direction: str = Form("left-to-right", description="Pan direction: left-to-right, right-to-left, top-to-bottom, bottom-to-top, zoom-in, zoom-out, diagonal-tl-br, diagonal-tr-bl"),
    fps: int = Form(30, description="Frames per second (default: 30)"),
    audio: Optional[UploadFile] = File(None, description="Optional audio file (mp3, wav, etc.)"),
    keep_aspect: bool = Form(True, description="Keep original image aspect ratio (default: True)")
):
    """Generate a cinematic pan & scan video from image URL.
    
    This endpoint creates a 9:16 (1080x1920) video with:
    - Cinematic pan & scan effect on the image
    - Static text overlay with headline and highlight
    - Same styling as generated images
    - Various pan directions and zoom effects
    
    Returns:
        JSON response containing the public URL of the generated video.
    """
    # Validate inputs
    if not headline:
        raise HTTPException(status_code=400, detail="headline is required")
    if not highlight:
        raise HTTPException(status_code=400, detail="highlight is required")
    
    if duration < 1 or duration > 30:
        raise HTTPException(status_code=400, detail="duration must be between 1 and 30 seconds")
    
    valid_directions = [
        "left-to-right", "right-to-left", 
        "top-to-bottom", "bottom-to-top",
        "zoom-in", "zoom-out",
        "diagonal-tl-br", "diagonal-tr-bl"
    ]
    if direction not in valid_directions:
        raise HTTPException(status_code=400, detail=f"direction must be one of: {', '.join(valid_directions)}")
    
    # Download image
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        base_img = Image.open(io.BytesIO(response.content)).convert('RGBA')
    except requests.RequestException as exc:
        raise HTTPException(status_code=400, detail=f"Could not download image from URL: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not process downloaded image: {exc}")
    
    # Process audio if provided
    audio_path = None
    actual_duration = duration
    if audio is not None:
        try:
            audio_data = await audio.read()
            audio_path = f"/tmp/audio_{uuid.uuid4()}{os.path.splitext(audio.filename)[1]}"
            with open(audio_path, 'wb') as f:
                f.write(audio_data)
            
            # Obtener duración del audio para ajustar el video
            from video_generator import get_audio_duration
            audio_duration = get_audio_duration(audio_path)
            if audio_duration:
                actual_duration = audio_duration
                
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Could not process audio file: {exc}")
    
    # Generate video
    try:
        # Save to temp file first
        temp_path = f"/tmp/video_{uuid.uuid4()}.mp4"
        
        make_pan_scan_video(
            output_path=temp_path,
            image_input=base_img,
            headline=headline,
            highlight=highlight,
            duration=actual_duration,
            out_w=1080 if not keep_aspect else None,
            out_h=1920 if not keep_aspect else None,
            fps=fps,
            direction=direction,
            ease_in_out=True,
            audio_path=audio_path,
            keep_aspect=keep_aspect
        )
        
        # Clean up temp audio file if exists
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
        
        # Get video dimensions before moving the file
        import subprocess
        try:
            cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'csv=p=0',
                temp_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                w, h = result.stdout.strip().split(',')
                video_dimensions = f"{w}x{h}"
                aspect = f"{w}:{h}" if keep_aspect else "9:16"
            else:
                video_dimensions = "unknown"
                aspect = "unknown"
        except:
            video_dimensions = "unknown"
            aspect = "unknown"
        
        # Move to public directory and get URL
        video_url = _save_video_and_get_url(temp_path)
        
        return {
            "success": True,
            "video_url": video_url,
            "headline": headline,
            "highlight": highlight,
            "duration": actual_duration,
            "direction": direction,
            "fps": fps,
            "format": aspect,
            "dimensions": video_dimensions,
            "keep_aspect": keep_aspect,
            "has_audio": audio_path is not None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Video generation failed: {exc}")


@app.post("/generate-static-video-from-url", responses={
    200: {"description": "Video generado exitosamente con portada y audio"},
    500: {"description": "Error en la generación del video"}
})
async def generate_static_video_from_url(
    image_url: str = Form(..., description="URL de la portada del diario"),
    audio: UploadFile = File(..., description="Archivo de audio con el resumen noticioso (mp3, wav, etc.)"),
    fps: int = Form(30, description="Frames por segundo (default: 30)")
):
    """
    Genera un video estático mostrando únicamente la portada del diario con audio.
    
    Sin texto, sin efectos de movimiento, solo la imagen estática con el audio del resumen noticioso.
    Ideal para resúmenes diarios de noticias.
    
    - **image_url**: URL de la portada del diario
    - **audio**: Archivo de audio con el resumen (el video durará lo mismo que el audio)
    - **fps**: Frames por segundo del video (default: 30)
    
    Returns:
        JSON con la URL del video generado, duración, dimensiones y metadata
    """
    import tempfile
    from datetime import datetime
    
    try:
        # Download image from URL
        response = requests.get(image_url)
        response.raise_for_status()
        base_img = Image.open(BytesIO(response.content))
        
        # Save audio temporarily
        audio_path = None
        if audio:
            audio_suffix = os.path.splitext(audio.filename)[1] if audio.filename else ".wav"
            with tempfile.NamedTemporaryFile(delete=False, suffix=audio_suffix) as tmp_audio:
                tmp_audio.write(await audio.read())
                audio_path = tmp_audio.name
        
        # Get audio duration
        from video_generator import get_audio_duration
        audio_duration = get_audio_duration(audio_path)
        if not audio_duration:
            raise HTTPException(status_code=400, detail="No se pudo obtener la duración del audio")
        
        print(f"📻 Generando video estático con portada y audio de {audio_duration:.2f}s")
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        temp_filename = f"video_{timestamp}_{unique_id}.mp4"
        temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
        
        # Generate static video with audio
        make_static_video_with_audio(
            output_path=temp_path,
            image_input=base_img,
            audio_path=audio_path,
            fps=fps
        )
        
        # Get video dimensions using ffprobe
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                 '-show_entries', 'stream=width,height',
                 '-of', 'csv=s=x:p=0', temp_path],
                capture_output=True,
                text=True
            )
            video_dimensions = result.stdout.strip() if result.returncode == 0 else "unknown"
        except:
            video_dimensions = "unknown"
        
        # Move to public directory and get URL
        video_url = _save_video_and_get_url(temp_path)
        
        # Clean up audio file
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
        
        return {
            "success": True,
            "video_url": video_url,
            "duration": audio_duration,
            "fps": fps,
            "dimensions": video_dimensions,
            "format": "static",
            "has_audio": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as exc:
        # Clean up audio file on error
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
        raise HTTPException(status_code=500, detail=f"Static video generation failed: {exc}")


if __name__ == "__main__":  # pragma: no cover
    import uvicorn
    # Run the app on localhost for manual testing
    uvicorn.run(app, host="0.0.0.0", port=8000)