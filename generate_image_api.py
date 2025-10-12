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

app = FastAPI(title=APP_NAME, description=APP_DESCRIPTION)

# Crear directorio de imágenes públicas si no existe
os.makedirs(PUBLIC_IMAGES_DIR, exist_ok=True)


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
    width, height = img.size

    # Determine sizes for fonts relative to image height
    main_font_size = max(12, int(height * 0.06))  # ensure minimum size
    side_font_size = max(8, int(height * 0.03))

    # Load fonts
    font_bold = _load_font(main_font_size, bold=True)
    font_reg = _load_font(main_font_size, bold=False)
    font_side = _load_font(side_font_size, bold=False)

    # Prepare watermark along the left side
    bar_width = int(width * 0.07)
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
    available_width = width - bar_width - 20
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
    wrapped_lines = wrap_text_with_highlights(headline, highlight_mask, font_reg, available_width * 0.85)
    
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
        
        for char_idx, char in enumerate(line_text):
            # Check if this character is highlighted
            is_highlighted = char_idx < len(line_highlights) and line_highlights[char_idx]
            color = highlight_color if is_highlighted else text_color
            font = font_bold if is_highlighted else font_reg
            
            # Adjust Y position for bold text to align with regular text
            y_position = padding_y + (baseline_offset if is_highlighted else 0)
            
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
    logo: Optional[UploadFile] = File(None, description="Optional logo file to override the default.")
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
    # Generate the composite image
    result_img = _create_composite_image(
        base_img,
        headline=headline,
        highlight=highlight,
        logo_image=logo_img,
    )
    
    # Save image and get public URL
    image_url = _save_image_and_get_url(result_img)
    
    # Return JSON response with URL
    return {
        "success": True,
        "image_url": image_url,
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
    logo_url: Optional[str] = Form(None, description="Optional URL of a custom logo file.")
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
    
    # Generate the composite image
    result_img = _create_composite_image(
        base_img,
        headline=headline,
        highlight=highlight,
        logo_image=logo_img,
    )
    
    # Save image and get public URL
    image_url = _save_image_and_get_url(result_img)
    
    # Return JSON response with URL
    return {
        "success": True,
        "image_url": image_url,
        "headline": headline,
        "highlight": highlight,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":  # pragma: no cover
    import uvicorn
    # Run the app on localhost for manual testing
    uvicorn.run(app, host="0.0.0.0", port=8000)